"use client";

import { useState, useCallback, useRef, useEffect, Fragment } from "react";

interface CodeBlockProps {
  code: string;
  language?: string;
  maxHeight?: string;
  showLineNumbers?: boolean;
  className?: string;
}

function CopyIcon() {
  return (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  );
}

function ExpandIcon() {
  return (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
    </svg>
  );
}

function CollapseIcon() {
  return (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
    </svg>
  );
}

type TokenType = "heading" | "bold" | "bullet" | "property" | "number" | "color" | "plain";

interface Token {
  type: TokenType;
  text: string;
}

function tokenizeLine(line: string): Token[] {
  const tokens: Token[] = [];

  if (line.match(/^#{1,6}\s/)) {
    return [{ type: "heading", text: line }];
  }

  if (line.match(/^[-*]\s/)) {
    tokens.push({ type: "bullet", text: "•" }, { type: "plain", text: " " + line.slice(2) });
    return tokens;
  }

  const propMatch = line.match(/^([A-Za-z][A-Za-z ]*?):\s/);
  if (propMatch) {
    const colonIndex = line.indexOf(":");
    tokens.push({ type: "property", text: line.slice(0, colonIndex) });
    tokens.push({ type: "plain", text: ":" });
    const remainder = line.slice(colonIndex + 1);
    tokens.push(...tokenizeInline(remainder));
    return tokens;
  }

  tokens.push(...tokenizeInline(line));
  return tokens;
}

function tokenizeInline(text: string): Token[] {
  const tokens: Token[] = [];
  let remaining = text;

  const patterns: [RegExp, TokenType][] = [
    [/\*\*(.+?)\*\*/g, "bold"],
    [/\b(\d+(?:px|rem|em|vh|vw|%|xl|lg|md|sm|xs)?)\b/g, "number"],
    [/\b(slate|zinc|stone|red|orange|amber|yellow|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(?:\d{2,3}|white|black)\b/g, "color"],
  ];

  while (remaining.length > 0) {
    let earliestMatch: RegExpMatchArray | null = null;
    let earliestType: TokenType = "plain";
    let earliestIndex = remaining.length;

    for (const [pattern, type] of patterns) {
      pattern.lastIndex = 0;
      const match = pattern.exec(remaining);
      if (match && match.index < earliestIndex) {
        earliestMatch = match;
        earliestType = type;
        earliestIndex = match.index;
      }
    }

    if (!earliestMatch) {
      if (remaining) tokens.push({ type: "plain", text: remaining });
      break;
    }

    if (earliestIndex > 0) {
      tokens.push({ type: "plain", text: remaining.slice(0, earliestIndex) });
    }

    if (earliestType === "bold") {
      tokens.push({ type: "bold", text: earliestMatch[1] });
    } else {
      tokens.push({ type: earliestType, text: earliestMatch[0] });
    }

    remaining = remaining.slice(earliestIndex + earliestMatch[0].length);
  }

  return tokens;
}

const TOKEN_STYLES: Record<TokenType, string> = {
  heading: "text-amber-400/90 font-semibold",
  bold: "text-emerald-400/90 font-semibold",
  bullet: "text-zinc-600",
  property: "text-sky-400/80",
  number: "text-orange-400/80",
  color: "text-violet-400/80",
  plain: "text-zinc-400",
};

function highlightLine(line: string, lineNum: number) {
  const tokens = tokenizeLine(line);
  return (
    <div key={lineNum} className="flex">
      <span className="w-10 flex-shrink-0 text-right pr-4 text-zinc-700 select-none text-[11px] leading-6">
        {lineNum + 1}
      </span>
      <span className="flex-1 text-[12px] leading-6">
        {tokens.map((token, i) => (
          <span key={i} className={TOKEN_STYLES[token.type]}>{token.text}</span>
        ))}
      </span>
    </div>
  );
}

export default function CodeBlock({
  code,
  language = "markdown",
  maxHeight = "60vh",
  showLineNumbers = true,
  className = "",
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [code]);

  const lines = code.split("\n");

  return (
    <div
      className={`group relative rounded-xl overflow-hidden border border-zinc-800/80 bg-[#0d0d0d] ${className}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#111111] border-b border-zinc-800/60">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]/80" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#febc2e]/80" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#28c840]/80" />
          </div>
          <span className="text-[10px] text-zinc-600 font-mono ml-2">{language}</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 rounded-md text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50 transition-all"
            title={expanded ? "Collapse" : "Expand"}
          >
            {expanded ? <CollapseIcon /> : <ExpandIcon />}
          </button>
          <button
            onClick={handleCopy}
            className={`p-1.5 rounded-md transition-all ${
              copied
                ? "text-emerald-400 bg-emerald-400/10"
                : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50"
            }`}
            title="Copy to clipboard"
          >
            {copied ? <CheckIcon /> : <CopyIcon />}
          </button>
        </div>
      </div>

      {/* Code content */}
      <div
        ref={containerRef}
        className="overflow-auto transition-all duration-300"
        style={{
          maxHeight: expanded ? "85vh" : maxHeight,
        }}
      >
        <div className="p-4 font-mono">
          {code.split("\n").map((line, i) => highlightLine(line, i))}
        </div>
      </div>

      {/* Expand overlay */}
      {!expanded && (
        <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-[#0d0d0d] to-transparent pointer-events-none" />
      )}

      {/* Line count */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#111111] border-t border-zinc-800/60">
        <span className="text-[10px] text-zinc-600 font-mono">{lines.length} lines</span>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-[10px] text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          {expanded ? "Show less" : `Show all ${lines.length} lines`}
        </button>
      </div>
    </div>
  );
}