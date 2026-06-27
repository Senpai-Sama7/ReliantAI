import { EventEmitter } from 'node:events';

export class AdvancedCircuitBreaker extends EventEmitter {
  constructor(opts = {}) {
    super();
    this.failureThreshold = opts.failureThreshold ?? 5;
    this.successThreshold = opts.successThreshold ?? 3;
    this.timeout = opts.timeout ?? 30000;
    this.retryTimeoutBase = opts.retryTimeoutBase ?? 1000;
    this.state = 'CLOSED';
    this.failureCount = 0;
    this.successCount = 0;
    this.nextAttempt = Date.now();
  }
  async execute(operation) {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) throw new Error('Circuit breaker is OPEN.');
      this.state = 'HALF_OPEN';
      this.successCount = 0;
    }
    try {
      const result = await Promise.race([
        operation(),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Operation timed out.')), this.timeout))
      ]);
      this.onSuccess();
      return result;
    } catch (e) {
      this.onFailure();
      throw e;
    }
  }
  onSuccess() {
    this.failureCount = 0;
    if (this.state === 'HALF_OPEN') {
      this.successCount++;
      if (this.successCount >= this.successThreshold) {
        this.state = 'CLOSED';
        this.emit('close');
      }
    } else {
      this.state = 'CLOSED';
    }
    this.emit('success');
  }
  onFailure() {
    this.failureCount++;
    if (this.state === 'HALF_OPEN' || this.failureCount >= this.failureThreshold) {
      this.state = 'OPEN';
      const exponent = this.failureCount - this.failureThreshold;
      const wait = this.retryTimeoutBase * Math.pow(2, Math.max(0, exponent));
      this.nextAttempt = Date.now() + wait;
      this.emit('open');
    }
    this.emit('failure');
  }
}
