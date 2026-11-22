"""Offline OHLCV bucket utilities adapted from GAON Trading P31's
domain/candle.py and domain/market_data.py.

These functions merge *observed trades*, not exchange-certified bars.
They cannot authorize or place any brokerage order.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True, slots=True)
class MinuteBar:
    timestamp: str
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int

def _validate(bar: MinuteBar) -> None:
    if len(bar.timestamp) != 14 or not bar.timestamp.isascii() or not bar.timestamp.isdigit():
        raise ValueError('timestamp must be YYYYMMDDHHMMSS')
    if any(not p.is_finite() for p in (bar.open_price, bar.high_price, bar.low_price, bar.close_price)):
        raise ValueError('non-finite OHLC value')
    if not (bar.low_price <= bar.open_price <= bar.high_price and
            bar.low_price <= bar.close_price <= bar.high_price):
        raise ValueError('invalid OHLC range')
    if bar.volume < 0:
        raise ValueError('negative volume')

def _merge(existing: MinuteBar, incoming: MinuteBar, *, open_price: Decimal|None=None,
           close_price: Decimal|None=None) -> MinuteBar:
    return MinuteBar(
        timestamp=existing.timestamp,
        open_price=existing.open_price if open_price is None else open_price,
        high_price=max(existing.high_price, incoming.high_price),
        low_price=min(existing.low_price, incoming.low_price),
        close_price=incoming.close_price if close_price is None else close_price,
        volume=existing.volume+incoming.volume,
    )

def merge_observed_minute_buckets(
    bars: tuple[MinuteBar, ...],
    observed: tuple[MinuteBar, ...],
    *, max_bars: int = 2600,
) -> tuple[MinuteBar, ...]:
    """Merge received trade fragments without interpolating missing minutes.

    Arrival order chooses the closing price for a repeated minute.
    This output is observational and should not be used as certified data.
    """
    if max_bars < 1:
        raise ValueError('max_bars must be positive')
    by_minute: dict[str, MinuteBar] = {}
    for bar in (*bars, *observed):
        _validate(bar)
        old=by_minute.get(bar.timestamp)
        by_minute[bar.timestamp]=_merge(old,bar) if old else bar
    return tuple(by_minute[k] for k in sorted(by_minute)[-max_bars:])

def merge_time_ordered_observed_minute_buckets(
    bars: tuple[MinuteBar, ...],
    observed: tuple[MinuteBar, ...],
    *, existing_bounds: dict[str, tuple[str,str]],
    observed_bounds: tuple[tuple[str,str,str],...],
    max_bars: int = 2600,
) -> tuple[tuple[MinuteBar,...], dict[str,tuple[str,str]]]:
    """Use broker-provided first/last timestamps when provenance exists.

    Same-second ties cannot be proven and remain arrival-ordered.
    Pre-existing bars without provenance retain their original open.
    """
    if max_bars < 1:
        raise ValueError('max_bars must be positive')
    by_minute: dict[str,MinuteBar]={}
    for bar in bars:
        _validate(bar)
        by_minute[bar.timestamp]=bar
    clocks=dict(existing_bounds)
    incoming={key:(first,last) for key,first,last in observed_bounds
              if len(key)==14 and len(first)==14 and len(last)==14
              and key.isascii() and first.isascii() and last.isascii()
              and key.isdigit() and first.isdigit() and last.isdigit()
              and first[:12]==key[:12] and last[:12]==key[:12] and first<=last}
    for bar in observed:
        _validate(bar)
        old=by_minute.get(bar.timestamp)
        new_clock=incoming.get(bar.timestamp)
        old_clock=clocks.get(bar.timestamp)
        if old is None:
            by_minute[bar.timestamp]=bar
            if new_clock: clocks[bar.timestamp]=new_clock
            continue
        first=old.open_price
        last=bar.close_price
        if old_clock is not None and new_clock is not None:
            if new_clock[0]<old_clock[0]: first=bar.open_price
            if new_clock[1]<old_clock[1]: last=old.close_price
            clocks[bar.timestamp]=(min(old_clock[0],new_clock[0]),max(old_clock[1],new_clock[1]))
        elif old_clock is None and new_clock is not None:
            clocks[bar.timestamp]=new_clock
        by_minute[bar.timestamp]=_merge(old,bar,open_price=first,close_price=last)
    recent=sorted(by_minute)[-max_bars:]
    return tuple(by_minute[k] for k in recent), {k:clocks[k] for k in recent if k in clocks}
