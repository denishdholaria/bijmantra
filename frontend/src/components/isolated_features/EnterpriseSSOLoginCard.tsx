import * as React from "react"
import { useState } from "react"
import {
  Building2,
  ArrowRight,
  Chrome,
  ShieldCheck,
  Globe,
  Loader2,
  AlertCircle
} from "lucide-react"
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

interface EnterpriseSSOLoginCardProps {
  className?: string
  onSSOSubmit?: (domain: string) => Promise<void>
}

/**
 * EnterpriseSSOLoginCard Component
 *
 * A standalone component for Enterprise SSO (Single Sign-On) login.
 * Allows users to enter their organization domain or choose a common SSO provider.
 * Follows pure TailwindCSS + Shadcn patterns.
 */
export function EnterpriseSSOLoginCard({ className, onSSOSubmit }: EnterpriseSSOLoginCardProps) {
  const [domain, setDomain] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!domain) {
      setError("Please enter your organization domain")
      return
    }

    // Basic domain validation
    const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$/
    if (!domainRegex.test(domain)) {
      setError("Please enter a valid domain (e.g., company.com)")
      return
    }

    setError(null)
    setIsLoading(true)

    try {
      if (onSSOSubmit) {
        await onSSOSubmit(domain)
      } else {
        // Mocking the SSO redirection logic
        console.log(`Redirecting to SSO for domain: ${domain}`)
        await new Promise(resolve => setTimeout(resolve, 1500))
        // In a real scenario, this would be:
        // window.location.href = `${API_URL}/auth/sso/login?domain=${domain}`
      }
    } catch {
      setError("Failed to initiate SSO login. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleProviderLogin = async (provider: string) => {
    setIsLoading(true)
    setError(null)
    try {
      console.log(`Logging in with ${provider}`)
      await new Promise(resolve => setTimeout(resolve, 1500))
    } catch {
      setError(`Failed to login with ${provider}`)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className={cn("w-full max-w-md mx-auto overflow-hidden", className)}>
      <CardHeader className="space-y-1 bg-slate-50/50 dark:bg-slate-900/50 border-b">
        <div className="flex items-center gap-2 mb-2">
          <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg text-emerald-600 dark:text-emerald-400">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <CardTitle className="text-xl">Enterprise Login</CardTitle>
        </div>
        <CardDescription>
          Sign in using your corporate credentials via Single Sign-On.
        </CardDescription>
      </CardHeader>

      <CardContent className="pt-6 space-y-6">
        {error && (
          <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 flex items-start gap-2 text-red-600 dark:text-red-400 text-sm animate-in fade-in slide-in-from-top-1">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="domain" className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Organization Domain
            </Label>
            <div className="relative group">
              <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 group-focus-within:text-emerald-500 transition-colors" />
              <Input
                id="domain"
                type="text"
                placeholder="company.com"
                value={domain}
                onChange={(e) => {
                  setDomain(e.target.value)
                  if (error) setError(null)
                }}
                disabled={isLoading}
                className="pl-10 h-11 border-slate-200 focus-visible:ring-emerald-500 focus-visible:border-emerald-500 transition-all"
              />
            </div>
          </div>
          <Button
            type="submit"
            className="w-full h-11 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold transition-all shadow-md shadow-emerald-600/10"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Connecting...
              </>
            ) : (
              <>
                Continue with SSO
                <ArrowRight className="ml-2 h-4 w-4" />
              </>
            )}
          </Button>
        </form>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-slate-200 dark:border-slate-800" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-white dark:bg-slate-950 px-2 text-slate-500">
              Or continue with
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Button
            variant="outline"
            className="h-11 border-slate-200 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900 transition-all"
            onClick={() => handleProviderLogin("Google")}
            disabled={isLoading}
          >
            <Chrome className="mr-2 h-4 w-4" />
            Google
          </Button>
          <Button
            variant="outline"
            className="h-11 border-slate-200 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900 transition-all"
            onClick={() => handleProviderLogin("Microsoft")}
            disabled={isLoading}
          >
            <Building2 className="mr-2 h-4 w-4" />
            Azure AD
          </Button>
        </div>
      </CardContent>

      <CardFooter className="flex flex-col space-y-4 border-t pt-6 bg-slate-50/30 dark:bg-slate-900/10">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <ShieldCheck className="h-3 w-3" />
          <span>Secured by Bijmantra Auth Gateway</span>
        </div>
        <div className="w-full flex justify-between items-center text-xs">
          <button type="button" className="text-slate-500 hover:text-emerald-600 transition-colors cursor-pointer">Help Center</button>
          <button type="button" className="text-slate-500 hover:text-emerald-600 transition-colors cursor-pointer">Privacy Policy</button>
        </div>
      </CardFooter>
    </Card>
  )
}
