"use client";

import { useState } from 'react';
import { FragranceTable } from '../components/FragranceTable';
import { AlertModal } from '../components/AlertModal';
import { Sparkles, Activity } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Home() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedFragrance, setSelectedFragrance] = useState<any>(null);

  const handleOpenAlert = (fragrance: any) => {
    setSelectedFragrance(fragrance);
    setIsModalOpen(true);
  };

  const handleOpenRareAlert = () => {
    setSelectedFragrance(null);
    setIsModalOpen(true);
  };

  return (
    <main className="min-h-screen bg-[#FDFCF8] text-stone-800 relative selection:bg-rose-200 selection:text-rose-900 font-sans">

      <div className="relative z-10 max-w-6xl mx-auto px-6 py-16">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center text-center mb-16 gap-6"
        >
          <div className="flex items-center gap-3 px-4 py-1.5 bg-white border border-stone-200 rounded-full shadow-sm">
            <Sparkles className="text-stone-400 w-4 h-4" />
            <span className="text-xs font-semibold text-stone-500 uppercase tracking-[0.2em]">Market Intelligence</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-serif font-light text-stone-900 tracking-tight">
            The Scent <span className="italic font-normal text-stone-500">Index</span>
          </h1>

          <p className="mt-4 text-stone-500 max-w-lg text-lg leading-relaxed font-light">
            Curated price tracking from the enthusiast community. Discover deals, analyze volatility, and secure your signature scent.
          </p>

          <div className="flex gap-4 mt-4">
            <button
              onClick={handleOpenRareAlert}
              className="px-8 py-3 bg-stone-900 text-white hover:bg-stone-800 rounded-full transition-all flex items-center gap-2 shadow-lg hover:shadow-xl hover:-translate-y-0.5"
            >
              <Activity className="w-4 h-4 text-emerald-300" />
              <span className="font-medium">Track Rare Item</span>
            </button>
          </div>
        </motion.div>

        {/* Main Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <FragranceTable onOpenAlert={handleOpenAlert} />
        </motion.div>
      </div>

      <AlertModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        fragrance={selectedFragrance}
      />
    </main>
  );
}
