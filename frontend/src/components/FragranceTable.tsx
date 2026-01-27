import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Search, ArrowUpDown, BellPlus, Tag } from 'lucide-react';

interface Fragrance {
    reddit_name: string;
    brand?: string;
    weighted_avg_price?: number;
    weighted_std_dev?: number;
    listing_count?: number;
    jomashop_price?: number;
    weighted_price_diff?: number;
}

interface FragranceTableProps {
    onOpenAlert: (fragrance: Fragrance) => void;
}

export const FragranceTable: React.FC<FragranceTableProps> = ({ onOpenAlert }) => {
    const [fragrances, setFragrances] = useState<Fragrance[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/fragrances');
            setFragrances(response.data);
        } catch (error) {
            console.error("Error fetching fragrances:", error);
        } finally {
            setLoading(false);
        }
    };

    const filteredFragrances = fragrances.filter(f =>
        f.reddit_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (f.brand && f.brand.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    return (
        <div className="w-full space-y-4">
            {/* Search Bar */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 w-5 h-5" />
                <input
                    type="text"
                    placeholder="Search fragrances, brands..."
                    className="w-full pl-10 pr-4 py-3 bg-zinc-900/50 border border-zinc-800 rounded-xl text-white placeholder-zinc-500 focus:ring-2 focus:ring-indigo-500 outline-none backdrop-blur-sm transition-all"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
            </div>

            {/* Table */}
            <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/30 backdrop-blur-md">
                <table className="w-full text-left text-sm text-zinc-400">
                    <thead className="bg-zinc-900/80 text-zinc-200 uppercase tracking-wider text-xs">
                        <tr>
                            <th className="px-6 py-4 font-semibold">Fragrance</th>
                            <th className="px-6 py-4 font-semibold">Market Price</th>
                            <th className="px-6 py-4 font-semibold">Volatility</th>
                            <th className="px-6 py-4 font-semibold">Jomashop</th>
                            <th className="px-6 py-4 font-semibold text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800/50">
                        {loading ? (
                            <tr><td colSpan={5} className="px-6 py-8 text-center">Loading data...</td></tr>
                        ) : filteredFragrances.map((fragrance, idx) => (
                            <motion.tr
                                key={idx}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.05 }}
                                className="group hover:bg-zinc-800/30 transition-colors"
                            >
                                <td className="px-6 py-4">
                                    <div className="flex flex-col">
                                        <span className="font-medium text-white text-base">{fragrance.reddit_name}</span>
                                        <span className="text-xs text-zinc-500">{fragrance.brand}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="text-white font-mono">${fragrance.weighted_avg_price?.toFixed(2)}</span>
                                    <span className="text-xs text-zinc-500 ml-2">({fragrance.listing_count} listings)</span>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-16 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-indigo-500 rounded-full"
                                                style={{ width: `${Math.min(((fragrance.weighted_std_dev || 0) / (fragrance.weighted_avg_price || 1)) * 500, 100)}%` }}
                                            />
                                        </div>
                                        <span className="text-xs">±${fragrance.weighted_std_dev?.toFixed(2)}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    {fragrance.jomashop_price ? (
                                        <div className="flex flex-col">
                                            <span className="font-mono">${fragrance.jomashop_price.toFixed(2)}</span>
                                            {fragrance.weighted_price_diff && (
                                                <span className={`text-xs font-bold ${fragrance.weighted_price_diff < 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                    {fragrance.weighted_price_diff < 0 ? 'Deals found!' : 'Retail cheaper'}
                                                </span>
                                            )}
                                        </div>
                                    ) : <span className="text-zinc-600">-</span>}
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <button
                                        onClick={() => onOpenAlert(fragrance)}
                                        className="inline-flex items-center gap-2 px-3 py-1.5 bg-indigo-500/10 text-indigo-400 rounded-lg hover:bg-indigo-500 hover:text-white transition-all text-xs font-medium border border-indigo-500/20 hover:border-indigo-500"
                                    >
                                        <BellPlus className="w-3.5 h-3.5" />
                                        Set Alert
                                    </button>
                                </td>
                            </motion.tr>
                        ))}
                    </tbody>
                </table>
                {!loading && filteredFragrances.length === 0 && (
                    <div className="p-8 text-center text-zinc-500">No fragrances found matching your search.</div>
                )}
            </div>
        </div>
    );
};
