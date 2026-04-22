// apex-mcp/src/tools/code_execution.ts
// Sandboxed code execution for Python, JavaScript, and shell scripts
import { ToolDefinition } from '../types';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { createHash } from 'crypto';

const execAsync = promisify(exec);

// Execution sandbox configuration
const SANDBOX_CONFIG = {
  timeout_ms: 30000,
  max_output_bytes: 100 * 1024, // 100KB
  allowed_imports: [
    'math', 'random', 'datetime', 'json', 're', 'string', 'collections',
    'itertools', 'functools', 'statistics', 'typing', 'hashlib', 'uuid',
    'base64', 'urllib.parse', 'html', 'textwrap', 'decimal', 'fractions',
  ],
  blocked_patterns: [
    /import\s+os\b/,
    /import\s+sys\b/,
    /import\s+subprocess\b/,
    /__import__\s*\(/,
    /eval\s*\(/,
    /exec\s*\(/,
    /compile\s*\(/,
    /open\s*\(/,
    /file\s*\(/,
    /\.read\s*\(/,
    /\.write\s*\(/,
    /socket\./,
    /urllib\.request/,
    /http\./,
    /ftplib\./,
    /smtplib\./,
    /subprocess\./,
    /os\./,
    /sys\./,
    /shutil\./,
    /pathlib\./,
    /__file__/,
    /__name__\s*==\s*['"]__main__['"]/,
  ],
};

// ── Execute Python Code Tool ────────────────────────────────────────────────
export const executePythonTool: ToolDefinition = {
  name: 'code_execute_python',
  description: 'Execute Python code in a sandboxed environment. Safe for data processing, calculations, and transformations.',
  integration: 'code_execution',
  inputSchema: {
    type: 'object',
    properties: {
      code: {
        type: 'string',
        description: 'Python code to execute',
      },
      input_data: {
        type: 'object',
        description: 'Input data as JSON (accessible as variable `input_data`)',
      },
      timeout: {
        type: 'number',
        description: 'Execution timeout in milliseconds (default: 30000, max: 60000)',
      },
    },
    required: ['code'],
  },
  async execute(args) {
    const code = String(args['code']);
    const inputData = args['input_data'] || {};
    const timeout = Math.min(Number(args['timeout']) || SANDBOX_CONFIG.timeout_ms, 60000);

    // Security scan
    for (const pattern of SANDBOX_CONFIG.blocked_patterns) {
      if (pattern.test(code)) {
        throw new Error(`Security violation: Code matches blocked pattern ${pattern.source}`);
      }
    }

    const tmpDir = os.tmpdir();
    const scriptId = createHash('sha256').update(code + Date.now()).digest('hex').substring(0, 16);
    const scriptPath = path.join(tmpDir, `apex_python_${scriptId}.py`);

    // Create wrapper script with input data injection
    const wrapperCode = `
# APEX Code Execution Sandbox
data_input = ${JSON.stringify(inputData)}
result_output = {"success": True, "output": None, "error": None}

try:
${code.split('\n').map(line => '    ' + line).join('\n')}
    result_output["output"] = locals().get('result', None)
except Exception as e:
    result_output["success"] = False
    result_output["error"] = str(e)
    result_output["error_type"] = type(e).__name__

import json
print("__APEX_RESULT__" + json.dumps(result_output))
`;

    fs.writeFileSync(scriptPath, wrapperCode);

    try {
      const { stdout, stderr } = await execAsync(`python3 "${scriptPath}"`, {
        timeout,
        maxBuffer: SANDBOX_CONFIG.max_output_bytes,
        env: {
          ...process.env,
          PYTHONPATH: '',
          PYTHONDONTWRITEBYTECODE: '1',
        },
      });

      // Cleanup
      fs.unlinkSync(scriptPath);

      // Parse result
      const resultMatch = stdout.match(/__APEX_RESULT__(.+)/);
      if (resultMatch) {
        const result = JSON.parse(resultMatch[1]);
        return {
          success: result.success,
          output: result.output,
          error: result.error,
          error_type: result.error_type,
          stdout: stdout.replace(/__APEX_RESULT__.+/, '').trim(),
          stderr: stderr || null,
        };
      }

      return {
        success: true,
        output: stdout.trim(),
        stderr: stderr || null,
      };
    } catch (error) {
      // Cleanup on error
      if (fs.existsSync(scriptPath)) {
        fs.unlinkSync(scriptPath);
      }

      if (error instanceof Error && error.message.includes('timeout')) {
        throw new Error('Code execution timeout');
      }

      throw error;
    }
  },
};

// ── Execute JavaScript Code Tool ────────────────────────────────────────────
export const executeJavaScriptTool: ToolDefinition = {
  name: 'code_execute_javascript',
  description: 'Execute JavaScript/Node.js code in a sandboxed environment.',
  integration: 'code_execution',
  inputSchema: {
    type: 'object',
    properties: {
      code: {
        type: 'string',
        description: 'JavaScript code to execute',
      },
      input_data: {
        type: 'object',
        description: 'Input data as JSON (accessible as variable `inputData`)',
      },
      timeout: {
        type: 'number',
        description: 'Execution timeout in milliseconds (default: 30000)',
      },
    },
    required: ['code'],
  },
  async execute(args) {
    const code = String(args['code']);
    const inputData = args['input_data'] || {};
    const timeout = Math.min(Number(args['timeout']) || SANDBOX_CONFIG.timeout_ms, 60000);

    // Security scan
    const blockedJsPatterns = [
      /require\s*\(\s*['"](fs|child_process|os|path|net|http|https|crypto)['"]/,
      /import\s+.*\s+from\s+['"](fs|child_process|os|path|net|http|https)['"]/,
      /process\./,
      /global\./,
      /eval\s*\(/,
      /Function\s*\(/,
      /setTimeout\s*\(/,
      /setInterval\s*\(/,
      /fetch\s*\(/,
      /XMLHttpRequest/,
      /WebSocket/,
      /Worker/,
    ];

    for (const pattern of blockedJsPatterns) {
      if (pattern.test(code)) {
        throw new Error(`Security violation: Code matches blocked pattern ${pattern.source}`);
      }
    }

    const tmpDir = os.tmpdir();
    const scriptId = createHash('sha256').update(code + Date.now()).digest('hex').substring(0, 16);
    const scriptPath = path.join(tmpDir, `apex_js_${scriptId}.js`);

    // Create wrapper script
    const wrapperCode = `
// APEX Code Execution Sandbox
const inputData = ${JSON.stringify(inputData)};
let result = undefined;

try {
${code.split('\n').map(line => '  ' + line).join('\n')}
  console.log('__APEX_RESULT__' + JSON.stringify({ success: true, output: result }));
} catch (error) {
  console.log('__APEX_RESULT__' + JSON.stringify({ 
    success: false, 
    error: error.message,
    error_type: error.name 
  }));
}
`;

    fs.writeFileSync(scriptPath, wrapperCode);

    try {
      const { stdout, stderr } = await execAsync(`node "${scriptPath}"`, {
        timeout,
        maxBuffer: SANDBOX_CONFIG.max_output_bytes,
      });

      fs.unlinkSync(scriptPath);

      const resultMatch = stdout.match(/__APEX_RESULT__(.+)/);
      if (resultMatch) {
        const result = JSON.parse(resultMatch[1]);
        return {
          success: result.success,
          output: result.output,
          error: result.error,
          error_type: result.error_type,
          stdout: stdout.replace(/__APEX_RESULT__.+/, '').trim(),
          stderr: stderr || null,
        };
      }

      return {
        success: true,
        output: stdout.trim(),
        stderr: stderr || null,
      };
    } catch (error) {
      if (fs.existsSync(scriptPath)) {
        fs.unlinkSync(scriptPath);
      }
      throw error;
    }
  },
};

// ── Execute Shell Script Tool ───────────────────────────────────────────────
export const executeShellTool: ToolDefinition = {
  name: 'code_execute_shell',
  description: 'Execute a shell script. Limited to safe commands only.',
  integration: 'code_execution',
  inputSchema: {
    type: 'object',
    properties: {
      script: {
        type: 'string',
        description: 'Shell script content to execute',
      },
      timeout: {
        type: 'number',
        description: 'Execution timeout in milliseconds (default: 30000)',
      },
    },
    required: ['script'],
  },
  async execute(args) {
    const script = String(args['script']);
    const timeout = Math.min(Number(args['timeout']) || SANDBOX_CONFIG.timeout_ms, 60000);

    // Security scan for dangerous commands
    const dangerousPatterns = [
      /rm\s+-rf\s*\/\s*$/,
      />\s*\/dev\/null/,
      /mkfs/,
      /dd\s+if=/,
      /:\(\)\s*\{/,
      /curl\s+.*\|\s*sh/,
      /wget\s+.*\|\s*sh/,
      /sudo/,
      /su\s+-/,
      /passwd/,
      /useradd/,
      /usermod/,
      /chmod\s+777/,
    ];

    for (const pattern of dangerousPatterns) {
      if (pattern.test(script)) {
        throw new Error(`Security violation: Script matches blocked pattern ${pattern.source}`);
      }
    }

    const tmpDir = os.tmpdir();
    const scriptId = createHash('sha256').update(script + Date.now()).digest('hex').substring(0, 16);
    const scriptPath = path.join(tmpDir, `apex_shell_${scriptId}.sh`);

    fs.writeFileSync(scriptPath, script);
    fs.chmodSync(scriptPath, 0o700);

    try {
      const { stdout, stderr } = await execAsync(`bash "${scriptPath}"`, {
        timeout,
        maxBuffer: SANDBOX_CONFIG.max_output_bytes,
      });

      fs.unlinkSync(scriptPath);

      return {
        success: true,
        stdout,
        stderr: stderr || null,
        exit_code: 0,
      };
    } catch (error) {
      if (fs.existsSync(scriptPath)) {
        fs.unlinkSync(scriptPath);
      }
      throw error;
    }
  },
};

// ── Analyze Code Tool ────────────────────────────────────────────────────────
export const analyzeCodeTool: ToolDefinition = {
  name: 'code_analyze',
  description: 'Analyze code for errors, style issues, and improvements. Supports Python, JavaScript, TypeScript.',
  integration: 'code_execution',
  inputSchema: {
    type: 'object',
    properties: {
      code: {
        type: 'string',
        description: 'Code to analyze',
      },
      language: {
        type: 'string',
        description: 'Programming language',
        enum: ['python', 'javascript', 'typescript'],
      },
    },
    required: ['code', 'language'],
  },
  async execute(args) {
    const code = String(args['code']);
    const language = String(args['language']);

    const issues: Array<{ type: string; message: string; line?: number }> = [];

    if (language === 'python') {
      // Check for common Python issues
      const lines = code.split('\n');
      
      lines.forEach((line, index) => {
        // Check for bare except
        if (/^\s*except\s*:/.test(line)) {
          issues.push({ type: 'warning', message: 'Bare except clause - use specific exceptions', line: index + 1 });
        }
        // Check for mutable default args
        if (/def\s+\w+\s*\([^)]*=\s*(\[|\{)/.test(line)) {
          issues.push({ type: 'warning', message: 'Mutable default argument', line: index + 1 });
        }
        // Check for print statements (should use logging)
        if (/^\s*print\s*\(/.test(line)) {
          issues.push({ type: 'info', message: 'Consider using logging instead of print', line: index + 1 });
        }
      });

      // Try syntax check
      try {
        const tmpDir = os.tmpdir();
        const scriptPath = path.join(tmpDir, `apex_syntax_check_${Date.now()}.py`);
        fs.writeFileSync(scriptPath, code);
        await execAsync(`python3 -m py_compile "${scriptPath}"`, { timeout: 5000 });
        fs.unlinkSync(scriptPath);
      } catch (syntaxError) {
        issues.push({ type: 'error', message: 'Syntax error in code' });
      }
    } else if (language === 'javascript' || language === 'typescript') {
      const lines = code.split('\n');
      
      lines.forEach((line, index) => {
        // Check for console.log
        if (/console\.log\s*\(/.test(line)) {
          issues.push({ type: 'info', message: 'Consider removing console.log', line: index + 1 });
        }
        // Check for == instead of ===
        if (/[^=!]==[^=]/.test(line)) {
          issues.push({ type: 'warning', message: 'Use === instead of ==', line: index + 1 });
        }
        // Check for var
        if (/\bvar\b/.test(line)) {
          issues.push({ type: 'warning', message: 'Use let or const instead of var', line: index + 1 });
        }
      });
    }

    return {
      success: true,
      language,
      issues,
      issue_count: issues.length,
      summary: {
        errors: issues.filter(i => i.type === 'error').length,
        warnings: issues.filter(i => i.type === 'warning').length,
        info: issues.filter(i => i.type === 'info').length,
      },
    };
  },
};

// Export all code execution tools
export const codeExecutionTools: ToolDefinition[] = [
  executePythonTool,
  executeJavaScriptTool,
  executeShellTool,
  analyzeCodeTool,
];
