/**
 * Minimal App for debugging white screen
 */

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Login } from '@/pages/Login'

function MinimalDashboard() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-green-600">🌱 Bijmantra Dashboard</h1>
      <p className="mt-4 text-gray-600">If you see this, the app is working!</p>
    </div>
  )
}

export default function App() {
  console.log('[App] Rendering minimal app...')
  
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<MinimalDashboard />} />
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Router>
  )
}
