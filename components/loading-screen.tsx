"use client";

import React, { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";
import { sdgColors } from "@/lib/sdg-colors";
import { motion, AnimatePresence } from "framer-motion";

// Client-only component for SVG paths to avoid hydration errors
const SdgColorRing = () => {
  return (
    <svg width="140" height="140" viewBox="0 0 140 140" className="drop-shadow-lg">
      {sdgColors.map((color, i) => {
        const startAngle = (i / 17) * 360;
        const endAngle = ((i + 1) / 17) * 360;
        const largeArc = endAngle - startAngle > 180 ? 1 : 0;
        const polarToCartesian = (cx: number, cy: number, r: number, angle: number) => {
          const a = (angle - 90) * (Math.PI / 180);
          return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
        };
        const r = 65;
        const start = polarToCartesian(70, 70, r, startAngle);
        const end = polarToCartesian(70, 70, r, endAngle);
        const d = [
          "M", start.x, start.y,
          "A", r, r, 0, largeArc, 1, end.x, end.y
        ].join(" ");
        return (
          <path key={i} d={d} stroke={color} strokeWidth={12} fill="none" strokeLinecap="round" />
        );
      })}
    </svg>
  );
};

const SDG_QUOTES = [
  "End poverty in all its forms everywhere.",
  "Zero Hunger: End hunger, achieve food security and improved nutrition.",
  "Ensure healthy lives and promote well-being for all at all ages.",
  "Ensure inclusive and equitable quality education.",
  "Achieve gender equality and empower all women and girls.",
  "Ensure availability and sustainable management of water and sanitation.",
  "Ensure access to affordable, reliable, sustainable and modern energy.",
  "Promote sustained, inclusive and sustainable economic growth.",
  "Build resilient infrastructure, promote inclusive and sustainable industrialization.",
  "Reduce inequality within and among countries.",
  "Make cities and human settlements inclusive, safe, resilient and sustainable.",
  "Ensure sustainable consumption and production patterns.",
  "Take urgent action to combat climate change and its impacts.",
  "Conserve and sustainably use the oceans, seas and marine resources.",
  "Protect, restore and promote sustainable use of terrestrial ecosystems.",
  "Promote peaceful and inclusive societies for sustainable development.",
  "Strengthen the means of implementation and revitalize the global partnership."
];

interface LoadingScreenProps {
  message?: string;
  minDisplayTime?: number;
}

export function ImprovedLoadingScreen({ message = "Loading project data...", minDisplayTime = 2200 }: LoadingScreenProps) {
  const [quoteIdx, setQuoteIdx] = useState(0);
  const [isVisible, setIsVisible] = useState(true);
  const [isClient, setIsClient] = useState(false);
  
  // Only run on client-side
  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      // Select a random quote index
      const randomIndex = Math.floor(Math.random() * SDG_QUOTES.length);
      setQuoteIdx(randomIndex);
    }, 1500);

    const minDisplayTimeout = setTimeout(() => {
      setIsVisible(false);
    }, minDisplayTime);

    return () => {
      clearInterval(interval);
      clearTimeout(minDisplayTimeout);
    };
  }, [minDisplayTime]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col items-center justify-center min-h-screen p-8 bg-white rounded-2xl shadow-2xl"
        >
          <div className="flex flex-col items-center space-y-10">
            <motion.div
              className="relative mb-8"
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 30, ease: "linear" }}
            >
              {isClient ? <SdgColorRing /> : (
                // Placeholder for server rendering
              <div className="w-[140px] h-[140px] rounded-full bg-slate-100"></div>
              )}
              <div className="absolute top-0 left-0 w-full h-full flex items-center justify-center pointer-events-none">
                <Loader2 className="h-16 w-16 text-slate-700 animate-spin mt-10" />
              </div>

            </motion.div>
            <p> </p>
            <h3 className="text-3xl font-extrabold text-slate-800 mb-4 mt-10 animate-pulse">
              {message}
            </h3>

            <p className="text-lg text-gray-600 text-center max-w-md mb-6">
              We’re retrieving the latest UNOPS Remote Sensing project data. This may take a moment.
            </p>

            <motion.div className="mt-4 px-6 py-3 rounded-2xl bg-gradient-to-r from-slate-100 via-slate-50 to-slate-100 shadow-md" animate={{ opacity: [0.6, 1, 0.6] }} transition={{ repeat: Infinity, duration: 4 }}>
              <span className="block text-lg font-semibold text-center" style={{ color: sdgColors[quoteIdx] }}>
                {SDG_QUOTES[quoteIdx]}
              </span>
            </motion.div>
            <div className="mt-6 flex flex-wrap gap-3 justify-center">
              {sdgColors.map((color, idx) => (
                <span
                  key={idx}
                  className="inline-block w-6 h-6 rounded-full shadow-lg"
                  style={{ backgroundColor: color, border: '2px solid #fff' }}
                  title={`SDG ${idx + 1}`}
                ></span>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
