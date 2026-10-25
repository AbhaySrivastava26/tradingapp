# Personal Trading Journal
Local-only single-user starter; no login/logout and no broker connection.

## Run on Windows
1. Extract the ZIP.
2. Install Python 3.11+ from https://www.python.org/downloads/ and select **Add Python to PATH**.
3. Double-click `run_windows.bat`. First launch installs dependencies (internet required).
4. Open http://127.0.0.1:8000.
5. Next time, use `start_existing_install.bat`.

## Included
- Dashboard and trade metrics
- Manual trade entry/edit/delete
- Date-wise calendar and search
- Reasons, strategy, emotions, rule adherence and notes
- Before/after screenshot uploads
- Analytics by strategy
- Saved rule-based daily reviews (not AI)
- Basic risk calculator
- CSV export and database backup

## Storage/privacy
Trades and reviews: `data/trading_journal.db`. Images: `uploads/`. App binds to localhost only. No external AI, news or broker API is configured. Anyone with access to your computer/files can view the data. Back up both `data` and `uploads`.

## Important
P&L is a generic approximation: (exit-entry)*quantity for Long and the reverse for Short, minus costs. Instrument-specific contract multipliers for forex, gold, CFDs, futures and leveraged instruments may be needed. Verify calculations against your broker before relying on them. The app cannot verify trades or know live balance. AI image analysis, live news, full candle replay, and live broker sync are not enabled in this starter.
