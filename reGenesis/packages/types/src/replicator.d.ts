export interface BreakpointConfig {
  name: string;
  width: number;
  height: number;
}

export interface OptimizationPlugin {
  name: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  apply: (data: any) => Promise<any>;
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

