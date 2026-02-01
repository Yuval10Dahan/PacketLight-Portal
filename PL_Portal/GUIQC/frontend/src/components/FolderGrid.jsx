import { FolderOpen, TrendingUp, CheckCircle2, AlertCircle, Activity } from 'lucide-react'

export default function FolderGrid({ 
    items, 
    onSelect, 
    title, 
    subtitle,
    variant = 'standard', // 'standard' | 'key' (for PL devices)
    emptyMessage = "No items found",
    onBack = null,
    backLabel = "Go Back"
}) {
    if (!items || items.length === 0) {
        return (
            <div className="text-center p-10">
                <h3 className="text-lg text-slate-600 mb-4">{emptyMessage}</h3>
                {onBack && (
                    <button onClick={onBack} className="text-blue-600 hover:underline">
                        {backLabel}
                    </button>
                )}
            </div>
        )
    }

    return (
        <div className="animate-fade-in-up">
            {onBack && (
                <button
                    onClick={onBack}
                    className="mb-6 flex items-center text-slate-500 hover:text-blue-600 transition-colors font-medium group"
                >
                    <svg className="w-5 h-5 mr-1 transform group-hover:-translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    {backLabel}
                </button>
            )}

            {(title || subtitle) && (
                <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center">
                    {subtitle && <span className="text-slate-400 font-normal mr-2">{subtitle} /</span>}
                    {title}
                </h2>
            )}

            <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6`}>
                {items.map((item) => (
                    <div
                        key={item.id}
                        onClick={() => onSelect(item)}
                        className={`
                            group relative bg-white/90 backdrop-blur-md rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 border border-slate-100 cursor-pointer overflow-hidden transform hover:-translate-y-1
                            ${variant === 'key' ? 'hover:border-blue-200' : 'hover:border-primary-200'}
                        `}
                    >
                        {/* Variant: Key (Devices) has a top gradient border */}
                        {variant === 'key' && (
                            <div className="h-1.5 w-full bg-gradient-to-r from-blue-500 to-indigo-600 opacity-80 group-hover:opacity-100 transition-opacity" />
                        )}

                        <div className="p-6">
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className={`
                                        p-3 rounded-xl transition-colors
                                        ${variant === 'key' ? 'bg-blue-50 group-hover:bg-blue-100' : 'bg-primary-100 group-hover:bg-primary-600'}
                                    `}>
                                        {variant === 'key' ? (
                                             <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M12 5l7 7-7 7" />
                                            </svg>
                                        ) : (
                                            <FolderOpen className={`w-6 h-6 ${variant === 'standard' ? 'text-primary-600 group-hover:text-white' : ''} transition-colors`} />
                                        )}
                                    </div>
                                    <div>
                                        <h3 className={`font-bold text-slate-800 transition-colors ${variant === 'key' ? 'text-lg group-hover:text-blue-700' : 'text-lg group-hover:text-primary-700'}`}>
                                            {item.name}
                                        </h3>
                                        {variant === 'key' && (
                                            <p className="text-xs text-slate-500 uppercase tracking-wide font-medium">Device Folder</p>
                                        )}
                                    </div>
                                </div>
                                {variant === 'key' && (
                                     <span className="bg-slate-100 px-2 py-1 rounded text-xs text-slate-600">ID: {item.id}</span>
                                )}
                            </div>

                            {/* Stats Section (if available) - Standard variant usually has stats */}
                            {variant === 'standard' && item.total !== undefined ? (
                                <div className="space-y-2 mt-2">
                                     <div className="flex justify-between items-center text-sm">
                                        <span className="text-slate-600">Passed:</span>
                                        <span className="font-semibold text-success-600">{item.passed || 0}</span>
                                    </div>
                                    <div className="flex justify-between items-center text-sm">
                                        <span className="text-slate-600">Failed:</span>
                                        <span className={`font-semibold ${(item.failed || 0) > 0 ? 'text-red-600' : 'text-slate-400'}`}>
                                            {item.failed || 0}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center text-sm">
                                        <span className="text-slate-600">Not Executed:</span>
                                        <span className="font-semibold text-slate-500">{item.not_executed || 0}</span>
                                    </div>

                                    {/* Progress Bar */}
                                    <div className="mt-3 w-full bg-slate-100 rounded-full h-2 flex overflow-hidden">
                                        <div
                                            className="bg-success-500 h-full"
                                            style={{ width: `${((item.passed || 0) / (item.total || 1)) * 100}%` }}
                                        />
                                        <div
                                            className="bg-red-500 h-full"
                                            style={{ width: `${((item.failed || 0) / (item.total || 1)) * 100}%` }}
                                        />
                                    </div>
                                    <p className="text-xs text-center text-slate-500 mt-2">
                                        {item.total || 0} Total Tests
                                    </p>
                                </div>
                            ) : null}

                             {/* Key Variant Arrow */}
                            {variant === 'key' && (
                                <div className="mt-4 flex items-center justify-between text-sm text-slate-500">
                                    <span className="flex items-center hover:text-blue-600 transition-colors">
                                        View Versions &rarr;
                                    </span>
                                </div>
                            )}
                             
                            {/* Simple Versions List Item - No stats, just ID */}
                             {variant === 'standard' && item.total === undefined && (
                                <div className="mt-2 text-sm text-slate-400">
                                     ID: {item.id}
                                </div>
                             )}

                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
