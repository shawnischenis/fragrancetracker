import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ChevronDown, Bell, TrendingUp, Droplet } from 'lucide-react';

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

    // Search Dropdown States
    const [showDropdown, setShowDropdown] = useState(false);
    const searchContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchData();

        // Close dropdown when clicking outside
        const handleClickOutside = (event: MouseEvent) => {
            if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
                setShowDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
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

    // --- Search Logic ---
    const lowerSearch = searchTerm.toLowerCase();

    // 1. Filtered List for Table (matches search)
    const filteredFragrances = fragrances.filter(f =>
        f.reddit_name.toLowerCase().includes(lowerSearch) ||
        (f.brand && f.brand.toLowerCase().includes(lowerSearch))
    );

    // 2. Dropdown Suggestions Logic
    // Get unique matching brands
    const matchingBrands = Array.from(new Set(
        fragrances
            .filter(f => f.brand && f.brand.toLowerCase().includes(lowerSearch))
            .map(f => f.brand as string)
    )).slice(0, 3); // Top 3 matching brands

    // Get matching individual fragrances (exclude if covered by brand search? no, show specific)
    const matchingItems = fragrances
        .filter(f => f.reddit_name.toLowerCase().includes(lowerSearch))
        .slice(0, 5); // Top 5 matching items

    const handleSelectSuggestion = (term: string) => {
        setSearchTerm(term);
        setShowDropdown(false);
    };

    return (
        <div className="w-full space-y-6">
            {/* --- Smart Search Bar --- */}
            <div className="relative max-w-2xl mx-auto" ref={searchContainerRef}>
                <div className="relative group">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400 w-5 h-5 group-focus-within:text-stone-600 transition-colors" />
                    <input
                        type="text"
                        placeholder="Search for a scent (e.g. 'Aventus') or brand..."
                        className="w-full pl-12 pr-4 py-4 bg-white border border-stone-200 rounded-2xl text-stone-800 placeholder-stone-400 focus:ring-2 focus:ring-stone-200 focus:border-stone-300 outline-none shadow-sm transition-all text-lg font-light"
                        value={searchTerm}
                        onChange={(e) => {
                            setSearchTerm(e.target.value);
                            setShowDropdown(true);
                        }}
                        onFocus={() => setShowDropdown(true)}
                    />
                </div>

                {/* Dropdown Results */}
                <AnimatePresence>
                    {showDropdown && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 10 }}
                            className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border border-stone-100 overflow-hidden z-50 py-2"
                        >
                            {searchTerm.length === 0 ? (
                                // Default / Empty State -> Show Trending (Simulated)
                                <div>
                                    <div className="px-4 py-2 text-xs font-semibold text-stone-400 uppercase tracking-wider">Trending Now</div>
                                    {fragrances.slice(0, 5).map((f, i) => (
                                        <div
                                            key={i}
                                            onClick={() => handleSelectSuggestion(f.reddit_name)}
                                            className="px-4 py-3 hover:bg-stone-50 cursor-pointer flex items-center justify-between group"
                                        >
                                            <div className="flex items-center gap-3">
                                                <TrendingUp className="w-4 h-4 text-stone-300 group-hover:text-rose-400" />
                                                <span className="text-stone-700">{f.reddit_name}</span>
                                            </div>
                                            <span className="text-stone-400 text-xs">${f.weighted_avg_price?.toFixed(0)}</span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                // Search Results
                                <div>
                                    {matchingBrands.length > 0 && (
                                        <div className="mb-2">
                                            <div className="px-4 py-2 text-xs font-semibold text-stone-400 uppercase tracking-wider">Brands</div>
                                            {matchingBrands.map((brand, i) => (
                                                <div
                                                    key={i}
                                                    onClick={() => handleSelectSuggestion(brand)}
                                                    className="px-4 py-2 hover:bg-stone-50 cursor-pointer text-stone-800 font-medium"
                                                >
                                                    {brand}
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    <div>
                                        <div className="px-4 py-2 text-xs font-semibold text-stone-400 uppercase tracking-wider">Fragrances</div>
                                        {matchingItems.length > 0 ? matchingItems.map((f, i) => (
                                            <div
                                                key={i}
                                                onClick={() => handleSelectSuggestion(f.reddit_name)}
                                                className="px-4 py-3 hover:bg-stone-50 cursor-pointer flex items-center justify-between"
                                            >
                                                <span className="text-stone-600">{f.reddit_name}</span>
                                                {f.brand && <span className="text-xs text-stone-400 bg-stone-100 px-2 py-1 rounded-full">{f.brand}</span>}
                                            </div>
                                        )) : (
                                            <div className="px-4 py-3 text-stone-400 italic text-sm">No matched fragrances found.</div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* --- Data Table --- */}
            <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
                <table className="w-full text-left text-sm text-stone-600">
                    <thead className="bg-[#F6F4F1] text-stone-500 uppercase tracking-wider text-xs border-b border-stone-100">
                        <tr>
                            <th className="px-6 py-5 font-semibold font-serif">Fragrance</th>
                            <th className="px-6 py-5 font-semibold font-serif">Market AVG</th>
                            <th className="px-6 py-5 font-semibold font-serif">Volatility</th>
                            <th className="px-6 py-5 font-semibold font-serif">Retail Ref</th>
                            <th className="px-6 py-5 font-semibold font-serif text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-100">
                        {loading ? (
                            <tr><td colSpan={5} className="px-6 py-12 text-center text-stone-400 font-light">Loading the index...</td></tr>
                        ) : filteredFragrances.map((fragrance, idx) => (
                            <motion.tr
                                key={idx}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: idx * 0.03 }}
                                className="group hover:bg-[#FAF9F7] transition-colors"
                            >
                                <td className="px-6 py-4">
                                    <div className="flex flex-col">
                                        <span className="font-medium text-stone-800 text-base">{fragrance.reddit_name}</span>
                                        <span className="text-xs text-stone-400 font-medium tracking-wide">{fragrance.brand}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="text-stone-800 font-medium text-lg">${fragrance.weighted_avg_price?.toFixed(0)}</span>
                                    <span className="text-xs text-stone-400 ml-1.5 block">based on {fragrance.listing_count} sales</span>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex flex-col gap-1.5 w-24">
                                        <div className="h-1.5 bg-stone-200 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-stone-400/80 rounded-full"
                                                style={{ width: `${Math.min(((fragrance.weighted_std_dev || 0) / (fragrance.weighted_avg_price || 1)) * 500, 100)}%` }}
                                            />
                                        </div>
                                        <span className="text-[10px] text-stone-400">±${fragrance.weighted_std_dev?.toFixed(0)}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    {fragrance.jomashop_price ? (
                                        <div className="flex flex-col">
                                            <span className="text-stone-500 font-mono text-xs uppercase tracking-wide">Jomashop</span>
                                            <div className="flex items-center gap-2">
                                                <span className="text-stone-700">${fragrance.jomashop_price.toFixed(0)}</span>
                                                {fragrance.weighted_price_diff && (
                                                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${fragrance.weighted_price_diff < 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                                                        {fragrance.weighted_price_diff < 0 ? 'DEAL' : 'HIGH'}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    ) : <span className="text-stone-300">-</span>}
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <button
                                        onClick={() => onOpenAlert(fragrance)}
                                        className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-stone-200 text-stone-600 rounded-full hover:bg-stone-800 hover:text-white hover:border-stone-800 transition-all text-xs font-semibold shadow-sm"
                                    >
                                        <Bell className="w-3.5 h-3.5" />
                                        Alert
                                    </button>
                                </td>
                            </motion.tr>
                        ))}
                    </tbody>
                </table>
                {!loading && filteredFragrances.length === 0 && (
                    <div className="p-12 text-center text-stone-400">No fragrances found matching "{searchTerm}".</div>
                )}
            </div>
        </div>
    );
};
