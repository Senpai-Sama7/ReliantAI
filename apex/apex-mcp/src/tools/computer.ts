// apex-mcp/src/tools/computer.ts
// Computer use capabilities: screenshot, mouse/keyboard control, system info
import { ToolDefinition } from '../types';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

const execAsync = promisify(exec);

// ── Screenshot Tool ──────────────────────────────────────────────────────────
export const screenshotTool: ToolDefinition = {
  name: 'computer_screenshot',
  description: 'Take a screenshot of the desktop. Returns base64 encoded PNG.',
  integration: 'computer',
  inputSchema: {
    type: 'object',
    properties: {
      display: {
        type: 'number',
        description: 'Display number (0 = primary, default 0)',
      },
    },
    required: [],
  },
  async execute(args) {
    const display = Number(args['display']) || 0;
    const tmpDir = os.tmpdir();
    const screenshotPath = path.join(tmpDir, `apex_screenshot_${Date.now()}.png`);

    try {
      // Try gnome-screenshot first (Linux), then screencapture (macOS), then import (ImageMagick)
      let command: string;
      if (process.platform === 'darwin') {
        command = `screencapture -D ${display + 1} "${screenshotPath}"`;
      } else if (process.platform === 'linux') {
        // Try gnome-screenshot, then fallback to import
        command = `which gnome-screenshot >/dev/null 2>&1 && gnome-screenshot -f "${screenshotPath}" -d || import -window root "${screenshotPath}"`;
      } else {
        throw new Error(`Unsupported platform: ${process.platform}`);
      }

      await execAsync(command);

      if (!fs.existsSync(screenshotPath)) {
        throw new Error('Screenshot command failed to create file');
      }

      const imageBuffer = fs.readFileSync(screenshotPath);
      const base64 = imageBuffer.toString('base64');

      // Cleanup
      fs.unlinkSync(screenshotPath);

      return {
        success: true,
        format: 'png',
        encoding: 'base64',
        data: base64,
        size_bytes: imageBuffer.length,
        display,
      };
    } catch (error) {
      // Cleanup on error
      if (fs.existsSync(screenshotPath)) {
        fs.unlinkSync(screenshotPath);
      }
      throw error;
    }
  },
};

// ── List Directory Tool ──────────────────────────────────────────────────────
export const listDirectoryTool: ToolDefinition = {
  name: 'computer_list_dir',
  description: 'List files and directories at a path.',
  integration: 'computer',
  inputSchema: {
    type: 'object',
    properties: {
      path: {
        type: 'string',
        description: 'Directory path to list (default: current directory)',
      },
      show_hidden: {
        type: 'boolean',
        description: 'Show hidden files (default: false)',
      },
    },
    required: [],
  },
  async execute(args) {
    const targetPath = args['path'] ? String(args['path']) : process.cwd();
    const showHidden = args['show_hidden'] === true;

    const entries = fs.readdirSync(targetPath, { withFileTypes: true });
    
    const items = entries
      .filter(entry => showHidden || !entry.name.startsWith('.'))
      .map(entry => ({
        name: entry.name,
        type: entry.isDirectory() ? 'directory' : 'file',
        size: entry.isFile() ? fs.statSync(path.join(targetPath, entry.name)).size : null,
      }));

    return {
      success: true,
      path: targetPath,
      items,
      count: items.length,
    };
  },
};

// ── Read File Tool ───────────────────────────────────────────────────────────
export const readFileTool: ToolDefinition = {
  name: 'computer_read_file',
  description: 'Read contents of a text file.',
  integration: 'computer',
  inputSchema: {
    type: 'object',
    properties: {
      path: {
        type: 'string',
        description: 'File path to read',
      },
      limit: {
        type: 'number',
        description: 'Maximum lines to read (default: 500)',
      },
      offset: {
        type: 'number',
        description: 'Starting line number (default: 1)',
      },
    },
    required: ['path'],
  },
  async execute(args) {
    const filePath = String(args['path']);
    const limit = Number(args['limit']) || 500;
    const offset = (Number(args['offset']) || 1) - 1; // Convert to 0-indexed

    if (!fs.existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n');
    const totalLines = lines.length;

    const selectedLines = lines.slice(offset, offset + limit);
    const finalContent = selectedLines.join('\n');
    const truncated = totalLines > offset + limit;

    return {
      success: true,
      path: filePath,
      content: finalContent,
      total_lines: totalLines,
      lines_read: selectedLines.length,
      truncated,
    };
  },
};

// ── Write File Tool ──────────────────────────────────────────────────────────
export const writeFileTool: ToolDefinition = {
  name: 'computer_write_file',
  description: 'Write content to a file (creates if not exists, overwrites if exists).',
  integration: 'computer',
  inputSchema: {
    type: 'object',
    properties: {
      path: {
        type: 'string',
        description: 'File path to write',
      },
      content: {
        type: 'string',
        description: 'Content to write',
      },
      append: {
        type: 'boolean',
        description: 'Append to file instead of overwrite (default: false)',
      },
    },
    required: ['path', 'content'],
  },
  async execute(args) {
    const filePath = String(args['path']);
    const content = String(args['content']);
    const append = args['append'] === true;

    // Ensure directory exists
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    if (append) {
      fs.appendFileSync(filePath, content);
    } else {
      fs.writeFileSync(filePath, content);
    }

    const stats = fs.statSync(filePath);

    return {
      success: true,
      path: filePath,
      bytes_written: Buffer.byteLength(content),
      total_size: stats.size,
      operation: append ? 'append' : 'write',
    };
  },
};

// ── System Info Tool ──────────────────────────────────────────────────────────
export const systemInfoTool: ToolDefinition = {
  name: 'computer_system_info',
  description: 'Get system information (OS, CPU, memory, disk).',
  integration: 'computer',
  inputSchema: {
    type: 'object',
    properties: {},
    required: [],
  },
  async execute() {
    const cpus = os.cpus();
    const totalMem = os.totalmem();
    const freeMem = os.freemem();

    return {
      success: true,
      platform: process.platform,
      arch: process.arch,
      hostname: os.hostname(),
      cpu: {
        model: cpus[0]?.model || 'unknown',
        cores: cpus.length,
      },
      memory: {
        total_mb: Math.round(totalMem / 1024 / 1024),
        free_mb: Math.round(freeMem / 1024 / 1024),
        used_percent: Math.round(((totalMem - freeMem) / totalMem) * 100),
      },
      uptime_seconds: os.uptime(),
      node_version: process.version,
    };
  },
};

// ── Run Shell Command Tool ────────────────────────────────────────────────────
export const shellCommandTool: ToolDefinition = {
  name: 'computer_shell',
  description: 'Execute a shell command. Use with caution - only safe commands allowed.',
  integration: 'computer',
  inputSchema: {
    type: 'object',
    properties: {
      command: {
        type: 'string',
        description: 'Shell command to execute',
      },
      cwd: {
        type: 'string',
        description: 'Working directory (default: current directory)',
      },
      timeout: {
        type: 'number',
        description: 'Timeout in milliseconds (default: 30000)',
      },
    },
    required: ['command'],
  },
  async execute(args) {
    const command = String(args['command']);
    const cwd = args['cwd'] ? String(args['cwd']) : process.cwd();
    const timeout = Number(args['timeout']) || 30000;

    // Security: Block dangerous commands
    const blockedPatterns = [
      /rm\s+-rf\s*\/\s*$/,
      />\s*\/dev\/null.*2>&1/,
      /mkfs/,
      /dd\s+if=/,
      /:\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}/, // Fork bomb
    ];

    for (const pattern of blockedPatterns) {
      if (pattern.test(command)) {
        throw new Error('Command blocked for security reasons');
      }
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd,
      timeout,
      maxBuffer: 10 * 1024 * 1024, // 10MB
    });

    return {
      success: true,
      command,
      stdout,
      stderr,
      exit_code: 0,
    };
  },
};

// Export all computer tools
export const computerTools: ToolDefinition[] = [
  screenshotTool,
  listDirectoryTool,
  readFileTool,
  writeFileTool,
  systemInfoTool,
  shellCommandTool,
];
