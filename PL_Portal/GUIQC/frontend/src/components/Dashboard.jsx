import { useQuery } from '@tanstack/react-query'
import { getDashboardStats } from '../api'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import {
    Loader2,
    FolderOpen,
    CheckCircle2,
    XCircle,
    AlertCircle,
    TrendingUp,
    Activity
} from 'lucide-react'
import TestTable from './TestTable'
import FolderGrid from './FolderGrid'

const COLORS = {
    executed: '#22c55e',    // green
    notExecuted: '#94a3b8', // gray
}

const STATUS_COLORS = {
    'Passed': 'badge-success',
    'Failed': 'badge-danger',
    'Blocked': 'badge-warning',
    'Warning': 'badge-warning',
    'No Run': 'badge-neutral',
    'N/A': 'badge-neutral',
    'Not Completed': 'badge-neutral',
}

function Dashboard({ folderId, onDrillDown, isVersionLevel = false }) {
    const { data, isLoading, error } = useQuery({
        queryKey: ['dashboard', folderId],
        queryFn: () => getDashboardStats(folderId),
    })

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-20">
                <div className="flex flex-col items-center gap-3">
                    <Loader2 className="w-12 h-12 animate-spin text-primary-600" />
                    <p className="text-slate-600 font-medium">Loading dashboard data...</p>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="card p-8">
                <div className="flex items-center gap-3 text-danger-600">
                    <XCircle className="w-8 h-8" />
                    <div>
                        <h3 className="font-semibold text-lg">Error Loading Data</h3>
                        <p className="text-sm text-slate-600">{error.message}</p>
                    </div>
                </div>
            </div>
        )
    }

    const { folder_name, summary, children, failed_tests } = data

    // Prepare data for pie chart
    const chartData = [
        { name: 'Passed', value: summary.passed, color: STATUS_COLORS.Passed.replace('badge-success', COLORS.executed) }, // Hacky color mapping, better to use explicit colors
        { name: 'Failed', value: summary.failed, color: '#dc2626' }, // Red-600
        { name: 'Not Executed', value: summary.not_executed, color: COLORS.notExecuted },
    ].filter(item => item.value > 0) // Only show slices with data

    // Check if we're at a leaf node (children are tests, not folders)
    const isLeafNode = children.length > 0 && children[0].type === 'test'

    return (
        <div className="space-y-8">
            {/* Summary Card with Chart */}
            <div className="card p-6 shadow-sm">
                <div className="grid md:grid-cols-2 gap-6">
                    {/* Left: Chart */}
                    <div className="flex flex-col items-center justify-center">
                        <h2 className="text-2xl font-bold text-slate-800 mb-4">
                            {folder_name}
                        </h2>
                        <ResponsiveContainer width="100%" height={250}>
                            <PieChart>
                                <Pie
                                    data={chartData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={70}
                                    outerRadius={90}
                                    paddingAngle={2}
                                    dataKey="value"
                                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                    labelLine={false}
                                >
                                    {chartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="mt-4 text-center">
                            <p className="text-[32px] font-bold text-gradient">
                                {summary.execution_percentage}%
                            </p>
                            <p className="text-sm text-slate-500 mt-1">Execution Progress</p>
                        </div>
                    </div>

                    {/* Right: Stats */}
                    <div className="flex flex-col justify-center space-y-3">
                        <div className="bg-gradient-to-br from-success-50 to-success-100 rounded-xl p-4 border border-success-200">
                            <div className="flex items-center gap-2 mb-1">
                                <CheckCircle2 className="w-5 h-5 text-success-600" />
                                <h3 className="font-semibold text-success-900 text-sm">Executed</h3>
                            </div>
                            <div className="flex items-baseline gap-2">
                                <span className="text-2xl font-bold text-success-700">{summary.executed}</span>
                                <span className="text-xs text-success-600">tests completed</span>
                            </div>
                        </div>

                        <div className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl p-4 border border-slate-200">
                            <div className="flex items-center gap-2 mb-1">
                                <Activity className="w-5 h-5 text-slate-600" />
                                <h3 className="font-semibold text-slate-900 text-sm">Not Executed</h3>
                            </div>
                            <div className="flex items-baseline gap-2">
                                <span className="text-2xl font-bold text-slate-700">{summary.not_executed}</span>
                                <span className="text-xs text-slate-600">tests pending</span>
                            </div>
                        </div>

                        <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-4 border border-red-200">
                            <div className="flex items-center gap-2 mb-1">
                                <AlertCircle className="w-5 h-5 text-red-600" />
                                <h3 className="font-semibold text-red-900 text-sm">Failed</h3>
                            </div>
                            <div className="flex items-baseline gap-2">
                                <span className="text-2xl font-bold text-red-700">{summary.failed}</span>
                                <span className="text-xs text-red-600">tests failed</span>
                            </div>
                        </div>

                        <div className="bg-gradient-to-br from-primary-50 to-primary-100 rounded-xl p-4 border border-primary-200">
                            <div className="flex items-center gap-2 mb-1">
                                <TrendingUp className="w-5 h-5 text-primary-600" />
                                <h3 className="font-semibold text-primary-900 text-sm">Total Tests</h3>
                            </div>
                            <div className="flex items-baseline gap-2">
                                <span className="text-2xl font-bold text-primary-700">{summary.total}</span>
                                <span className="text-xs text-primary-600">in this folder</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Failed Tests Table - Shown if there are failures AND not at version level */}
            {!isVersionLevel && failed_tests && failed_tests.length > 0 && (
                <TestTable 
                    tests={failed_tests} 
                    title={`Failed Tests (${failed_tests.length})`}
                    subtitle="Failures in this folder"
                    variant="danger"
                    showPath={true}
                />
            )}

            {/* Drill-Down Section */}
            {!isLeafNode && children.length > 0 && (
                <FolderGrid 
                    items={children} 
                    title="Sub-Folders" 
                    onSelect={(child) => onDrillDown(child.id, child.name)} 
                    variant="standard"
                />
            )}

            {/* Test Table (Leaf Node) */}
            {isLeafNode && <TestTable tests={children} />}
        </div>
    )
}

export default Dashboard
