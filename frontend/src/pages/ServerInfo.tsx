/**
 * Server Info Page - BrAPI Core Module
 * BrAPI server information and capabilities
 * 
 * Production-ready: Fetches from /brapi/v2/serverinfo
 */
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import { StatusPage } from '@/components/StatusPage'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'

interface ServerInfo {
  serverName: string
  serverDescription: string
  organizationName: string
  organizationURL: string
  location: string
  contactEmail: string
  documentationURL: string
  brapiVersion: string
  calls: Array<{
    service: string
    dataTypes: string[]
    methods: string[]
    versions: string[]
  }>
}

export function ServerInfo() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['serverInfo'],
    queryFn: async (): Promise<ServerInfo | null> => {
      const response = await fetch('/brapi/v2/serverinfo')
      if (!response.ok) {
        throw new Error('Failed to fetch server info')
      }
      const json = await response.json()
      const result = json.result || json
      
      // Map BrAPI response to our interface
      return {
        serverName: result.serverName || 'BijMantra Server',
        serverDescription: result.serverDescription || '',
        organizationName: result.organizationName || '',
        organizationURL: result.organizationURL || '',
        location: result.location || '',
        contactEmail: result.contactEmail || '',
        documentationURL: result.documentationURL || '',
        brapiVersion: result.brapiVersion || '2.1',
        calls: result.calls || []
      }
    },
  })

  const serverInfo = data

  const getMethodBadge = (method: string) => {
    const colors: Record<string, string> = {
      GET: 'bg-green-100 text-green-800',
      POST: 'bg-blue-100 text-blue-800',
      PUT: 'bg-yellow-100 text-yellow-800',
      DELETE: 'bg-red-100 text-red-800',
    }
    return colors[method] || 'bg-gray-100 text-gray-800'
  }

  const copyEndpoint = (service: string) => {
    navigator.clipboard.writeText(`/brapi/v2/${service}`)
    toast.success('Endpoint copied to clipboard')
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error || !serverInfo) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Server Information</h1>
          <p className="text-muted-foreground mt-1">BrAPI server capabilities, endpoints, and system status</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Unable to fetch server information. Please ensure the backend is running.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold">Server Information</h1>
        <p className="text-muted-foreground mt-1">BrAPI server capabilities, endpoints, and system status</p>
      </div>

      <Tabs defaultValue="info">
        <TabsList>
          <TabsTrigger value="info">Server Info</TabsTrigger>
          <TabsTrigger value="endpoints">Endpoints</TabsTrigger>
          <TabsTrigger value="status">System Status</TabsTrigger>
        </TabsList>

        <TabsContent value="info" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Server Details</CardTitle>
            <CardDescription>Basic server information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground">Server Name</p>
              <p className="font-semibold">{serverInfo?.serverName}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Description</p>
              <p className="text-sm">{serverInfo?.serverDescription}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">BrAPI Version</p>
              <Badge className="bg-green-100 text-green-800">v{serverInfo?.brapiVersion}</Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Location</p>
              <p className="font-medium">{serverInfo?.location}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Organization</CardTitle>
            <CardDescription>Contact and documentation</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground">Organization</p>
              <p className="font-semibold">{serverInfo?.organizationName}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Website</p>
              <a href={serverInfo?.organizationURL} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                {serverInfo?.organizationURL}
              </a>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Contact</p>
              <a href={`mailto:${serverInfo?.contactEmail}`} className="text-primary hover:underline">
                {serverInfo?.contactEmail}
              </a>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Documentation</p>
              <a href={serverInfo?.documentationURL} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                {serverInfo?.documentationURL}
              </a>
            </div>
          </CardContent>
        </Card>
      </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6 text-center">
                <div className="text-2xl font-bold">{serverInfo?.calls.length}</div>
                <p className="text-sm text-muted-foreground">Endpoints</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 text-center">
                <div className="text-2xl font-bold">{serverInfo?.calls.filter(c => c.methods.includes('GET')).length}</div>
                <p className="text-sm text-muted-foreground">GET Endpoints</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 text-center">
                <div className="text-2xl font-bold">{serverInfo?.calls.filter(c => c.methods.includes('POST')).length}</div>
                <p className="text-sm text-muted-foreground">POST Endpoints</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 text-center">
                <div className="text-2xl font-bold">v{serverInfo?.brapiVersion}</div>
                <p className="text-sm text-muted-foreground">BrAPI Version</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="endpoints" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Available Endpoints</CardTitle>
              <CardDescription>{serverInfo?.calls.length} BrAPI services available</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {serverInfo?.calls.map((call) => (
                  <div key={call.service} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <div className="flex items-center gap-4">
                      <code className="text-sm font-mono bg-background px-2 py-1 rounded">
                        /brapi/v2/{call.service}
                      </code>
                      <div className="flex gap-1">
                        {call.methods.map((method) => (
                          <Badge key={method} className={getMethodBadge(method)} variant="secondary">
                            {method}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">v{call.versions[0]}</Badge>
                      <Button size="sm" variant="ghost" onClick={() => copyEndpoint(call.service)}>
                        📋
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="status" className="mt-6">
          <StatusPage />
        </TabsContent>
      </Tabs>
    </div>
  )
}
