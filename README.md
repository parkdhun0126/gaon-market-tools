# GAON Market Tools

A small, independent, **offline and read-only** Python utility package adapted from the GAON Trading P31 research/development codebase. It is not the automated trading application.

This project provides reusable examples for consolidating observed trade-minute OHLCV fragments and for displaying **session-only** P/L estimates without confusing account equity with daily trading performance.

## Features

- Merge observed minute buckets without interpolation or fabricated exchange bars
- Respect original broker timestamps when available and document limits of same-second sequencing
- Display session P/L only when the trading date and starting capital are verified

**Not included:** broker integrations, brokerage credentials, trading strategies, live orders, account data, private history, or operational datasets.

## Install and test

Python 3.10+; no third-party runtime dependencies.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python tools/audit.py
```

## Usage

```python
from decimal import Decimal
from gaon_market_tools import MinuteBar, merge_observed_minute_buckets

bar = MinuteBar("20261120103000", Decimal("100"), Decimal("103"),
                Decimal("99"), Decimal("102"), 5)
observations = merge_observed_minute_buckets((), (bar,))
print(observations)
```

## Project maturity and safety

Early-stage open-source utilities, with no established public adoption or trading profitability claims. These observational outputs are not certified market data, accounting statements, investment advice, or authorization to send brokerage orders. Review and test before reuse.

Only the standalone publication export was scanned and tested. The private GAON Trading repository and its full Git history were **not** exhaustively security audited.

## Contributing

Issues, documentation fixes and pull requests are welcome. Never post secrets or personally identifiable financial information in issues.

License: MIT, copyright 2026 DONGHUN PARK.
