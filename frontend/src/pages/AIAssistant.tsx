/**
 * Legacy AI Assistant route.
 *
 * Production chat is canonicalized on the server-side REEVU path. This route
 * remains only as a compatibility redirect so the application no longer ships
 * a second browser-to-vendor production chat implementation.
 */
import { Navigate } from 'react-router-dom'

export function AIAssistant() {
  return <Navigate to="/reevu" replace />
}