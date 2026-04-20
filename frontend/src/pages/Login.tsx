/**
 * Login Page - Thin Adapter
 * 
 * Thin route-entry adapter for the Login feature.
 * All business logic lives in features/auth/LoginForm.tsx
 */

import { LoginForm } from '@/features/auth/LoginForm'

export function Login() {
  return <LoginForm />
}
