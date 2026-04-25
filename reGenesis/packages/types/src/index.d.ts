export interface BreakpointConfig {
  name: string;
  width: number;
  height: number;
}

export interface OptimizationPlugin {
  name: string;
  apply: (data: unknown) => Promise<unknown>;
}

export interface ReplicationOptions {
  viewport: { width: number; height: number };
  userAgent: string;
  timeout: number;
  pageConcurrency: number;
  baseAssetConcurrency: number;
  domainAssetConcurrency: number;
  maxRetries: number;
  retryDelayBase: number;
  incremental: boolean;
  crawlSPA: boolean;
  maxCrawlDepth: number;
  respectRobotsTxt: boolean;
  optimizeImages: boolean;
  enableAVIF: boolean;
  minifyCSS: boolean;
  minifyHTML?: boolean;
  captureResponsive: boolean;
  responsiveBreakpoints: BreakpointConfig[];
  enableBrotli: boolean;
  memoryThreshold: number;
  allowedDomains: string[];
  maxAssetSize: number;
  requestTimeout: number;
  requestInterval: number;
  optimizationPlugins?: OptimizationPlugin[];
}

export interface AssetManifest {
  originalUrl: string;
  contentType: string;
  size: number;
  integrity: string;
  etag?: string;
  lastModified?: string;
}

export interface ReplicationResult {
  success: boolean;
  url: string;
  assets: AssetManifest[];
  error?: string;
}