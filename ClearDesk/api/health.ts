import type { VercelRequest, VercelResponse } from '@vercel/node';

/**
 * Health check endpoint for ClearDesk AR processing
 * Returns service status, Claude API connectivity, and metrics
 */
export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const checks = {
    timestamp: new Date().toISOString(),
    service: 'ClearDesk',
    version: '1.0.0',
    status: 'healthy' as 'healthy' | 'degraded' | 'unhealthy',
    checks: {} as Record<string, { status: string; responseTime?: number; error?: string }>,
  };

  // Check Claude API connectivity
  const startTime = Date.now();
  try {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      checks.checks.claude = { status: 'unconfigured', error: 'ANTHROPIC_API_KEY not set' };
      checks.status = 'degraded';
    } else {
      // Lightweight Claude API check
      const response = await fetch('https://api.anthropic.com/v1/models', {
        method: 'GET',
        headers: {
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
        },
      });

      if (response.ok) {
        checks.checks.claude = {
          status: 'healthy',
          responseTime: Date.now() - startTime,
        };
      } else {
        checks.checks.claude = {
          status: 'unhealthy',
          error: `API returned ${response.status}`,
          responseTime: Date.now() - startTime,
        };
        checks.status = 'degraded';
      }
    }
  } catch (error) {
    checks.checks.claude = {
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown error',
      responseTime: Date.now() - startTime,
    };
    checks.status = 'degraded';
  }

  // Check storage
  try {
    const hasBlobToken = !!process.env.BLOB_READ_WRITE_TOKEN;
    const isProduction = process.env.VERCEL_ENV === 'production';
    
    if (isProduction && !hasBlobToken) {
      checks.checks.storage = { status: 'unconfigured', error: 'BLOB_READ_WRITE_TOKEN not set' };
      checks.status = 'degraded';
    } else {
      checks.checks.storage = {
        status: hasBlobToken ? 'blob' : 'json-fallback',
      };
    }
  } catch (error) {
    checks.checks.storage = {
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }

  // Circuit breaker status (if available)
  checks.checks.circuitBreaker = { status: 'not-implemented' };

  const statusCode = checks.status === 'healthy' ? 200 : 
                     checks.status === 'degraded' ? 200 : 503;

  return res.status(statusCode).json(checks);
}
