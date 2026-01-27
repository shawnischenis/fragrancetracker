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
    <main className="min-h-screen bg-black text-white relative overflow-hidden selection:bg-indigo-500/30">
      {/* Background Gradients */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-600/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/20 rounded-full blur-[120px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 gap-6"
        >
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="text-yellow-400 w-5 h-5" />
              <span className="text-sm font-medium text-zinc-400 uppercase tracking-widest">Fragrance Tracker</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-zinc-200 to-zinc-500">
              Market Intelligence
            </h1>
            <p className="mt-2 text-zinc-400 max-w-lg">
              Real-time price tracking and volatility analysis from Reddit's fragrance community.
            </p>
          </div>

          <div className="flex gap-4">
            <button
              onClick={handleOpenRareAlert}
              className="px-6 py-3 bg-zinc-900 border border-zinc-700 hover:border-zinc-500 hover:bg-zinc-800 rounded-xl transition-all flex items-center gap-2 shadow-xl"
            >
              <Activity className="w-4 h-4 text-pink-500" />
              <span className="font-medium text-sm">Track Rare Item</span>
            </button>
          </div>
        </motion.div>

        {/* Stats Grid could go here */}

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
