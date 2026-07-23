"use client";

import { useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import type { TradeScene } from "@/lib/immersive";
import { SCENE_LABEL } from "@/lib/immersive";

gsap.registerPlugin(ScrollTrigger, useGSAP);

interface TradeInstrumentProps {
  scene: TradeScene;
  progress?: number; // 0–1 visual state
  className?: string;
  light?: boolean;
}

/**
 * Semantic SVG instruments — communicate real trade work, never decorative blobs.
 * Progress drives stroke reveal / dial / wipe via CSS custom property.
 */
export default function TradeInstrument({
  scene,
  progress = 0.72,
  className = "",
  light = false,
}: TradeInstrumentProps) {
  const root = useRef<HTMLDivElement>(null);
  const stroke = light ? "var(--trade-ink)" : "var(--trade-accent)";
  const muted = light
    ? "color-mix(in oklab, var(--trade-ink) 28%, transparent)"
    : "color-mix(in oklab, var(--trade-accent) 28%, transparent)";
  const fill = light
    ? "color-mix(in oklab, var(--trade-accent) 18%, transparent)"
    : "color-mix(in oklab, var(--trade-accent) 14%, transparent)";

  const p = Math.max(0, Math.min(1, progress));
  const dash = 420;
  const offset = dash * (1 - p);

  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const paths = root.current?.querySelectorAll(".instrument-path");
      if (!paths?.length) return;
      gsap.fromTo(
        paths,
        { strokeDashoffset: dash },
        {
          strokeDashoffset: offset,
          duration: 1.4,
          ease: "power2.out",
          stagger: 0.08,
          scrollTrigger: {
            trigger: root.current,
            start: "top 80%",
            once: true,
          },
        },
      );
    },
    { scope: root, dependencies: [offset, scene] },
  );

  return (
    <div
      ref={root}
      className={`instrument-stage relative aspect-[4/3] w-full max-w-xl ${className}`}
      data-scene={scene}
      style={{ ["--instrument-p" as string]: String(p) }}
      role="img"
      aria-label={SCENE_LABEL[scene]}
    >
      <svg
        viewBox="0 0 400 300"
        className="instrument-svg h-full w-full"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Shared frame */}
        <rect
          x="12"
          y="12"
          width="376"
          height="276"
          rx="4"
          stroke={muted}
          strokeWidth="1"
        />
        <text
          x="28"
          y="36"
          fill={stroke}
          fontSize="10"
          fontFamily="var(--font-sans), system-ui, sans-serif"
          letterSpacing="2"
          opacity="0.7"
        >
          {SCENE_LABEL[scene].toUpperCase()}
        </text>

        {scene === "thermal-airflow" && (
          <>
            <path
              d="M48 210 H120 V90 H200 V210 H280 V120 H352"
              stroke={muted}
              strokeWidth="10"
              strokeLinecap="square"
            />
            <path
              d="M48 210 H120 V90 H200 V210 H280 V120 H352"
              stroke={stroke}
              strokeWidth="3"
              strokeLinecap="square"
              strokeDasharray={dash}
              strokeDashoffset={offset}
              className="instrument-path"
            />
            <circle cx="120" cy="90" r="14" fill={fill} stroke={stroke} strokeWidth="1.5" />
            <circle cx="200" cy="210" r="14" fill={fill} stroke={stroke} strokeWidth="1.5" />
            <circle cx="280" cy="120" r="14" fill={fill} stroke={stroke} strokeWidth="1.5" />
            <text x="100" y="72" fill={stroke} fontSize="9" opacity="0.8">
              FILTER
            </text>
            <text x="178" y="242" fill={stroke} fontSize="9" opacity="0.8">
              COIL
            </text>
            <text x="258" y="102" fill={stroke} fontSize="9" opacity="0.8">
              SUPPLY
            </text>
            {/* Temperature dial */}
            <circle cx="330" cy="230" r="36" stroke={muted} strokeWidth="6" />
            <circle
              cx="330"
              cy="230"
              r="36"
              stroke={stroke}
              strokeWidth="6"
              strokeDasharray={`${Math.PI * 2 * 36 * (0.35 + p * 0.45)} ${Math.PI * 2 * 36}`}
              strokeLinecap="round"
              transform="rotate(-120 330 230)"
            />
            <text
              x="330"
              y="234"
              textAnchor="middle"
              fill={stroke}
              fontSize="14"
              fontFamily="var(--font-display), Georgia, serif"
            >
              {Math.round(68 + p * 10)}°
            </text>
          </>
        )}

        {scene === "pressure-flow" && (
          <>
            <path
              d="M40 80 H160 Q200 80 200 120 V180 Q200 220 240 220 H360"
              stroke={muted}
              strokeWidth="14"
              strokeLinecap="round"
            />
            <path
              d="M40 80 H160 Q200 80 200 120 V180 Q200 220 240 220 H360"
              stroke={stroke}
              strokeWidth="3"
              strokeDasharray={dash}
              strokeDashoffset={offset}
              className="instrument-path"
            />
            <rect x="150" y="62" width="28" height="36" rx="2" fill={fill} stroke={stroke} />
            <text x="148" y="52" fill={stroke} fontSize="9">
              VALVE
            </text>
            <path
              d="M300 160 A40 40 0 1 1 300 240"
              stroke={muted}
              strokeWidth="8"
              strokeLinecap="round"
            />
            <path
              d="M300 160 A40 40 0 1 1 300 240"
              stroke={stroke}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${80 * p} 200`}
            />
            <text x="286" y="206" fill={stroke} fontSize="11" fontFamily="var(--font-display), Georgia, serif">
              PSI
            </text>
          </>
        )}

        {scene === "circuit-load" && (
          <>
            <rect x="48" y="60" width="70" height="180" rx="3" stroke={muted} strokeWidth="2" />
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <rect
                key={i}
                x="58"
                y={74 + i * 26}
                width="50"
                height="14"
                rx="1"
                fill={i / 5 <= p ? fill : "transparent"}
                stroke={stroke}
                strokeWidth="1"
                opacity={i / 5 <= p ? 1 : 0.35}
              />
            ))}
            <text x="58" y="52" fill={stroke} fontSize="9">
              PANEL
            </text>
            <path
              d="M118 88 H180 V140 H260 V88 H340"
              stroke={stroke}
              strokeWidth="2"
              strokeDasharray={dash}
              strokeDashoffset={offset}
            />
            <path d="M118 140 H180" stroke={muted} strokeWidth="2" />
            <path d="M118 192 H220 V240 H320" stroke={muted} strokeWidth="2" />
            <circle cx="340" cy="88" r="8" fill={fill} stroke={stroke} />
            <circle cx="260" cy="140" r="8" fill={fill} stroke={stroke} />
            <circle cx="320" cy="240" r="8" fill={fill} stroke={stroke} />
            <text x="300" y="76" fill={stroke} fontSize="9">
              LOAD
            </text>
          </>
        )}

        {scene === "roof-assembly" && (
          <>
            <path d="M40 200 L200 60 L360 200" stroke={muted} strokeWidth="2" />
            <path
              d="M40 200 L200 60 L360 200"
              stroke={stroke}
              strokeWidth="2.5"
              strokeDasharray="380"
              strokeDashoffset={380 * (1 - p)}
            />
            <path d="M70 200 H330 V240 H70 Z" fill={fill} stroke={stroke} strokeWidth="1.5" />
            <line x1="70" y1="180" x2="330" y2="180" stroke={muted} strokeWidth="1" />
            <line x1="90" y1="160" x2="310" y2="160" stroke={muted} strokeWidth="1" />
            <line
              x1="110"
              y1={140 - p * 20}
              x2="290"
              y2={140 - p * 20}
              stroke={stroke}
              strokeWidth="1.5"
            />
            <text x="160" y="268" fill={stroke} fontSize="9" letterSpacing="1.5">
              UNDERLAY · DECK · SHINGLE
            </text>
          </>
        )}

        {scene === "finish-wipe" && (
          <>
            <rect x="48" y="56" width="304" height="188" rx="2" stroke={muted} strokeWidth="1.5" />
            <defs>
              <clipPath id="wipe">
                <rect x="48" y="56" width={304 * p} height="188" />
              </clipPath>
            </defs>
            <rect
              x="48"
              y="56"
              width="304"
              height="188"
              fill={fill}
              clipPath="url(#wipe)"
            />
            <line
              x1={48 + 304 * p}
              y1="56"
              x2={48 + 304 * p}
              y2="244"
              stroke={stroke}
              strokeWidth="2"
            />
            <text x="60" y="48" fill={stroke} fontSize="9">
              PREP
            </text>
            <text x="170" y="48" fill={stroke} fontSize="9">
              PRIME
            </text>
            <text x="290" y="48" fill={stroke} fontSize="9">
              FINISH
            </text>
            <text
              x="200"
              y="160"
              textAnchor="middle"
              fill={stroke}
              fontSize="22"
              fontFamily="var(--font-display), Georgia, serif"
              opacity={0.35 + p * 0.5}
            >
              {Math.round(p * 100)}%
            </text>
          </>
        )}

        {scene === "site-plan" && (
          <>
            <rect x="40" y="50" width="320" height="200" rx="2" stroke={muted} strokeWidth="1.5" />
            <rect
              x="60"
              y="70"
              width={100 + p * 40}
              height="80"
              fill={fill}
              stroke={stroke}
              strokeWidth="1.5"
            />
            <path
              d="M180 200 C220 160, 260 220, 320 170"
              stroke={stroke}
              strokeWidth="2"
              strokeDasharray={dash}
              strokeDashoffset={offset}
            />
            <circle cx="100" cy="200" r="18" fill={fill} stroke={stroke} />
            <circle cx="250" cy="100" r="12" fill={fill} stroke={stroke} />
            <rect x="280" y="180" width="60" height="40" stroke={stroke} strokeWidth="1.5" fill="transparent" />
            <text x="68" y="64" fill={stroke} fontSize="9">
              LAWN
            </text>
            <text x="288" y="174" fill={stroke} fontSize="9">
              HARDSCAPE
            </text>
            <text x="88" y="206" fill={stroke} fontSize="8" textAnchor="middle">
              TREE
            </text>
          </>
        )}
      </svg>
    </div>
  );
}
