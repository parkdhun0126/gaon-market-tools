"""Display-only intraday P/L metrics adapted from P31's session metrics.

Not suitable as an accounting ledger or source of broker truth.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

MAX_MANAGED_SEED=Decimal('10000000')

@dataclass(frozen=True, slots=True)
class DailySessionDisplay:
    valid: bool
    seed: Decimal|None
    estimated_pl: Decimal|None
    rate_pct: Decimal|None
    rate_text: str
    pl_text: str
    capital_text: str

def _day(value: object) -> str|None:
    raw=''.join(c for c in str(value or '') if c.isdigit())
    if len(raw)!=8 or not raw.isascii(): return None
    try: datetime.strptime(raw,'%Y%m%d')
    except ValueError: return None
    return raw

def _decimal(value: object) -> Decimal|None:
    try:
        number=Decimal(str(value))
        return number if number.is_finite() else None
    except (TypeError,ValueError,InvalidOperation,OverflowError): return None

def build_daily_session_display(*,trading_date:str,budget:object)->DailySessionDisplay:
    """Never mistake account balance or a prior day for today's P/L."""
    unknown=DailySessionDisplay(False,None,None,None,
        'Session unavailable','Unverified session P/L','Unverified starting capital')
    if _day(trading_date) is None or _day(trading_date)!=_day(getattr(budget,'trading_date_kst',None)):
        return unknown
    seed=_decimal(getattr(budget,'starting_capital_krw',None))
    pl=_decimal(getattr(budget,'session_net_pl_krw',None))
    if seed is None or pl is None or not (Decimal('0')<seed<=MAX_MANAGED_SEED):
        return unknown
    rate=(pl/seed)*Decimal('100')
    return DailySessionDisplay(True,seed,pl,rate,
        '0.00%' if rate==0 else f'{rate:+.2f}%',
        f'{pl:+,.0f} KRW (estimated session P/L)',
        f'{seed:,.0f} KRW (session seed)')
