# market-lab

Research lab for short/medium-term trading edges across S&P, Nasdaq, oil, gold, BTC,
sectors, and individual stocks. Data collected daily by GitHub Actions into `data/`.
Owner: Guy. Analysis happens in Claude Code sessions and claude.ai chats (repo is
public so claude.ai can fetch raw CSVs directly).

## Project layout
- `collect.py` — daily OHLCV collector (yfinance, stooq fallback). Universe defined at top.
- `data/*.csv` — one file per ticker: date, open, high, low, close, volume.
- `research/` — one markdown file per hypothesis: thesis, test, result, verdict. Never delete failed ones; the graveyard prevents re-testing dead ideas.
- `.github/workflows/collect.yml` — daily run + commit.

## Research rules (non-negotiable — learned the hard way)
1. **Never assume values — always compute from actual data before concluding.**
2. **No lookahead.** Signals use only data available at decision time; trade at next close at the earliest.
3. **Costs always.** Minimum 0.05%/side equities, 0.1% BTC, plus slippage on illiquid names.
4. **Out-of-sample or it didn't happen.** Split train/test by time; an edge that only exists in one regime is a regime bet, not an edge.
5. **Sample size.** <30 trades = anecdote. Report n with every stat.
6. **Benchmark honestly.** Compare against buy-and-hold of the same asset AND T-bills. Win rate is meaningless without payoff ratio; report expectancy, profit factor, max drawdown, max consecutive losses.
7. **Multiple-testing discipline.** Testing 50 indicators and reporting the best one is data mining. Log every test run, including failures, in `research/`.
8. **Leverage rules.** Any leveraged result must show: volatility drag modeled at the rebalance frequency, liquidation/halt modeling, and survival through the worst historical window in the data.
9. **Known graveyard (do not re-test without new angle):** BTC daily MACD(12,26,9) crossovers — no edge vs baseline (n=359). Naive constant 3x leverage — wipes out. Shorting below 200MA — edge vanished post-1990. RSI-2 dip-buy standalone — positive but tiny (PF≈1.1-1.3), doesn't beat T-bills on capital efficiency.
10. **Validated so far:** time-series momentum / 200d-MA trend filter (multi-asset, 150yr support); trend-gated leverage; next-day bounce after -1% down-day in SPY (+0.14%/trade, n=242, bull-sample caveat).

## Trading rules (when anything goes live)
- Deterministic Python only. No LLM in the execution loop.
- Kill switch flag checked before every order. Daily loss limit. Position size caps.
- Paper trade minimum 30 days before real capital. Real capital starts small.
- API keys in environment/secrets only, trade-only permissions, never committed.
- Before going live, re-verify: broker ToS allows automation, rate limits respected, risk module intact.

## Conventions
- Python: pandas/numpy, matplotlib for charts. Charts saved to research/figs/.
- Every research file ends with a one-line VERDICT: EDGE / NO EDGE / NEEDS DATA.
- Keep functions reusable; shared helpers go in `lib.py` (create when needed).
