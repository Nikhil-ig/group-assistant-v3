import React from 'react'
import Dashboard from './components/Dashboard'

export default function App() {
    return (
        <div className="min-h-screen bg-gray-50 text-gray-900">
            <header className="bg-white shadow">
                <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
                    <h1 className="text-3xl font-bold">V3 Moderation Dashboard</h1>
                </div>
            </header>
            <main className="py-8">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <Dashboard />
                </div>
            </main>
        </div>
    )
}
