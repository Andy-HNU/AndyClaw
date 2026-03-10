# V2 Signal Research

## Purpose
This note translates early investment ideas into signals that are more defensible,
more testable, and safer to automate.

It is intentionally conservative:
- do not treat news or technical signals as direct trading instructions
- do not encode subjective market slang as if it were a precise model
- prefer explainable signals with evidence, confidence, and limits

## Why This Matters
Terms like `洗盘` and `出货` are common market slang, but they are not stable
financial definitions. If the system uses them directly, it will be easy to
overfit narrative and hard to validate correctness.

Recommended approach:
- keep user-facing language understandable
- translate slang into evidence-backed internal signals
- make the report show both the plain-language interpretation and the evidence

## Signal Translation

### 1. `洗盘`
This is usually used to describe a pullback or volatility burst that does not
necessarily break the longer-term uptrend, often interpreted as weak holders
being forced out before trend continuation.

This should not be a direct system label.

Recommended internal translation:
- high-volatility pullback
- uptrend intact but short-term pressure elevated
- suspected shakeout, low confidence

Candidate evidence:
- short-term drawdown expands while medium-term trend is still upward
- volume spikes during a pullback, but accumulation-type indicators do not
  collapse
- price breaks below a short-term support level but quickly reclaims it
- sector and peer assets do not confirm a broad structural breakdown

Recommended report wording:
- `possible shakeout / volatility flush`
- not `confirmed washout`

### 2. `出货`
This usually means large holders may be distributing into strength.

Recommended internal translation:
- suspected distribution
- negative price-volume divergence
- trend continuation risk rising

Candidate evidence:
- price makes higher highs while volume-based indicators fail to confirm
- repeated upper-shadow / failed breakout behavior
- Chaikin Money Flow weakens while price stays elevated
- On-Balance Volume or Accumulation/Distribution fails to confirm price highs

Recommended report wording:
- `suspected distribution`
- `distribution risk rising`

### 3. `高估`
This is more suitable for valuation models than chart slang.

Recommended internal translation:
- trading above fair value estimate
- relative valuation stretched vs peers/history

Candidate evidence:
- price/fair value ratio materially above `1`
- P/E, PEG, EV/EBITDA, P/B or other relevant multiples exceed peer range
- earnings expectations imply aggressive assumptions with limited margin of safety

Recommended report wording:
- `valuation appears stretched`
- `trading at a premium to fair value / peers`

### 4. `低估`
Recommended internal translation:
- trading below fair value estimate
- relative valuation discounted vs peers/history

Candidate evidence:
- price/fair value ratio materially below `1`
- valuation multiples below peer range without corresponding business collapse
- earnings / balance sheet quality remains adequate while market pricing is weak

Recommended report wording:
- `valuation appears discounted`
- `trading below fair value / peer range`

## External Research Summary

### Price and Volume Signals
Fidelity's indicator guides are useful for translating `吸筹 / 派发 / 量价背离`
into implementable signals:

- `Accumulation/Distribution` looks at where the close sits in the period's
  range and weights that by volume. Fidelity explicitly says to focus on the
  direction of the indicator, and highlights divergence between price and A/D
  as a sign that trend continuation may fail.
- `OBV` measures buying and selling pressure by adding volume on up closes and
  subtracting it on down closes. Fidelity again highlights divergence as a key
  warning sign.
- `CMF` is a volume-weighted measure of accumulation/distribution over a window.
  Fidelity notes that values above zero suggest strength and below zero suggest
  weakness, with divergence around highs/lows usable as buy/sell context.

Implication for this project:
- if we want to approximate `洗盘 / 出货`, use A/D, OBV, CMF, trend breaks,
  drawdown, and divergence rules
- do not claim certainty; keep these as evidence-backed warnings

Sources:
- Fidelity: Accumulation/Distribution
  https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/accumulation-distribution
- Fidelity: On-Balance Volume
  https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/obv
- Fidelity: Chaikin Money Flow
  https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/cmf

### Valuation Signals
For `高估 / 低估`, long-term portfolio decisions should rely more on valuation
logic than on chart narrative.

Useful references:
- Schwab explains that P/E is a starting point for comparing how much investors
  pay for earnings, but it should be compared across peers and not treated as
  a standalone truth.
- Schwab also highlights PEG, ROE, P/B, debt/equity, and EV/EBITDA as useful
  complementary ratios.
- Morningstar defines fair value as an intrinsic value estimate driven by a DCF
  framework and uses price/fair value to describe premium vs discount.
- Morningstar also provides portfolio or ETF-level price/fair value concepts,
  which are especially relevant if this project later evaluates ETFs or fund
  baskets rather than only single stocks.

Implication for this project:
- `高估 / 低估` should usually mean either:
  - above/below fair value, or
  - above/below relevant peer valuation range
- the system should avoid calling an asset `cheap` or `expensive` from P/E alone

Sources:
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

### Fund and Risk Metrics
For funds and portfolios, Sharpe ratio and related measures are useful, but they
should remain supporting metrics rather than final decision rules.

Useful references:
- Fidelity's mutual fund pages expose `Sharpe Ratio`, `Beta`, `R^2`, and
  `Standard Deviation` as standard risk/performance fields.
- Investor.gov's fund education materials remind investors to consider market,
  issuer, credit, interest-rate, inflation, and concentration risk depending on
  the underlying assets.

Implication for this project:
- fund reports can reasonably include:
  - Sharpe ratio
  - volatility / standard deviation
  - drawdown
  - beta
  - category comparison
- bond and bond-fund analysis should explicitly include:
  - interest-rate risk
  - inflation risk
  - credit risk

Sources:
- Fidelity fund research example
  https://fundresearch.fidelity.com/mutual-funds/performance-and-risk/316127109
- Investor.gov: How to Read a Mutual Fund Prospectus
  https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/how-read-2

## Recommended System Vocabulary
To keep reports understandable but auditable, use a vocabulary like this:

- `possible shakeout`
- `suspected distribution`
- `valuation premium`
- `valuation discount`
- `trend weakening`
- `trend strengthening`
- `crowding risk rising`
- `manager style drift`
- `risk-adjusted return deteriorating`

Avoid presenting these as deterministic facts unless the underlying rule is
both narrow and well-tested.

## Recommended V2 Signal Families

### A. Position and Flow Signals
- amount change
- share change
- subscription / redemption activity
- net asset value driven change
- realized / unrealized gain split

### B. Trend and Distribution Signals
- moving-average trend state
- drawdown depth
- breakout / failed breakout
- A/D divergence
- OBV divergence
- CMF sign and slope
- turnover / volume spike abnormality

### C. Valuation Signals
- P/E vs peer range
- PEG vs growth profile
- P/B vs asset-heavy peers
- EV/EBITDA where applicable
- price/fair value ratio
- historical percentile of valuation metrics

### D. Fund Quality Signals
- Sharpe ratio
- max drawdown
- volatility
- beta
- manager change
- style drift
- concentration change

### E. Macro / Regime Signals
- inflation-sensitive asset leadership
- duration-sensitive asset weakness / strength
- cyclicals vs defensives
- policy/news direction
- credit / liquidity stress proxies

## Suggested Alert Levels
Instead of emitting binary verdicts, use levels:

- `observe`
  - weak evidence
  - no action bias
- `watch`
  - multiple signals align
  - review next report cycle
- `warning`
  - stronger evidence of deterioration or mispricing
  - consider whether target allocation or risk posture needs review

## Recommended Report Structure
If V2 is implemented, each risk/research item should include:
- signal_name
- summary
- evidence
- data_window
- confidence
- impact_scope
- suggested_follow_up

Example:
- signal_name: `suspected_distribution`
- summary: `price made new highs but OBV and CMF failed to confirm`
- evidence: `OBV lower high, CMF fell below prior peak, 20-day volume elevated`
- data_window: `20d / 60d`
- confidence: `medium`
- impact_scope: `stock sleeve / AI theme`
- suggested_follow_up: `monitor next monthly review before changing long-term target`

## Open-Source Reference Strategy
Do not directly trust outside trading repos.

Safer approach:
1. use mature libraries only for indicator calculation or portfolio statistics
2. re-implement project-specific decision rules in our own codebase
3. keep external dependencies small and auditable

Reasonable reference candidates:
- `bukosabino/ta`
  - useful for technical indicators like A/D-family, momentum, volatility
  - better used as a formula/reference layer than as business logic
  - https://github.com/bukosabino/ta
- `ranaroussi/quantstats`
  - useful for Sharpe, drawdown, rolling stats, report metrics
  - better used for analytics than for buy/sell judgment
  - https://github.com/ranaroussi/quantstats

## Security Review Rules For External Repos
Before adopting any external code or package:
- inspect license, maintainer activity, release cadence, and issue history
- inspect dependency tree size
- inspect for suspicious patterns such as:
  - hidden network calls
  - shell execution
  - dynamic code execution
  - serialized object loading without controls
  - bundled secrets or API keys
- run dependency review and code scanning where possible
- prefer copying formulas or rewriting small indicator logic ourselves

Supporting references:
- GitHub dependency review
  https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/customizing-your-dependency-review-action-configuration
- GitHub code scanning
  https://docs.github.com/github/finding-security-vulnerabilities-and-errors-in-your-code
- OpenSSF Scorecard
  https://github.com/ossf/scorecard

## Provisional Product Recommendation
For this project's early stage, the most defensible V2 rollout order is:

1. expand position model to track amount, shares, and change history
2. add report metrics for fund risk/return and valuation fields
3. add conservative warning signals for divergence, crowding, valuation stretch,
   and concentration
4. only later add macro-regime-driven target-allocation adjustment

This is an inference from the current project maturity:
- data quality and explainability matter more right now than prediction power
- if the base records are weak, higher-order financial judgment will be noisy

## Bottom Line
The system should not try to "sound like a trader."
It should try to:
- preserve evidence
- label uncertainty
- separate observation from recommendation
- keep long-term allocation discipline visible even when short-term signals appear
