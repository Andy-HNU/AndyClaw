# V2 Signal Spec

## Purpose
This file defines a first implementable set of warning and research signals for
V2. The goal is not to predict markets perfectly. The goal is to:
- make signal generation explicit
- keep formulas auditable
- separate observation from recommendation
- keep room for later refinement

All thresholds in this file are provisional and should be treated as a baseline
for testing, not as permanent truth.

## Data Requirements

### Core Market Data
- daily `open`
- daily `high`
- daily `low`
- daily `close`
- daily `volume`

### Position Data
- asset id
- asset type
- category
- amount
- shares
- average cost
- transaction history
- dividends / distributions if available

### Optional Research Data
- P/E
- PEG
- P/B
- EV/EBITDA
- earnings growth
- fair value estimate
- fund manager
- benchmark
- fund category

## Reporting Convention
Each signal should output:
- `signal_name`
- `level`: `observe` / `watch` / `warning`
- `summary`
- `evidence`
- `window`
- `confidence`
- `impact_scope`
- `suggested_follow_up`

## Position Tracking Formulas

### 1. Amount Change
Formula:
```text
amount_change = current_amount - previous_amount
amount_change_pct = (current_amount - previous_amount) / previous_amount * 100
```

Use:
- track how much market value changed over the report window

### 2. Share Change
Formula:
```text
share_change = current_shares - previous_shares
share_change_pct = (current_shares - previous_shares) / previous_shares * 100
```

Use:
- distinguish subscriptions/redemptions from market-price-only moves

### 3. Price-Driven Change vs Flow-Driven Change
Formula:
```text
price_effect = previous_shares * (current_nav_or_price - previous_nav_or_price)
flow_effect = amount_change - price_effect
```

If transaction data exists, refine to:
```text
flow_effect = net_subscription_amount - net_redemption_amount + dividend_reinvest_amount
```

Use:
- show whether changes came from market movement or from user action

### 4. Weight By Asset and By Category
Formula:
```text
asset_weight_pct = asset_amount / portfolio_total_amount * 100
category_weight_pct = category_amount / portfolio_total_amount * 100
```

Use:
- track both permanent-portfolio sleeves and sub-asset concentration

## Trend and Distribution Signals

### 1. Simple Moving Average
Formula:
```text
SMA_n = sum(close_t over n days) / n
```

Suggested windows:
- `SMA20`
- `SMA60`
- `SMA120`

Trend interpretation:
- strong uptrend:
  - `close > SMA20 > SMA60 > SMA120`
- weakening uptrend:
  - `close > SMA60` but `SMA20 < SMA60`
- weak trend / possible breakdown:
  - `close < SMA60`

### 2. Drawdown
Formula:
```text
rolling_peak_n = max(close over n days)
drawdown_pct = (close - rolling_peak_n) / rolling_peak_n * 100
```

Suggested windows:
- `20d`
- `60d`
- `120d`

Suggested thresholds:
- `observe`: drawdown <= `-5%`
- `watch`: drawdown <= `-10%`
- `warning`: drawdown <= `-15%`

### 3. Accumulation/Distribution Line
Formula:
```text
money_flow_multiplier =
((close - low) - (high - close)) / (high - low)

money_flow_volume = money_flow_multiplier * volume

AD_t = AD_(t-1) + money_flow_volume
```

If `high == low`, set multiplier to `0`.

Use:
- detect whether closes happen near the upper or lower end of each day's range
- detect divergence between price and accumulation/distribution flow

### 4. On-Balance Volume
Formula:
```text
if close_t > close_(t-1): OBV_t = OBV_(t-1) + volume_t
if close_t < close_(t-1): OBV_t = OBV_(t-1) - volume_t
if close_t == close_(t-1): OBV_t = OBV_(t-1)
```

Use:
- estimate whether volume confirms or contradicts price trend

### 5. Chaikin Money Flow
Formula:
```text
CMF_n = sum(money_flow_volume over n days) / sum(volume over n days)
```

Suggested window:
- `20d`

Interpretation:
- `CMF > 0`: buying pressure stronger
- `CMF < 0`: selling pressure stronger

### 6. Volume Spike
Formula:
```text
volume_ratio_20 = current_volume / average(volume over last 20 days)
```

Suggested thresholds:
- `observe`: `>= 1.5`
- `watch`: `>= 2.0`
- `warning`: `>= 3.0`

### 7. Suspected Distribution
This should not be a single formula. Use a rule bundle.

Suggested rule:
emit `suspected_distribution` when at least 3 of the following are true:
- price is within `3%` of a `60d` high
- `AD` fails to make a new `60d` high
- `OBV` fails to make a new `60d` high
- `CMF_20 < 0`
- one or more breakout attempts fail within `10d`
- `volume_ratio_20 >= 1.5` on down days

Suggested levels:
- `observe`: 3 conditions
- `watch`: 4 conditions
- `warning`: 5 or more conditions

Suggested summary:
- `price remains elevated but volume-flow confirmation is weakening`

### 8. Possible Shakeout
Suggested rule:
emit `possible_shakeout` when all of the following are true:
- `close` is still above `SMA60`
- drawdown from `20d` peak is between `-5%` and `-12%`
- `volume_ratio_20 >= 1.5`
- within `5` trading days price reclaims a prior short-term support or closes
  back above `SMA20`

Suggested summary:
- `short-term flush occurred but medium-term trend remains intact`

### 9. Failed Trend / Breakdown Warning
Suggested rule:
emit `trend_break_warning` when:
- `close < SMA60`
- `SMA20 < SMA60`
- `CMF_20 < 0`
- `drawdown_60 <= -10%`

## Valuation Signals

### 1. P/E Premium vs Peer Group
Formula:
```text
pe_premium_pct = (asset_pe - peer_median_pe) / peer_median_pe * 100
```

Suggested thresholds:
- `observe`: `> 15%`
- `watch`: `> 30%`
- `warning`: `> 50%`

### 2. P/B Premium vs Peer Group
Formula:
```text
pb_premium_pct = (asset_pb - peer_median_pb) / peer_median_pb * 100
```

Suggested thresholds:
- same as P/E premium unless the sector needs a custom range

### 3. PEG Filter
Formula:
```text
PEG = PE / earnings_growth_rate
```

Use:
- avoid calling a fast-growing asset `overvalued` only because raw P/E is high

Suggested interpretation:
- `PEG < 1`: growth-adjusted valuation may be reasonable
- `1 <= PEG <= 2`: neutral
- `PEG > 2`: stretched, especially if peer premium is also high

### 4. EV/EBITDA Premium vs Peer Group
Formula:
```text
ev_ebitda_premium_pct =
(asset_ev_ebitda - peer_median_ev_ebitda) / peer_median_ev_ebitda * 100
```

Use:
- useful for operating businesses where debt structure matters more than P/E alone

### 5. Price / Fair Value
Formula:
```text
price_fair_value = market_price / fair_value_estimate
```

Suggested thresholds:
- `valuation_discount`:
  - `observe`: `< 0.9`
  - `watch`: `< 0.8`
  - `warning`: `< 0.7`
- `valuation_premium`:
  - `observe`: `> 1.1`
  - `watch`: `> 1.2`
  - `warning`: `> 1.3`

### 6. Historical Percentile of Valuation
Formula:
```text
valuation_percentile =
percentile_rank(current_metric within lookback_distribution)
```

Suggested lookback:
- `3y`
- `5y`

Interpretation:
- above `80th percentile`: stretched
- below `20th percentile`: discounted

### 7. Composite Overvaluation Warning
Emit `valuation_premium_warning` when one of the following is true:
- `price_fair_value > 1.2`
- two of these are true:
  - `pe_premium_pct > 30%`
  - `pb_premium_pct > 30%`
  - `ev_ebitda_premium_pct > 30%`
  - valuation percentile `> 80`
  - `PEG > 2`

Emit `valuation_discount_watch` when one of the following is true:
- `price_fair_value < 0.8`
- two of these are true:
  - `pe_premium_pct < -20%`
  - `pb_premium_pct < -20%`
  - `ev_ebitda_premium_pct < -20%`
  - valuation percentile `< 20`

Important constraint:
- do not call something `cheap` if earnings quality is collapsing

## Fund and Portfolio Quality Signals

### 1. Sharpe Ratio
Formula:
```text
Sharpe = (portfolio_return - risk_free_rate) / return_std_dev
```

Use the same periodicity for all inputs.

Suggested interpretation:
- `< 0`: poor risk-adjusted return
- `0 to 1`: weak to moderate
- `1 to 2`: solid
- `> 2`: unusually strong

This should be used comparatively:
- compare to benchmark
- compare to category median
- compare to own trailing history

### 2. Volatility
Formula:
```text
volatility_annualized = std_dev(periodic_returns) * sqrt(periods_per_year)
```

Suggested windows:
- `60d`
- `252d`

### 3. Maximum Drawdown
Formula:
```text
max_drawdown = min((value_t - rolling_peak_t) / rolling_peak_t)
```

Use:
- detect whether a fund's downside behavior is worsening

### 4. Beta
Formula:
```text
beta = cov(asset_returns, benchmark_returns) / var(benchmark_returns)
```

Use:
- identify whether a fund is becoming more aggressive than intended

### 5. Manager Style Drift
This is partly rule-based, not purely mathematical.

Suggested triggers:
- fund manager changed
- top holdings changed materially
- sector exposure changed by more than `10 percentage points`
- rolling beta changed by more than `0.2`
- active share proxy rose sharply if data exists

### 6. Risk-Adjusted Deterioration
Emit `risk_adjusted_return_deterioration` when at least 2 are true:
- Sharpe ratio below category median by `20%+`
- max drawdown worse than category median by `20%+`
- annualized volatility above category median by `20%+`
- beta rises above target band

## Macro / Regime Signal Baseline
This is not the final V2 regime model. It is a first workable baseline.

### 1. Inflation-Like Pressure
Possible score inputs:
- inflation-sensitive assets outperform
- long-duration assets weaken
- commodity / gold-related news frequency rises
- policy/news mention sticky prices or cost pressure

### 2. Deflation-Like Pressure
Possible score inputs:
- long-duration bonds strengthen
- cyclical assets weaken
- commodity weakness broadens
- policy/news mention weak demand or falling prices

### 3. Expansion-Like Pressure
Possible score inputs:
- cyclicals outperform defensives
- earnings revisions improve
- broad risk appetite strengthens
- news tone supports investment / production / hiring

### 4. Recession-Like Pressure
Possible score inputs:
- defensives outperform cyclicals
- credit or liquidity stress rises
- earnings revisions deteriorate
- news tone emphasizes slowdown, contraction, layoffs, weak demand

Suggested early implementation:
- build a `0-100` score for each regime family
- normalize to relative ranking
- report top 2 regimes with confidence
- do not directly auto-rewrite strategic targets yet

## Concentration Signals

### 1. Single Asset Concentration
Formula:
```text
single_asset_weight_pct = asset_amount / portfolio_total * 100
```

Suggested thresholds:
- `observe`: `> 10%`
- `watch`: `> 15%`
- `warning`: `> 20%`

### 2. Theme Concentration
Formula:
```text
theme_weight_pct = theme_total_amount / portfolio_total * 100
```

Suggested thresholds should be customized by theme importance.

### 3. Sleeve Drift Persistence
Formula:
```text
drift_persistence = number_of_consecutive_report_cycles_with_same_breach
```

Suggested thresholds:
- `observe`: `>= 2`
- `watch`: `>= 3`
- `warning`: `>= 4`

## Confidence Rules
Confidence should be derived from evidence count and data quality.

Suggested mapping:
- `low`
  - 1 weak signal
  - or incomplete data
- `medium`
  - 2-3 aligned signals
  - data quality acceptable
- `high`
  - multiple aligned signals across price, volume, valuation, and peer context

## Implementation Rules
- no signal should directly trigger a buy or sell
- every signal must preserve raw evidence fields
- regime signals may inform review, but not automatically rewrite long-term targets
- valuation warnings must include peer or fair-value context
- `洗盘 / 出货` should remain user-facing aliases only, never internal canonical ids

## Canonical Signal IDs
Recommended internal ids:
- `possible_shakeout`
- `suspected_distribution`
- `trend_break_warning`
- `valuation_premium_warning`
- `valuation_discount_watch`
- `risk_adjusted_return_deterioration`
- `manager_style_drift`
- `concentration_warning`
- `persistent_allocation_drift`
- `macro_regime_shift_watch`

## Reference Only
The following are useful references, not dependencies to import by default.

### Financial Interpretation References
- Fidelity: Accumulation/Distribution
  https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/accumulation-distribution
- Fidelity: On-Balance Volume
  https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/obv
- Fidelity: Chaikin Money Flow
  https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/cmf
- Schwab: P/E Ratio Basics
  https://www.schwab.com/learn/story/pe-ratio-basics
- Schwab: Five Key Financial Ratios for Stock Analysis
  https://www.schwab.com/learn/story/five-key-financial-ratios-stock-analysis
- Schwab: Stock Valuation with EV/EBITDA
  https://www.schwab.com/learn/story/stock-valuation-with-evebitda
- Morningstar: Fair Value Estimate
  https://www.morningstar.com/investing-terms/fair-value-estimate
- Morningstar: Portfolio Price/Fair Value
  https://www.morningstar.com/investing-terms/portfolio-price-fair-value
- Investor.gov: Mutual fund and bond risk references
  https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/how-read-2
  https://www.investor.gov/index.php/introduction-investing/investing-basics/glossary/bond-funds-and-income-funds

### Open-Source Logic References
- `bukosabino/ta`
  https://github.com/bukosabino/ta
- `ranaroussi/quantstats`
  https://github.com/ranaroussi/quantstats

### Supply-Chain Security References
- GitHub dependency review
  https://docs.github.com/en/enterprise-cloud@latest/code-security/concepts/supply-chain-security/about-dependency-review
- GitHub code scanning
  https://docs.github.com/en/code-security
- OpenSSF Scorecard
  https://github.com/ossf/scorecard
