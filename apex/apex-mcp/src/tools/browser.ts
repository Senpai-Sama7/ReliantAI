// apex-mcp/src/tools/browser.ts
// Browser automation via Playwright for agent computer use capabilities
import { ToolDefinition } from '../types';
import { chromium, Browser, Page, BrowserContext } from 'playwright';

// Browser instance cache (one per process to avoid overhead)
let browserInstance: Browser | null = null;
let browserContext: BrowserContext | null = null;
let activePage: Page | null = null;

async function getBrowser(): Promise<Browser> {
  if (!browserInstance) {
    browserInstance = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
  }
  return browserInstance;
}

async function getContext(): Promise<BrowserContext> {
  if (!browserContext) {
    const browser = await getBrowser();
    browserContext = await browser.newContext({
      viewport: { width: 1280, height: 720 },
      userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    });
  }
  return browserContext;
}

async function getPage(): Promise<Page> {
  if (!activePage) {
    const context = await getContext();
    activePage = await context.newPage();
  }
  return activePage;
}

// Cleanup function for graceful shutdown
export async function cleanupBrowser(): Promise<void> {
  if (activePage) {
    await activePage.close();
    activePage = null;
  }
  if (browserContext) {
    await browserContext.close();
    browserContext = null;
  }
  if (browserInstance) {
    await browserInstance.close();
    browserInstance = null;
  }
}

// ── Browser Navigate Tool ────────────────────────────────────────────────────
export const browserNavigateTool: ToolDefinition = {
  name: 'browser_navigate',
  description: 'Navigate to a URL in the browser. Use this to load web pages for scraping, form filling, or interaction.',
  integration: 'browser',
  inputSchema: {
    type: 'object',
    properties: {
      url: {
        type: 'string',
        description: 'URL to navigate to (must include http:// or https://)',
      },
      wait_until: {
        type: 'string',
        description: 'When to consider navigation complete',
        enum: ['load', 'domcontentloaded', 'networkidle'],
      },
      timeout: {
        type: 'number',
        description: 'Navigation timeout in milliseconds (default 30000)',
      },
    },
    required: ['url'],
  },
  async execute(args) {
    const page = await getPage();
    const url = String(args['url']);
    const waitUntil = (args['wait_until'] as 'load' | 'domcontentloaded' | 'networkidle') || 'domcontentloaded';
    const timeout = Number(args['timeout']) || 30000;

    await page.goto(url, { waitUntil, timeout });
    const title = await page.title();
    const currentUrl = page.url();

    return {
      success: true,
      title,
      url: currentUrl,
      message: `Navigated to ${currentUrl}`,
    };
  },
};

// ── Browser Click Tool ──────────────────────────────────────────────────────
export const browserClickTool: ToolDefinition = {
  name: 'browser_click',
  description: 'Click on an element in the browser. Use CSS selector or element description.',
  integration: 'browser',
  inputSchema: {
    type: 'object',
    properties: {
      selector: {
        type: 'string',
        description: 'CSS selector for the element to click',
      },
      text: {
        type: 'string',
        description: 'Text content to find and click (alternative to selector)',
      },
      timeout: {
        type: 'number',
        description: 'Wait timeout in milliseconds (default 5000)',
      },
    },
    required: [],
  },
  async execute(args) {
    const page = await getPage();
    const selector = args['selector'] ? String(args['selector']) : null;
    const text = args['text'] ? String(args['text']) : null;
    const timeout = Number(args['timeout']) || 5000;

    if (!selector && !text) {
      throw new Error('Either selector or text must be provided');
    }

    let element;
    if (selector) {
      await page.waitForSelector(selector, { timeout });
      element = await page.locator(selector).first();
    } else {
      element = await page.getByText(text!).first();
    }

    await element.click();
    await page.waitForTimeout(500); // Small delay for any navigation/state change

    return {
      success: true,
      message: `Clicked ${selector || `text "${text}"`}`,
      current_url: page.url(),
    };
  },
};

// ── Browser Type Tool ───────────────────────────────────────────────────────
export const browserTypeTool: ToolDefinition = {
  name: 'browser_type',
  description: 'Type text into an input field. Use for form filling.',
  integration: 'browser',
  inputSchema: {
    type: 'object',
    properties: {
      selector: {
        type: 'string',
        description: 'CSS selector for the input field',
      },
      text: {
        type: 'string',
        description: 'Text to type',
      },
      clear_first: {
        type: 'boolean',
        description: 'Clear the field before typing (default true)',
      },
      submit: {
        type: 'boolean',
        description: 'Press Enter after typing (default false)',
      },
    },
    required: ['selector', 'text'],
  },
  async execute(args) {
    const page = await getPage();
    const selector = String(args['selector']);
    const text = String(args['text']);
    const clearFirst = args['clear_first'] !== false;
    const submit = args['submit'] === true;

    const locator = page.locator(selector).first();
    
    if (clearFirst) {
      await locator.fill(text);
    } else {
      await locator.pressSequentially(text);
    }

    if (submit) {
      await locator.press('Enter');
    }

    return {
      success: true,
      message: `Typed "${text}" into ${selector}${submit ? ' and submitted' : ''}`,
    };
  },
};

// ── Browser Screenshot Tool ─────────────────────────────────────────────────
export const browserScreenshotTool: ToolDefinition = {
  name: 'browser_screenshot',
  description: 'Take a screenshot of the current page. Returns base64 encoded image.',
  integration: 'browser',
  inputSchema: {
    type: 'object',
    properties: {
      full_page: {
        type: 'boolean',
        description: 'Capture full page or just viewport (default false)',
      },
      selector: {
        type: 'string',
        description: 'CSS selector to screenshot specific element (optional)',
      },
    },
    required: [],
  },
  async execute(args) {
    const page = await getPage();
    const fullPage = args['full_page'] === true;
    const selector = args['selector'] ? String(args['selector']) : null;

    let screenshot: Buffer;
    if (selector) {
      const element = page.locator(selector).first();
      screenshot = await element.screenshot();
    } else {
      screenshot = await page.screenshot({ fullPage });
    }

    const base64 = screenshot.toString('base64');

    return {
      success: true,
      format: 'png',
      encoding: 'base64',
      data: base64,
      size_bytes: screenshot.length,
    };
  },
};

// ── Browser Extract Text Tool ───────────────────────────────────────────────
export const browserExtractTextTool: ToolDefinition = {
  name: 'browser_extract_text',
  description: 'Extract text content from the page or specific elements.',
  integration: 'browser',
  inputSchema: {
    type: 'object',
    properties: {
      selector: {
        type: 'string',
        description: 'CSS selector to extract from (default: body)',
      },
      visible_only: {
        type: 'boolean',
        description: 'Only extract visible text (default true)',
      },
    },
    required: [],
  },
  async execute(args) {
    const page = await getPage();
    const selector = args['selector'] ? String(args['selector']) : 'body';
    const visibleOnly = args['visible_only'] !== false;

    const locator = page.locator(selector).first();
    let text: string;

    if (visibleOnly) {
      text = await locator.innerText();
    } else {
      text = await locator.textContent() || '';
    }

    // Clean up whitespace
    text = text.replace(/\s+/g, ' ').trim();

    // Limit length for token management
    const maxLength = 10000;
    const truncated = text.length > maxLength;
    const finalText = truncated ? text.substring(0, maxLength) + '... [truncated]' : text;

    return {
      success: true,
      text: finalText,
      length: text.length,
      truncated,
      selector,
    };
  },
};

// ── Browser Scroll Tool ─────────────────────────────────────────────────────
export const browserScrollTool: ToolDefinition = {
  name: 'browser_scroll',
  description: 'Scroll the page vertically or to a specific element.',
  integration: 'browser',
  inputSchema: {
    type: 'object',
    properties: {
      direction: {
        type: 'string',
        description: 'Scroll direction',
        enum: ['up', 'down', 'top', 'bottom', 'to_element'],
      },
      amount: {
        type: 'number',
        description: 'Pixels to scroll for up/down (default 500)',
      },
      selector: {
        type: 'string',
        description: 'Element to scroll to (when direction is to_element)',
      },
    },
    required: ['direction'],
  },
  async execute(args) {
    const page = await getPage();
    const direction = String(args['direction']);
    const amount = Number(args['amount']) || 500;

    switch (direction) {
      case 'up':
        await page.evaluate((amt: number) => window.scrollBy(0, -amt), amount);
        break;
      case 'down':
        await page.evaluate((amt: number) => window.scrollBy(0, amt), amount);
        break;
      case 'top':
        await page.evaluate(() => window.scrollTo(0, 0));
        break;
      case 'bottom':
        await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
        break;
      case 'to_element':
        const selector = String(args['selector']);
        await page.locator(selector).first().scrollIntoViewIfNeeded();
        break;
      default:
        throw new Error(`Unknown direction: ${direction}`);
    }

    const scrollY = await page.evaluate(() => window.scrollY);

    return {
      success: true,
      direction,
      scroll_y: scrollY,
    };
  },
};

// ── Browser Get HTML Tool ───────────────────────────────────────────────────
export const browserGetHtmlTool: ToolDefinition = {
  name: 'browser_get_html',
  description: 'Get the HTML content of the page or a specific element.',
  integration: 'browser',
  inputSchema: {
    type: 'object',
    properties: {
      selector: {
        type: 'string',
        description: 'CSS selector (default: html)',
      },
    },
    required: [],
  },
  async execute(args) {
    const page = await getPage();
    const selector = args['selector'] ? String(args['selector']) : 'html';

    const locator = page.locator(selector).first();
    const html = await locator.innerHTML();

    // Limit size
    const maxLength = 50000;
    const truncated = html.length > maxLength;
    const finalHtml = truncated ? html.substring(0, maxLength) + '... [truncated]' : html;

    return {
      success: true,
      html: finalHtml,
      length: html.length,
      truncated,
    };
  },
};

// ── Browser Close Tool ──────────────────────────────────────────────────────
export const browserCloseTool: ToolDefinition = {
  name: 'browser_close',
  description: 'Close the browser and cleanup resources.',
  integration: 'browser',
  inputSchema: {
    type: 'object',
    properties: {},
    required: [],
  },
  async execute() {
    await cleanupBrowser();
    return {
      success: true,
      message: 'Browser closed successfully',
    };
  },
};

// Export all browser tools
export const browserTools: ToolDefinition[] = [
  browserNavigateTool,
  browserClickTool,
  browserTypeTool,
  browserScreenshotTool,
  browserExtractTextTool,
  browserScrollTool,
  browserGetHtmlTool,
  browserCloseTool,
];
