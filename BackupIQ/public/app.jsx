const { useState, useEffect, useCallback, memo, useRef } = React;

// --- SVG Icons ---
const IconShieldCheck = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-8 w-8 text-indigo-400">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="m9 12 2 2 4-4"></path>
    </svg>
);
const IconBox = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-8 w-8 text-indigo-400">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line>
    </svg>
);
const IconActivity = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-8 w-8 text-indigo-400">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
    </svg>
);
const IconCode = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-8 w-8 text-indigo-400">
        <polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline>
    </svg>
);


// --- Pixel Blast Background Component ---
const PixelBlastBackground = memo(() => {
    const canvasRef = useRef(null);

    const draw = useCallback((ctx, w, h, columns, symbols, yPositions) => {
        ctx.fillStyle = "rgba(17, 24, 39, 0.1)";
        ctx.fillRect(0, 0, w, h);
        ctx.fillStyle = '#6366f1'; // Indigo color to match theme
        ctx.font = '15pt monospace';

        yPositions.forEach((y, i) => {
            const text = String.fromCharCode(symbols[i]);
            const x = i * 20;
            ctx.fillText(text, x, y);
            if (y > 100 + Math.random() * 10000) {
                yPositions[i] = 0;
            } else {
                yPositions[i] = y + 20;
            }
        });
    }, []);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const context = canvas.getContext('2d', { alpha: true });
        let animationFrameId;

        let w = (canvas.width = window.innerWidth);
        let h = (canvas.height = window.innerHeight);
        let columns = Math.floor(w / 20) + 1;
        const symbols = Array.from({ length: 128 }, (_, i) => 0x30a0 + i);
        let yPositions = Array(columns).fill(0);

        const render = () => {
            draw(context, w, h, columns, symbols, yPositions);
            animationFrameId = window.requestAnimationFrame(render);
        };
        render();

        const handleResize = () => {
            w = canvas.width = window.innerWidth;
            h = canvas.height = window.innerHeight;
            columns = Math.floor(w / 20) + 1;
            yPositions = Array(columns).fill(0);
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.cancelAnimationFrame(animationFrameId);
            window.removeEventListener('resize', handleResize);
        };
    }, [draw]);

    return <canvas ref={canvasRef} className="absolute top-0 left-0 w-full h-full -z-10" />;
});


// --- Main App Component ---
function App() {
    const features = [
        { icon: <IconCode />, title: "Core Backup Engine", description: "Handles scheduled backups, file/database snapshotting, and seamless restore workflows. Supports multiple storage backends like cloud, object storage, and DB dumps." },
        { icon: <IconBox />, title: "Enterprise-Ready Packaging", description: "Comes with a non-root, multi-stage Dockerfile, Kubernetes manifests, and health/metrics endpoints (/health, /ready, /metrics) for robust, scalable deployments." },
        { icon: <IconShieldCheck />, title: "Reliability & Security", description: "Engineered for graceful startups/shutdowns, with timeout/retry/backoff patterns. Secrets are externalized, designed for secure integration with managers like HashiCorp Vault." },
        { icon: <IconActivity />, title: "Observability & Testing", description: "Features structured JSON logging, a Prometheus metrics endpoint, and a full suite of unit, integration, and acceptance tests. Includes sample CI/CD workflows." }
    ];

    const targetAudience = [
        { name: "MSPs & IT Agencies", description: "Offer white-label backup services to your clients." },
        { name: "SaaS Founders & Indie Hackers", description: "Launch your backup solution instantly, skipping months of dev time." },
        { name: "Ecommerce App Developers", description: "Build Shopify/Shop apps for one-click data recovery." },
        { name: "Crypto & Web3 Teams", description: "Adapt backup flows for critical blockchain nodes and wallet states." },
    ];

    return (
        <div className="bg-gray-900 text-gray-200 font-sans leading-relaxed">
            <PixelBlastBackground />
            <div className="relative isolate min-h-screen flex flex-col items-center justify-center text-center overflow-hidden px-4">
                <div className="absolute inset-0 -z-10 bg-gray-900/50 backdrop-blur-sm"></div>
                <header className="z-10">
                    <h1 className="text-4xl sm:text-5xl md:text-7xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 pb-2">
                        BackupIQ
                    </h1>
                    <p className="mt-4 text-lg sm:text-xl md:text-2xl max-w-3xl mx-auto text-gray-300">
                        An AI-Enabled, Production-Ready Backup & Restore SaaS Platform.
                    </p>
                    <p className="mt-6 text-base max-w-2xl mx-auto text-gray-400">
                        Your turnkey system to eliminate data loss anxiety. Reduce build time from 12 months to under 48 hours.
                    </p>
                    <div className="mt-10 flex items-center justify-center gap-x-6">
                        <a href="#features" className="rounded-md bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 transition-colors duration-300">
                            Explore Features
                        </a>
                        <a href="#pitch" className="text-sm font-semibold leading-6 text-gray-300 hover:text-white">
                            Learn more <span aria-hidden="true">→</span>
                        </a>
                    </div>
                </header>
            </div>
            <main className="relative z-10 bg-gray-900">
                <section id="features" className="py-20 sm:py-28 px-6 lg:px-8">
                    <div className="max-w-7xl mx-auto">
                        <div className="text-center">
                            <h2 className="text-base font-semibold leading-7 text-indigo-400">Everything Included</h2>
                            <p className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">The Blueprint for Modern Data Resilience</p>
                            <p className="mt-6 text-lg leading-8 text-gray-400">
                                This isn't just a script. It's a complete, enterprise-grade system engineered for reliability and scale.
                            </p>
                        </div>
                        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-10">
                            {features.map((feature) => (
                                <div key={feature.title} className="relative pl-16">
                                    <dt className="text-base font-semibold leading-7 text-white">
                                        <div className="absolute left-0 top-0 flex h-12 w-12 items-center justify-center rounded-lg bg-gray-800 border border-gray-700">
                                            {feature.icon}
                                        </div>
                                        {feature.title}
                                    </dt>
                                    <dd className="mt-2 text-base leading-7 text-gray-400">{feature.description}</dd>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>
                <section className="bg-gray-900/50 py-20 sm:py-28">
                    <div className="max-w-7xl mx-auto px-6 lg:px-8 grid md:grid-cols-3 gap-12 text-center">
                        <div className="p-8 rounded-xl bg-gray-800/50 border border-gray-700">
                            <div className="text-4xl font-bold text-indigo-400">$100K+</div>
                            <div className="mt-2 text-gray-300">Replacement Cost</div>
                            <p className="mt-4 text-sm text-gray-400">The engineering effort and salary cost to replicate this system from scratch.</p>
                        </div>
                        <div className="p-8 rounded-xl bg-gray-800/50 border border-gray-700">
                            <div className="text-4xl font-bold text-indigo-400">&lt;48 Hours</div>
                            <div className="mt-2 text-gray-300">Time-to-Market</div>
                            <p className="mt-4 text-sm text-gray-400">Skip 6-12 months of development, debugging, and infrastructure setup. Launch now.</p>
                        </div>
                        <div className="p-8 rounded-xl bg-gray-800/50 border border-gray-700">
                            <div className="text-4xl font-bold text-indigo-400">4+ Verticals</div>
                            <div className="mt-2 text-gray-300">Market Versatility</div>
                            <p className="mt-4 text-sm text-gray-400">Adaptable for SaaS, Ecommerce, MSPs, Agencies, and emerging Web3 use cases.</p>
                        </div>
                    </div>
                </section>
                <section id="who-for" className="py-20 sm:py-28 px-6 lg:px-8">
                    <div className="max-w-5xl mx-auto text-center">
                        <h2 className="text-base font-semibold leading-7 text-indigo-400">Built for Builders</h2>
                        <p className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">Who Would Buy This?</p>
                        <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                            {targetAudience.map((audience) => (
                                <div key={audience.name} className="p-6 bg-gray-800/50 border border-gray-700 rounded-lg">
                                    <h3 className="font-semibold text-white">{audience.name}</h3>
                                    <p className="mt-2 text-sm text-gray-400">{audience.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>
                <section id="pitch" className="bg-gray-800 py-20 sm:py-28">
                    <div className="max-w-7xl mx-auto px-6 lg:px-8 grid md:grid-cols-2 gap-16 items-center">
                        <div>
                            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">How to Pitch It</h2>
                            <p className="mt-4 text-lg text-gray-400">This is how you frame the value.</p>
                             <div className="mt-8 p-6 border border-dashed border-gray-600 rounded-lg">
                                <p className="text-lg font-semibold text-indigo-400">“BackupIQ — AI-enabled backup & restore SaaS codebase. Deploy in &lt;48 hours.”</p>
                            </div>
                            <ul className="mt-8 space-y-4 text-gray-300">
                                <li className="flex items-start">
                                    <svg className="flex-shrink-0 h-6 w-6 text-indigo-400 mr-3 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
                                    <span><strong>Production-Ready:</strong> Docker, Kubernetes, CI/CD, health/metrics/tests.</span>
                                </li>
                                <li className="flex items-start">
                                    <svg className="flex-shrink-0 h-6 w-6 text-indigo-400 mr-3 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
                                    <span><strong>Saves $75K+ and 6–12 months</strong> of engineering and opportunity cost.</span>
                                </li>
                                <li className="flex items-start">
                                    <svg className="flex-shrink-0 h-6 w-6 text-indigo-400 mr-3 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
                                    <span><strong>Adaptable:</strong> Perfect for SaaS, Shopify apps, MSPs, or Web3 projects.</span>
                                </li>
                                 <li className="flex items-start">
                                    <svg className="flex-shrink-0 h-6 w-6 text-indigo-400 mr-3 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
                                    <span><strong>License Once, Deploy Forever.</strong> A true asset for your portfolio.</span>
                                </li>
                            </ul>
                        </div>
                        <div>
                            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Licensing vs. Selling</h2>
                            <p className="mt-4 text-lg text-gray-400">Two paths to monetization.</p>
                             <div className="mt-8 space-y-6">
                                <div className="p-6 rounded-lg bg-gray-700/50">
                                    <h3 className="font-semibold text-white">Non-Exclusive License (~$10K each)</h3>
                                    <p className="mt-2 text-sm text-gray-400">The smart move. Sell to multiple buyers, create recurring deals, and retain the upside. The ideal path for maximizing returns.</p>
                                </div>
                                <div className="p-6 rounded-lg bg-gray-700/50">
                                    <h3 className="font-semibold text-white">Outright Sale (~$10K–$30K)</h3>
                                    <p className="mt-2 text-sm text-gray-400">A quick cash injection, but you lose all future rights to the codebase. Best for a fast exit.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </main>
            <footer className="bg-gray-900 border-t border-gray-800">
                <div className="max-w-7xl mx-auto py-8 px-6 lg:px-8 text-center text-gray-500">
                     <p>&copy; {new Date().getFullYear()} BackupIQ. All rights reserved. A conceptual product.</p>
                </div>
            </footer>
        </div>
    );
}

const container = document.getElementById('root');
const root = ReactDOM.createRoot(container);
root.render(<App />);
