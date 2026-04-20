import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, ArrowRight, Database, FileText, Network } from 'lucide-react'

const nextSteps = [
  {
    title: 'Review server capabilities',
    description: 'Use the runtime-backed server information surface to inspect the active API host and environment details.',
    route: '/serverinfo',
    icon: Database,
  },
  {
    title: 'Inspect API metrics',
    description: 'Check the published-versus-exposed BrAPI counts and current endpoint totals from the shared metrics surface.',
    route: '/dev-progress',
    icon: Network,
  },
  {
    title: 'Consult the reference docs',
    description: 'Open the detailed documentation page for BrAPI context, workflow guidance, and linked specifications.',
    route: '/help/docs',
    icon: FileText,
  },
]

export function APIExplorer() {

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold tracking-tight">API Explorer</h1>
            <Badge variant="outline">Execution disabled</Badge>
          </div>
          <p className="max-w-3xl text-muted-foreground">
            This route no longer simulates endpoint catalogs or fake request results. Live request execution will return here only after the explorer is connected to backend-discovered endpoints and tenant-safe request handling.
          </p>
        </div>
      </div>

      <Card className="border-amber-300 bg-amber-50/60">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-amber-900">
            <AlertTriangle className="h-5 w-5" />No synthetic responses
          </CardTitle>
          <CardDescription className="text-amber-900/80">
            BijMantra does not manufacture API execution results or placeholder endpoint catalogs on live admin routes.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-amber-950">
          <p>
            The previous test surface returned hardcoded request results. That behavior has been removed to keep the administration area truthful until a backend-backed explorer is implemented.
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">Backend discovery required</Badge>
            <Badge variant="secondary">Tenant-safe execution required</Badge>
            <Badge variant="secondary">No mock request output</Badge>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        {nextSteps.map((item) => {
          const Icon = item.icon

          return (
            <Link key={item.title} to={item.route} className="rounded-lg border bg-card p-5 transition-colors hover:bg-muted">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Icon className="h-5 w-5 text-muted-foreground" />
                    <p className="font-medium">{item.title}</p>
                  </div>
                  <p className="text-sm text-muted-foreground">{item.description}</p>
                </div>
                <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
              </div>
            </Link>
          )
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Implementation requirements</CardTitle>
          <CardDescription>
            The next implementation should use runtime data instead of placeholder catalogs.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          <p>1. Discover endpoints from the actual backend or OpenAPI document instead of a hardcoded list.</p>
          <p>2. Execute requests against the authenticated API host with tenant-aware safeguards.</p>
          <p>3. Render only real request and response payloads, including failure states, provenance, and status codes.</p>
          <div>
            <Link to="/admin/developer/master-board">
              <Button variant="outline">Track implementation on the developer board</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
