// apex-mcp/src/circuit-breaker.ts
import { CircuitBreakerStatus } from './types';

type State = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

interface Config {
  failureThreshold: number;
  resetTimeoutMs:   number;
  halfOpenMaxCalls: number;
}

const DEFAULT_CONFIG: Config = {
  failureThreshold: 3,
  resetTimeoutMs:   30_000,
  halfOpenMaxCalls: 1,
};

export class CircuitBreaker {
  private state:         State  = 'CLOSED';
  private failureCount:  number = 0;
  private lastFailTime:  number = 0;
  private halfOpenCalls: number = 0;

  constructor(
    private readonly name:   string,
    private readonly config: Config = DEFAULT_CONFIG,
  ) {}

  get status(): CircuitBreakerStatus {
    return { name: this.name, state: this.state, failures: this.failureCount };
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    // OPEN — check if reset window has elapsed
    if (this.state === 'OPEN') {
      const elapsed = Date.now() - this.lastFailTime;
      if (elapsed >= this.config.resetTimeoutMs) {
        this.state        = 'HALF_OPEN';
        this.halfOpenCalls = 0;
      } else {
        const retryIn = Math.ceil((this.config.resetTimeoutMs - elapsed) / 1000);
        throw new Error(
          `[CircuitBreaker:${this.name}] OPEN — retry in ${retryIn}s`
        );
      }
    }

    // HALF_OPEN — allow only one probe
    if (this.state === 'HALF_OPEN') {
      if (this.halfOpenCalls >= this.config.halfOpenMaxCalls) {
        throw new Error(
          `[CircuitBreaker:${this.name}] HALF_OPEN — probe already in progress`
        );
      }
      this.halfOpenCalls++;
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (err) {
      this.onFailure();
      throw err;
    }
  }

  private onSuccess(): void {
    this.failureCount = 0;
    this.state        = 'CLOSED';
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailTime = Date.now();
    if (
      this.state === 'HALF_OPEN' ||
      this.failureCount >= this.config.failureThreshold
    ) {
      this.state = 'OPEN';
    }
  }
}

// ── Global breaker registry, one per integration name ───────────────────────────
const breakers = new Map<string, CircuitBreaker>();

export function getBreaker(name: string): CircuitBreaker {
  if (!breakers.has(name)) {
    breakers.set(name, new CircuitBreaker(name));
  }
  return breakers.get(name)!;
}

export function getAllBreakerStatuses(): CircuitBreakerStatus[] {
  return Array.from(breakers.values()).map((b) => b.status);
}
