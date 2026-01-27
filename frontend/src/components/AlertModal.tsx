import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Bell, Zap } from 'lucide-react';
import axios from 'axios';

interface Fragrance {
    reddit_name: string;
    brand?: string;
    weighted_avg_price?: number;
    weighted_std_dev?: number;
}

interface AlertModalProps {
    isOpen: boolean;
    onClose: () => void;
    fragrance?: Fragrance | null;
}

export const AlertModal: React.FC<AlertModalProps> = ({ isOpen, onClose, fragrance }) => {
    const [email, setEmail] = useState('');
    const [thresholdSigma, setThresholdSigma] = useState(0.5);
    const [fragranceName, setFragranceName] = useState('');
    const [mode, setMode] = useState<'DEAL' | 'RARE'>('DEAL');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    // Initial state setup when modal opens
    React.useEffect(() => {
        if (fragrance) {
            setMode('DEAL');
            setFragranceName(fragrance.reddit_name);
        } else {
            setMode('RARE');
            setFragranceName('');
        }
        setSuccess(false);
    }, [fragrance, isOpen]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await axios.post('http://localhost:8000/api/alerts', {
                email,
                type: mode,
                target_name: fragranceName,
                threshold: mode === 'DEAL' ? thresholdSigma : undefined
            });
            setSuccess(true);
            setTimeout(() => {
                onClose();
            }, 1500);
        } catch (error) {
            console.error(error);
            alert("Failed to create alert");
        } finally {
            setLoading(false);
        }
    };

    const targetPrice = fragrance && fragrance.weighted_avg_price && fragrance.weighted_std_dev
        ? (fragrance.weighted_avg_price - (thresholdSigma * fragrance.weighted_std_dev)).toFixed(2)
        : "N/A";

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="w-full max-w-md overflow-hidden rounded-2xl bg-zinc-900 border border-zinc-800 shadow-2xl"
                    >
                        <div className="p-6">
                            <div className="flex justify-between items-center mb-6">
                                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                    <Bell className="w-5 h-5 text-indigo-400" />
                                    {mode === 'DEAL' ? 'Deal Alert' : 'Rare Find Alert'}
                                </h2>
                                <button onClick={onClose} className="text-zinc-400 hover:text-white transition-colors">
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {success ? (
                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="text-center py-8 text-green-400 font-medium"
                                >
                                    Alert Created Successfully!
                                </motion.div>
                            ) : (
                                <form onSubmit={handleSubmit} className="space-y-4">
                                    {!fragrance && (
                                        <div className="flex gap-2 mb-4 p-1 bg-zinc-800 rounded-lg">
                                            <button
                                                type="button"
                                                onClick={() => setMode('DEAL')}
                                                className={`flex-1 py-1 text-sm rounded-md transition-all ${mode === 'DEAL' ? 'bg-indigo-600 text-white shadow-lg' : 'text-zinc-400 hover:text-white'}`}
                                            >
                                                Deal Alert
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setMode('RARE')}
                                                className={`flex-1 py-1 text-sm rounded-md transition-all ${mode === 'RARE' ? 'bg-pink-600 text-white shadow-lg' : 'text-zinc-400 hover:text-white'}`}
                                            >
                                                Rare Find
                                            </button>
                                        </div>
                                    )}

                                    <div>
                                        <label className="block text-sm font-medium text-zinc-400 mb-1">Fragrance Name</label>
                                        <input
                                            type="text"
                                            value={fragranceName}
                                            onChange={(e) => setFragranceName(e.target.value)}
                                            disabled={!!fragrance}
                                            required
                                            className="w-full bg-zinc-800 border-zinc-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-indigo-500 outline-none disabled:opacity-50"
                                            placeholder="e.g. Aventus"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-zinc-400 mb-1">Email Address</label>
                                        <input
                                            type="email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            required
                                            className="w-full bg-zinc-800 border-zinc-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                                            placeholder="you@example.com"
                                        />
                                    </div>

                                    {mode === 'DEAL' && fragrance && (
                                        <div className="bg-zinc-800/50 p-4 rounded-lg border border-zinc-700/50">
                                            <div className="flex justify-between text-sm text-zinc-300 mb-2">
                                                <span>Alert Threshold</span>
                                                <span className="font-mono text-indigo-400">{thresholdSigma}σ below avg</span>
                                            </div>
                                            <input
                                                type="range"
                                                min="0.1"
                                                max="3.0"
                                                step="0.1"
                                                value={thresholdSigma}
                                                onChange={(e) => setThresholdSigma(parseFloat(e.target.value))}
                                                className="w-full h-2 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                                            />
                                            <div className="mt-3 flex justify-between items-center text-xs">
                                                <span className="text-zinc-500">Normal Price: ${fragrance.weighted_avg_price?.toFixed(2)}</span>
                                                <span className="flex items-center gap-1 text-green-400 font-bold">
                                                    Target: ${targetPrice} <Zap className="w-3 h-3" />
                                                </span>
                                            </div>
                                        </div>
                                    )}

                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-medium py-2 rounded-lg transition-all shadow-lg shadow-indigo-500/20 disabled:opacity-50"
                                    >
                                        {loading ? 'Creating...' : 'Create Alert'}
                                    </button>
                                </form>
                            )}
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
};
