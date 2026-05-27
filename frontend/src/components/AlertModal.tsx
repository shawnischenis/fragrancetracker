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
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/20 backdrop-blur-sm">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-2xl border border-stone-100"
                    >
                        <div className="p-8">
                            <div className="flex justify-between items-center mb-8">
                                <h2 className="text-xl font-serif font-medium text-stone-800 flex items-center gap-2">
                                    <Bell className="w-5 h-5 text-stone-400" />
                                    {mode === 'DEAL' ? 'Set Price Alert' : 'Hunt for Rare Item'}
                                </h2>
                                <button onClick={onClose} className="text-stone-400 hover:text-stone-600 transition-colors">
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {success ? (
                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="text-center py-12"
                                >
                                    <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <Bell className="w-6 h-6" />
                                    </div>
                                    <p className="text-stone-800 font-medium text-lg">Alert Active</p>
                                    <p className="text-stone-500 text-sm mt-1">We&apos;ll verify {mode === 'DEAL' ? 'pricing' : 'availability'} hourly.</p>
                                </motion.div>
                            ) : (
                                <form onSubmit={handleSubmit} className="space-y-6">
                                    {!fragrance && (
                                        <div className="flex bg-stone-100 p-1 rounded-lg">
                                            <button
                                                type="button"
                                                onClick={() => setMode('DEAL')}
                                                className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-all ${mode === 'DEAL' ? 'bg-white text-stone-800 shadow-sm' : 'text-stone-500 hover:text-stone-700'}`}
                                            >
                                                Deal
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setMode('RARE')}
                                                className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-all ${mode === 'RARE' ? 'bg-white text-stone-800 shadow-sm' : 'text-stone-500 hover:text-stone-700'}`}
                                            >
                                                Rare
                                            </button>
                                        </div>
                                    )}

                                    <div>
                                        <label className="block text-xs font-bold text-stone-400 uppercase tracking-wider mb-2">Target Fragrance</label>
                                        <input
                                            type="text"
                                            value={fragranceName}
                                            onChange={(e) => setFragranceName(e.target.value)}
                                            disabled={!!fragrance}
                                            required
                                            className="w-full bg-stone-50 border-stone-200 border rounded-xl px-4 py-3 text-stone-800 focus:ring-2 focus:ring-stone-200 focus:border-stone-300 outline-none transition-all disabled:opacity-60 disabled:bg-white"
                                            placeholder="e.g. Aventus"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-xs font-bold text-stone-400 uppercase tracking-wider mb-2">Notification Email</label>
                                        <input
                                            type="email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            required
                                            className="w-full bg-stone-50 border-stone-200 border rounded-xl px-4 py-3 text-stone-800 focus:ring-2 focus:ring-stone-200 focus:border-stone-300 outline-none transition-all"
                                            placeholder="you@example.com"
                                        />
                                    </div>

                                    {mode === 'DEAL' && fragrance && (
                                        <div className="bg-stone-50 p-5 rounded-xl border border-stone-100">
                                            <div className="flex justify-between text-sm text-stone-600 mb-4">
                                                <span>Aggressiveness</span>
                                                <span className="font-semibold text-stone-900">{thresholdSigma}σ deviation</span>
                                            </div>
                                            <input
                                                type="range"
                                                min="0.1"
                                                max="3.0"
                                                step="0.1"
                                                value={thresholdSigma}
                                                onChange={(e) => setThresholdSigma(parseFloat(e.target.value))}
                                                className="w-full h-1.5 bg-stone-200 rounded-lg appearance-none cursor-pointer accent-stone-800"
                                            />
                                            <div className="mt-4 flex justify-between items-center text-xs">
                                                <span className="text-stone-400">Market Avg: ${fragrance.weighted_avg_price?.toFixed(0)}</span>
                                                <span className="flex items-center gap-1 text-emerald-600 font-bold bg-emerald-50 px-2 py-1 rounded">
                                                    Target: ${targetPrice} <Zap className="w-3 h-3" />
                                                </span>
                                            </div>
                                        </div>
                                    )}

                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="w-full bg-stone-900 hover:bg-stone-800 text-white font-medium py-3.5 rounded-xl transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5 disabled:opacity-70 disabled:translate-y-0 disabled:shadow-none"
                                    >
                                        {loading ? 'Activating...' : 'Activate Alert'}
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
