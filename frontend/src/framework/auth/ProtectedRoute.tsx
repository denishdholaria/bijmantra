/**
 * Parashakti Framework - Protected Route
 * 
 * Route wrapper that checks authentication and permissions.
 */

import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermissions?: string[];
  requiredDivision?: string;
  fallback?: React.ReactNode;
  redirectTo?: string;
}

/**
 * Protects routes based on authentication and permissions
 */
export function ProtectedRoute({
  children,
  requiredPermissions = [],
  requiredDivision,
  fallback,
  redirectTo = '/login',
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, hasAllPermissions, canAccessDivision } = useAuth();
  const location = useLocation();

  // Show loading state
  if (isLoading) {
    return fallback ?? (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600" />
      </div>
    );
  }

  // Check authentication
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  // Check permissions
  if (requiredPermissions.length > 0 && !hasAllPermissions(requiredPermissions)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] p-6">
        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-2">
          Access Denied
        </h2>
        <p className="text-gray-600 dark:text-gray-400 text-center">
          You don't have permission to access this page.
        </p>
      </div>
    );
  }

  // Check division access
  if (requiredDivision && !canAccessDivision(requiredDivision)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] p-6">
        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-2">
          Division Not Available
        </h2>
        <p className="text-gray-600 dark:text-gray-400 text-center">
          This division is not enabled for your organization.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
