import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getDevices, getVersions } from './api' // We need to update api.js too
import Dashboard from './components/Dashboard'
import FolderGrid from './components/FolderGrid'
import { Loader2 } from 'lucide-react'

// View Modes
const VIEW_DEVICES = 'VIEW_DEVICES'
const VIEW_VERSIONS = 'VIEW_VERSIONS'
const VIEW_DASHBOARD = 'VIEW_DASHBOARD'

function App() {
    // Navigation State
    const [viewMode, setViewMode] = useState(VIEW_DEVICES)
    const [selectedDevice, setSelectedDevice] = useState(null)
    // navigationPath stores the stack of folders: [{id, name}, {id, name}, ...]
    const [navigationPath, setNavigationPath] = useState([])

    // Data Fetching for Devices (Level 0)
    const { data: devices, isLoading: devicesLoading, error: deviceError } = useQuery({
        queryKey: ['devices'],
        queryFn: getDevices,
        enabled: viewMode === VIEW_DEVICES
    })

    // Data Fetching for Versions (Level 1)
    const { data: versions, isLoading: versionsLoading } = useQuery({
        queryKey: ['versions', selectedDevice?.id],
        queryFn: () => getVersions(selectedDevice.id),
        enabled: !!selectedDevice && viewMode === VIEW_VERSIONS
    })

    // Handlers
    const handleSelectDevice = (device) => {
        setSelectedDevice(device)
        setViewMode(VIEW_VERSIONS)
        setNavigationPath([]) // Reset path when switching devices
    }

    const handleSelectVersion = (version) => {
        // Initialize path with the selected version
        setNavigationPath([{ id: version.id, name: version.name }])
        setViewMode(VIEW_DASHBOARD)
    }

    const handleDrillDown = (folderId, folderName) => {
        // Push new folder to path
        setNavigationPath(prev => [...prev, { id: folderId, name: folderName }])
    }

    const handleBreadcrumbClick = (index) => {
        // Slice path to go back to a specific level
        const newPath = navigationPath.slice(0, index + 1)
        setNavigationPath(newPath)
    }

    const handleBackToDevices = () => {
        setSelectedDevice(null)
        setNavigationPath([])
        setViewMode(VIEW_DEVICES)
    }

    const handleBackToVersions = () => {
        setNavigationPath([])
        setViewMode(VIEW_VERSIONS)
    }

    // Render Content based on View Mode
    const renderContent = () => {
        if (devicesLoading && viewMode === VIEW_DEVICES) {
            return (
                <div className="flex flex-col items-center justify-center p-20">
                    <Loader2 className="w-12 h-12 animate-spin text-primary-600 mb-4" />
                    <p className="text-slate-500">Loading Devices...</p>
                </div>
            )
        }

        if (deviceError && viewMode === VIEW_DEVICES) {
            return (
                <div className="text-center p-10 text-red-500">
                    Error loading devices: {deviceError.message}
                </div>
            )
        }

        switch (viewMode) {
            case VIEW_DEVICES:
                return (
                    <FolderGrid
                        items={devices}
                        onSelect={handleSelectDevice}
                        title="PL Devices"
                        variant="key"
                        emptyMessage="No devices found"
                    />
                )
            case VIEW_VERSIONS:
                if (versionsLoading) {
                    return (
                        <div className="flex flex-col items-center justify-center p-20">
                            <Loader2 className="w-10 h-10 animate-spin text-primary-600 mb-4" />
                            <p className="text-slate-500">Loading Versions for {selectedDevice?.name}...</p>
                        </div>
                    )
                }
                return (
                    <FolderGrid
                        items={versions}
                        onSelect={handleSelectVersion}
                        title="Versions"
                        subtitle={selectedDevice?.name}
                        variant="standard"
                        onBack={handleBackToDevices}
                        backLabel="Back to Devices"
                        emptyMessage={`No versions found for ${selectedDevice?.name}`}
                    />
                )
            case VIEW_DASHBOARD:
                // The current folder is the last item in the navigation path
                const currentFolder = navigationPath[navigationPath.length - 1]
                const isVersionLevel = navigationPath.length === 1
                
                return (
                    <div>
                         {/* Breadcrumbs for Dashboard Depth */}
                         <div className="flex flex-wrap items-center gap-2 mb-6 text-sm">
                            <button 
                                onClick={handleBackToVersions}
                                className="text-slate-500 hover:text-blue-600 transition-colors font-medium flex items-center"
                            >
                                <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                </svg>
                                {selectedDevice.name}
                            </button>
                            
                            {navigationPath.map((item, index) => (
                                <div key={item.id} className="flex items-center gap-2">
                                    <span className="text-slate-300">/</span>
                                    <button
                                        onClick={() => handleBreadcrumbClick(index)}
                                        disabled={index === navigationPath.length - 1}
                                        className={`font-medium transition-colors ${
                                            index === navigationPath.length - 1 
                                                ? 'text-slate-800 cursor-default' 
                                                : 'text-blue-600 hover:text-blue-800'
                                        }`}
                                    >
                                        {item.name}
                                    </button>
                                </div>
                            ))}
                        </div>

                        <Dashboard
                            folderId={currentFolder.id}
                            onDrillDown={handleDrillDown}
                            isVersionLevel={isVersionLevel}
                        />
                    </div>
                )
            default:
                return <div>Unknown View</div>
        }
    }

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Header */}
            <header className="glass sticky top-0 z-50 shadow-sm border-b border-white/20">
                <div className="container mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 cursor-pointer" onClick={handleBackToDevices}>
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
                                <span className="text-white font-bold text-xl">PL</span>
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-slate-800 tracking-tight">
                                    ALM Quality Dashboard
                                </h1>
                                <p className="text-xs text-slate-500 font-medium">PacketLight Networks</p>
                            </div>
                        </div>

                        {/* Current Context Badge */}
                        <div className="hidden md:flex items-center gap-2">
                            {selectedDevice && (
                                <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-semibold border border-blue-100">
                                    {selectedDevice.name}
                                </span>
                            )}
                            {/* Show current leaf in header if separate from crumbs */}
                            {navigationPath.length > 0 && (
                                <>
                                    <span className="text-slate-300">/</span>
                                    <span className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-xs font-semibold border border-indigo-100 truncate max-w-[200px]">
                                        {navigationPath[navigationPath.length - 1].name}
                                    </span>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-6 py-8">
                {renderContent()}
            </main>

            {/* Footer */}
            <footer className="mt-auto py-8 border-t border-slate-200 bg-white">
                <div className="container mx-auto px-6 text-center">
                    <p className="text-sm text-slate-400 font-medium">
                        © 2026 PacketLight Networks - Test Execution Dashboard
                    </p>
                </div>
            </footer>
        </div>
    )
}

export default App
