import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

const STATUS_COLORS = {
    'Passed': 'badge-success',
    'Failed': 'badge-danger',
    'Blocked': 'badge-warning',
    'Warning': 'badge-warning',
    'No Run': 'badge-neutral',
    'N/A': 'badge-neutral',
    'Not Completed': 'badge-neutral',
}

const VARIANTS = {
    primary: 'from-primary-600 to-primary-500',
    danger: 'from-red-600 to-red-500'
}

function TestTable({ tests, title = "Test Instances", subtitle, variant = "primary", showPath = false }) {
    const [sortConfig, setSortConfig] = useState({ key: 'name', direction: 'asc' })
    const [isExpanded, setIsExpanded] = useState(true)

    const handleSort = (key) => {
        let direction = 'asc'
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc'
        }
        setSortConfig({ key, direction })
    }

    const sortedTests = [...tests].sort((a, b) => {
        if (!a[sortConfig.key]) return 1;
        if (!b[sortConfig.key]) return -1;
        if (a[sortConfig.key] < b[sortConfig.key]) {
            return sortConfig.direction === 'asc' ? -1 : 1
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
            return sortConfig.direction === 'asc' ? 1 : -1
        }
        return 0
    })

    return (
        <div className="card overflow-hidden transition-all duration-300">
            <button 
                onClick={() => setIsExpanded(!isExpanded)}
                className={`w-full text-left px-6 py-4 bg-gradient-to-r ${VARIANTS[variant] || VARIANTS.primary} flex items-center justify-between hover:opacity-90 transition-opacity`}
            >
                <div>
                    <h3 className="text-xl font-bold text-white">{title}</h3>
                    <p className="text-sm text-white/80 mt-1">
                        {subtitle || `${tests.length} test${tests.length !== 1 ? 's' : ''} found`}
                    </p>
                </div>
                {isExpanded ? (
                    <ChevronUp className="w-6 h-6 text-white" />
                ) : (
                    <ChevronDown className="w-6 h-6 text-white" />
                )}
            </button>

            {isExpanded && (
                <>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-slate-50 border-b border-slate-200">
                                <tr>
                                    <th
                                        className="px-6 py-4 text-left text-sm font-semibold text-slate-700 cursor-pointer hover:bg-slate-100 transition-colors"
                                        onClick={() => handleSort('name')}
                                    >
                                        <div className="flex items-center gap-2">
                                            Test Name
                                            {sortConfig.key === 'name' &&
                                                (sortConfig.direction === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />)}
                                        </div>
                                    </th>
                                    <th
                                        className="px-6 py-4 text-left text-sm font-semibold text-slate-700 cursor-pointer hover:bg-slate-100 transition-colors"
                                        onClick={() => handleSort('status')}
                                    >
                                        <div className="flex items-center gap-2">
                                            Status
                                            {sortConfig.key === 'status' &&
                                                (sortConfig.direction === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />)}
                                        </div>
                                    </th>
                                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Owner</th>
                                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Execution Date</th>
                                    {showPath && <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Folder Path</th>}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-200">
                                {sortedTests.map((test, index) => (
                                    <tr
                                        key={test.id || index}
                                        className="hover:bg-slate-50 transition-colors"
                                    >
                                        <td className="px-6 py-4 text-sm text-slate-800 font-medium table-cell-wrap max-w-xs" title={test.name}>
                                            {test.name || 'N/A'}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`badge ${STATUS_COLORS[test.status] || 'badge-neutral'}`}>
                                                {test.status || 'Unknown'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-600">
                                            {test.owner || 'N/A'}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-600">
                                            {test.exec_date || 'Not executed'}
                                        </td>
                                        {showPath && (
                                            <td className="px-6 py-4 text-sm text-slate-600">
                                                {test.path || '-'}
                                            </td>
                                        )}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {tests.length === 0 && (
                        <div className="px-6 py-12 text-center">
                            <p className="text-slate-500">No tests found</p>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

export default TestTable
