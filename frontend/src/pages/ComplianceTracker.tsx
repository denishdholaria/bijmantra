import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, ArrowRight, Database, FileCheck, Shield } from 'lucide-react'

const evidenceAreas = [
  {
    title: 'Certificates and permits',
    description: 'Store authoritative certificates, permit files, and renewal dates in the database before status views are enabled.',
  },
  {
    title: 'Audit evidence',
    description: 'Review imports, workflow activity, and approval history in the audit log so traceability stays tied to recorded events.',
  },
  {
    title: 'Policy and security records',
    description: 'Connect policy acknowledgements, security events, and supporting documents before surfacing organization-level status.',
  },
]

export function ComplianceTracker() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold tracking-tight">Compliance Workspace</h1>
            <Badge variant="outline">Database-backed only</Badge>
          </div>
          <p className="max-w-3xl text-muted-foreground">
            This workspace becomes active when organization compliance records are connected. BijMantra does not show compliance percentages, deadlines, or status summaries until those records exist in the database.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to="/data-validation">
            <Button variant="outline">
              <Database className="mr-2 h-4 w-4" />Review data readiness
            </Button>
          </Link>
          <Link to="/auditlog">
            <Button>
              <FileCheck className="mr-2 h-4 w-4" />Open audit log
            </Button>
          </Link>
        </div>
      </div>

      <Card className="border-amber-300 bg-amber-50/60">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-amber-900">
            <AlertTriangle className="h-5 w-5" />No live compliance summary yet
          </CardTitle>
          <CardDescription className="text-amber-900/80">
            Status widgets appear only after connected records are available for this organization.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-amber-950">
          <p>
            Use this area to prepare the underlying records first. Once certificates, audits, and supporting evidence are stored in the database, this workspace can present organization-specific status without fabricated placeholders.
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">Tenant-scoped records required</Badge>
            <Badge variant="secondary">No hardcoded status data</Badge>
            <Badge variant="secondary">Evidence before summaries</Badge>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        {evidenceAreas.map((area) => (
          <Card key={area.title}>
            <CardHeader>
              <CardTitle className="text-lg">{area.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{area.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />Suggested next checks
          </CardTitle>
          <CardDescription>
            Related administration surfaces that already read from recorded system data.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          <Link to="/security" className="rounded-lg border p-4 transition-colors hover:bg-muted">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="font-medium">Security</p>
                <p className="text-sm text-muted-foreground">Review access, credentials, and system safeguards.</p>
              </div>
              <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground" />
            </div>
          </Link>
          <Link to="/data-validation" className="rounded-lg border p-4 transition-colors hover:bg-muted">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="font-medium">Data Validation</p>
                <p className="text-sm text-muted-foreground">Confirm required fields and documents are available.</p>
              </div>
              <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground" />
            </div>
          </Link>
          <Link to="/auditlog" className="rounded-lg border p-4 transition-colors hover:bg-muted">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="font-medium">Audit Log</p>
                <p className="text-sm text-muted-foreground">Inspect recorded actions, imports, and workflow history.</p>
              </div>
              <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground" />
            </div>
          </Link>
        </CardContent>
      </Card>
    </div>
  )
}
