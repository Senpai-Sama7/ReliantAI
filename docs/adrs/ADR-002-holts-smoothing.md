# ADR-002: Use Holt's Double Exponential Smoothing for AI Predictions

## Status
Accepted (2024-02-01)

## Context
The orchestrator needs to predict future CPU, memory, and response time for all
platform services to drive auto-scaling decisions. Key requirements:

1. **Low latency**: Prediction must complete in < 10ms (runs every 5 minutes).
2. **Trend detection**: Must distinguish between temporary spikes and sustained growth.
3. **No external dependencies**: Cannot rely on cloud ML APIs (Gemini/Vertex) for core infra.
4. **Explainable**: Scaling decisions must be auditable (not a black box).

## Decision
Use **Holt's double exponential smoothing** (a.k.a. two-parameter exponential smoothing)
with α=0.3 (level smoothing) and β=0.1 (trend smoothing).

### Formula
```
level_t   = α * observation + (1-α) * (level_{t-1} + trend_{t-1})
trend_t   = β * (level_t - level_{t-1}) + (1-β) * trend_{t-1}
forecast_{t+k} = level_t + k * trend_t     (k=2 for 2-step-ahead)
```

### Implementation
```python
@dataclass
class HoltState:
    level: float = 0.0
    trend: float = 0.0
    alpha: float = 0.3
    beta: float = 0.1

    def update(self, value: float) -> float:
        if self.level == 0.0 and self.trend == 0.0:
            # First observation initializes both
            self.level = value
            return value
        new_level = self.alpha * value + (1 - self.alpha) * (self.level + self.trend)
        new_trend = self.beta * (new_level - self.level) + (1 - self.beta) * self.trend
        self.level = new_level
        self.trend = new_trend
        return self.level + 2 * self.trend  # 2-step-ahead forecast
```

## Consequences

### Positive
- **Sub-millisecond predictions** — pure arithmetic, no network calls.
- **Trend-aware** — correctly identifies sustained growth vs noise.
- **Deterministic** — same input → same output every time (auditable).
- **No external dependencies** — works offline, no API keys, no rate limits.
- **Memory efficient** — O(1) state per metric (just `level` + `trend`).

### Negative
- **Assumes linear trend** — exponential growth (e.g. viral load) is underestimated.
- **No seasonality** — daily/weekly patterns (e.g. business hours) not captured.
- **Cold-start penalty** — first 3-5 observations are noisy until level stabilizes.
- **Hyperparameter sensitivity** — α=0.3/β=0.1 chosen for stability; may need tuning.

## Mitigation
- Cold-start: Seed with 3 historical values if available.
- Trend limits: Cap forecast at 2x current level to prevent runaway predictions.
- Seasonality: Not needed for infra metrics (5-minute resolution smooths daily patterns).
- Alternatives: Triple exponential smoothing (Holt-Winters) considered but rejected for
  unnecessary complexity — no clear seasonal pattern in CPU/memory at 5min granularity.

## Alternatives Considered
- **ARIMA**: Rejected — overkill for univariate 5-minute infra metrics; needs `statsmodels`.
- **LSTM (PyTorch/TensorFlow)**: Rejected — heavy dependency, needs GPU for training,
  non-deterministic, poor explainability.
- **Prophet (Meta)**: Rejected — Python-only, heavy pandas dependency, slower than Holt's.
- **Simple moving average**: Rejected — no trend detection; lags behind actual growth.
- **Rule-based thresholds only**: Rejected — purely reactive; cannot preemptively scale.
