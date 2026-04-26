"use client";

import { useState, useEffect, type ReactNode } from "react";

type Device = "desktop" | "tablet" | "mobile";

interface DeviceFrameProps {
  device: Device;
  children: ReactNode;
  url?: string;
  className?: string;
}

const DEVICE_CONFIG: Record<Device, {
  width: number;
  height: number;
  frameColor: string;
  screenRadius: string;
  hasNotch: boolean;
  hasHomeButton: boolean;
  statusBarHeight: number;
  bezel: number;
}> = {
  desktop: {
    width: 1440,
    height: 900,
    frameColor: "#1a1a1a",
    screenRadius: "0px",
    hasNotch: false,
    hasHomeButton: false,
    statusBarHeight: 0,
    bezel: 0,
  },
  tablet: {
    width: 768,
    height: 1024,
    frameColor: "#2a2a2a",
    screenRadius: "12px",
    hasNotch: false,
    hasHomeButton: true,
    statusBarHeight: 20,
    bezel: 8,
  },
  mobile: {
    width: 375,
    height: 812,
    frameColor: "#1a1a1a",
    screenRadius: "40px",
    hasNotch: true,
    hasHomeButton: false,
    statusBarHeight: 44,
    bezel: 12,
  },
};

function DesktopChrome({ url }: { url?: string }) {
  return (
    <div className="flex items-center h-9 px-3 bg-[#1e1e1e] border-b border-[#2a2a2a]">
      <div className="flex items-center gap-1.5 mr-4">
        <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
        <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
        <div className="w-3 h-3 rounded-full bg-[#28c840]" />
      </div>
      <div className="flex-1 flex items-center justify-center">
        <div className="flex items-center gap-2 px-4 py-1 bg-[#2a2a2a] rounded-md max-w-md w-full">
          <svg className="w-3 h-3 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <span className="text-[11px] text-zinc-400 font-mono truncate">{url || "localhost:3000"}</span>
        </div>
      </div>
      <div className="w-16" />
    </div>
  );
}

function TabletChrome({ url }: { url?: string }) {
  return (
    <div className="flex items-center justify-center h-5 bg-[#1a1a1a]">
      <span className="text-[9px] text-zinc-600 font-mono">{url || "localhost:3000"}</span>
    </div>
  );
}

function MobileStatusBar() {
  return (
    <div className="flex items-center justify-between px-6 pt-3 pb-1 bg-black">
      <span className="text-[11px] text-white font-semibold">9:41</span>
      <div className="flex items-center gap-1">
        <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 24 24">
          <path d="M1 9l2 2c4.97-4.97 13.03-4.97 18 0l2-2C16.93 2.93 7.08 2.93 1 9zm8 8l3 3 3-3c-1.65-1.66-4.34-1.66-6 0zm-4-4l2 2c2.76-2.76 7.24-2.76 10 0l2-2C15.14 9.14 8.87 9.14 5 13z" />
        </svg>
        <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 24 24">
          <path d="M15.67 4H14V2h-4v2H8.33C7.6 4 7 4.6 7 5.33v15.33C7 21.4 7.6 22 8.33 22h7.33c.74 0 1.34-.6 1.34-1.33V5.33C17 4.6 16.4 4 15.67 4z" />
        </svg>
      </div>
    </div>
  );
}

function MobileHomeIndicator() {
  return (
    <div className="flex justify-center pb-2 pt-1 bg-black">
      <div className="w-32 h-1 bg-zinc-600 rounded-full" />
    </div>
  );
}

export default function DeviceFrame({ device, children, url, className = "" }: DeviceFrameProps) {
  const config = DEVICE_CONFIG[device];
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [prevDevice, setPrevDevice] = useState(device);

  useEffect(() => {
    if (device !== prevDevice) {
      setIsTransitioning(true);
      const timer = setTimeout(() => {
        setIsTransitioning(false);
        setPrevDevice(device);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [device, prevDevice]);

  if (device === "desktop") {
    return (
      <div className={`flex flex-col h-full ${className}`}>
        <DesktopChrome url={url} />
        <div className="flex-1 overflow-hidden bg-white">
          {children}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex items-center justify-center h-full p-8 ${className}`}>
      <div
        className="relative transition-all duration-500 ease-out"
        style={{
          width: device === "mobile" ? 375 : 768,
          height: device === "mobile" ? 812 : 1024,
          maxHeight: "90vh",
        }}
      >
        {/* Device frame */}
        <div
          className="absolute inset-0 rounded-[44px] transition-all duration-500"
          style={{
            backgroundColor: config.frameColor,
            boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05)",
          }}
        >
          {/* Screen */}
          <div
            className="absolute overflow-hidden transition-all duration-500"
            style={{
              top: config.bezel,
              left: config.bezel,
              right: config.bezel,
              bottom: config.bezel,
              borderRadius: device === "mobile" ? "32px" : "8px",
            }}
          >
            {/* Notch (mobile only) */}
            {device === "mobile" && (
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-36 h-7 bg-black rounded-b-2xl z-20" />
            )}

            {/* Content */}
            <div className="h-full flex flex-col bg-white">
              {device === "mobile" ? <MobileStatusBar /> : <TabletChrome url={url} />}
              <div className="flex-1 overflow-hidden">
                {children}
              </div>
              {device === "mobile" && <MobileHomeIndicator />}
            </div>
          </div>
        </div>

        {/* Reflection effect */}
        <div
          className="absolute inset-0 rounded-[44px] pointer-events-none transition-opacity duration-500"
          style={{
            background: "linear-gradient(135deg, rgba(255,255,255,0.03) 0%, transparent 50%)",
            opacity: isTransitioning ? 0 : 1,
          }}
        />
      </div>
    </div>
  );
}