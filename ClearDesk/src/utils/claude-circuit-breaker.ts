/**
 * Circuit breaker for Claude API calls
 * Prevents cascade failures when Anthropic API is rate limited or down
 */

type CircuitState = 'closed' | 'open' | 'half-open';

interface CircuitBreakerConfig {
  failureThreshold: number;
  successThreshold: number;
  timeoutMs: number;
  halfOpenMaxCalls: number;
}

interface CircuitStats {
  state: CircuitState;
  failureCount: number;
  successCount: number;
  lastFailureTime: number | null;
}

class ClaudeCircuitBreaker {
  private state: CircuitState = 'closed';
  private failureCount = 0;
  private successCount = 0;
  private lastFailureTime: number | null = null;
  private halfOpenCalls = 0;
  private config: CircuitBreakerConfig;

  constructor(config: Partial<CircuitBreakerConfig> = {}) {
    this.config = {
      failureThreshold: 5,
      successThreshold: 3,
      timeoutMs: 60000, // 1 minute
      halfOpenMaxCalls: 2,
      ...config,
    };
  }

  private canExecute(): boolean {
    if (this.state === 'closed') return true;

    if (this.state === 'open') {
      if (this.lastFailureTime) {
        const elapsed = Date.now() - this.lastFailureTime;
        if (elapsed >= this.config.timeoutMs) {
          this.state = 'half-open';
          this.halfOpenCalls = 0;
          return true;
        }
      }
      return false;
    }

    if (this.state === 'half-open') {
      if (this.halfOpenCalls < this.config.halfOpenMaxCalls) {
        this.halfOpenCalls++;
        return true;
      }
      return false;
    }

    return true;
  }

  private onSuccess(): void {
    if (this.state === 'half-open') {
      this.successCount++;
      if (this.successCount >= this.config.successThreshold) {
        this.close();
      }
    } else if (this.state === 'closed') {
      this.failureCount = 0;
    }
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.state === 'half-open') {
      this.open();
    } else if (this.state === 'closed') {
      if (this.failureCount >= this.config.failureThreshold) {
        this.open();
      }
    }
  }

  private open(): void {
    this.state = 'open';
    this.successCount = 0;
    console.warn('[ClaudeCircuitBreaker] Circuit OPENED');
  }

  private close(): void {
    this.state = 'closed';
    this.failureCount = 0;
    this.successCount = 0;
    this.halfOpenCalls = 0;
    this.lastFailureTime = null;
    console.info('[ClaudeCircuitBreaker] Circuit CLOSED');
  }

  async execute<T>(fn: () => Promise<T>, fallback?: () => Promise<T>): Promise<T> {
    if (!this.canExecute()) {
      if (fallback) {
        console.warn('[ClaudeCircuitBreaker] Executing fallback');
        return fallback();
      }
      throw new Error('Claude circuit breaker is OPEN');
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  getStats(): CircuitStats {
    return {
      state: this.state,
      failureCount: this.failureCount,
      successCount: this.successCount,
      lastFailureTime: this.lastFailureTime,
    };
  }

  isHealthy(): boolean {
    return this.state === 'closed';
  }
}

// Singleton instance
let circuitBreaker: ClaudeCircuitBreaker | null = null;

export function getCircuitBreaker(): ClaudeCircuitBreaker {
  if (!circuitBreaker) {
    circuitBreaker = new ClaudeCircuitBreaker();
  }
  return circuitBreaker;
}

export function resetCircuitBreaker(): void {
  circuitBreaker = null;
}

// Retry wrapper with exponential backoff
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      if (attempt < maxRetries) {
        const delay = baseDelayMs * Math.pow(2, attempt);
        console.warn(`[Retry] Attempt ${attempt + 1} failed, retrying in ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError;
}

// Combined circuit breaker + retry wrapper
export async function withResilience<T>(
  fn: () => Promise<T>,
  fallback?: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  const breaker = getCircuitBreaker();
  
  return breaker.execute(
    () => withRetry(fn, maxRetries),
    fallback
  );
}

export type { CircuitStats, CircuitBreakerConfig };
