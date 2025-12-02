import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  FileText,
  Download,
  BarChart3,
  TrendingUp,
  Users,
  Calendar,
  MapPin,
  Leaf,
  CheckCircle2,
  Clock,
  Target
} from 'lucide-react'

interface TrialStats {
  entries: number
  locations: number
  traits: number
  observations: number
  completionRate: number
}

export function TrialSummary() {
  const [selectedTrial, setSelectedTrial] = useState('trial-1')

  const stats: TrialStats = {
    entries: 256,
    locations: 4,
    traits: 12,
    observations: 12288,
    completionRate: 87
  }

  const topPerformers = [
    { rank: 1, name: 'BM-2025-045', yield: 7.2, change: '+15.2%' },
    { rank: 2, name: 'BM-2025-023', yield: 6.9, change: '+10.4%' },
    { rank: 3, name: 'BM-2025-089', yield: 6.7, change: '+7.2%' },
    { rank: 4, name: 'BM-2025-012', yield: 6.5, change: '+4.0%' },
    { rank: 5, name: 'BM-2025-067', yield: 6.4, change: '+2.4%' }
  ]

  const traitSummary = [
    { trait: 'Grain Yield', mean: 5.8, cv: 12.4, lsd: 0.45, fValue: 8.7 },
    { trait: 'Plant Height', mean: 98, cv: 8.2, lsd: 5.2, fValue: 15.3 },
    { trait: 'Days to Maturity', mean: 122, cv: 4.5, lsd: 3.1, fValue: 22.1 },
    { trait: 'Disease Score', mean: 3.2, cv: 28.6, lsd: 0.8, fValue: 5.4 }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <FileText className="h-8 w-8 text-primary" />
            Trial Summary
          </h1>
          <p className="text-muted-foreground mt-1">Comprehensive trial analysis and reporting</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedTrial} onValueChange={setSelectedTrial}>
            <SelectTrigger className="w-[250px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="trial-1">Yield Trial Spring 2025</SelectItem>
              <SelectItem value="trial-2">Disease Screening 2025</SelectItem>
              <SelectItem value="trial-3">Multi-location Trial 2024</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export Report</Button>
        </div>
      </div>

      {/* Trial Info */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold">Yield Trial Spring 2025</h2>
              <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                <span className="flex items-center gap-1"><Calendar className="h-4 w-4" />Jan 15 - Jun 30, 2025</span>
                <span className="flex items-center gap-1"><MapPin className="h-4 w-4" />4 locations</span>
                <span className="flex items-center gap-1"><Users className="h-4 w-4" />Dr. Sarah Johnson</span>
              </div>
            </div>
            <Badge variant="default" className="text-lg py-1 px-3">
              <CheckCircle2 className="h-4 w-4 mr-2" />{stats.completionRate}% Complete
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <Leaf className="h-8 w-8 mx-auto text-green-600 mb-2" />
            <div className="text-2xl font-bold">{stats.entries}</div>
            <div className="text-sm text-muted-foreground">Entries</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <MapPin className="h-8 w-8 mx-auto text-blue-600 mb-2" />
            <div className="text-2xl font-bold">{stats.locations}</div>
            <div className="text-sm text-muted-foreground">Locations</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Target className="h-8 w-8 mx-auto text-purple-600 mb-2" />
            <div className="text-2xl font-bold">{stats.traits}</div>
            <div className="text-sm text-muted-foreground">Traits</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <BarChart3 className="h-8 w-8 mx-auto text-orange-600 mb-2" />
            <div className="text-2xl font-bold">{stats.observations.toLocaleString()}</div>
            <div className="text-sm text-muted-foreground">Observations</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Clock className="h-8 w-8 mx-auto text-pink-600 mb-2" />
            <div className="text-2xl font-bold">{stats.completionRate}%</div>
            <div className="text-sm text-muted-foreground">Complete</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList>
          <TabsTrigger value="performance">Top Performers</TabsTrigger>
          <TabsTrigger value="traits">Trait Summary</TabsTrigger>
          <TabsTrigger value="locations">By Location</TabsTrigger>
        </TabsList>

        <TabsContent value="performance">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><TrendingUp className="h-5 w-5" />Top Performing Entries</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {topPerformers.map((entry) => (
                  <div key={entry.rank} className="flex items-center gap-4 p-4 border rounded-lg">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${entry.rank === 1 ? 'bg-yellow-100 text-yellow-700' : entry.rank === 2 ? 'bg-gray-100 text-gray-700' : entry.rank === 3 ? 'bg-orange-100 text-orange-700' : 'bg-muted'}`}>
                      #{entry.rank}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">{entry.name}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold">{entry.yield} t/ha</div>
                      <div className="text-sm text-green-600">{entry.change}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="traits">
          <Card>
            <CardHeader>
              <CardTitle>Trait Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-3">Trait</th>
                    <th className="text-right p-3">Mean</th>
                    <th className="text-right p-3">CV (%)</th>
                    <th className="text-right p-3">LSD (5%)</th>
                    <th className="text-right p-3">F-value</th>
                  </tr>
                </thead>
                <tbody>
                  {traitSummary.map((trait, i) => (
                    <tr key={i} className="border-b hover:bg-muted/50">
                      <td className="p-3 font-medium">{trait.trait}</td>
                      <td className="p-3 text-right">{trait.mean}</td>
                      <td className="p-3 text-right">{trait.cv}</td>
                      <td className="p-3 text-right">{trait.lsd}</td>
                      <td className="p-3 text-right">{trait.fValue}**</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="locations">
          <Card>
            <CardHeader>
              <CardTitle>Performance by Location</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                {['IRRI Los Baños', 'CIMMYT El Batán', 'ICRISAT Patancheru', 'AfricaRice Ibadan'].map((loc, i) => (
                  <div key={i} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">{loc}</h4>
                      <Badge variant="outline">64 entries</Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div><span className="text-muted-foreground">Mean Yield:</span> <span className="font-bold">{(5.2 + i * 0.3).toFixed(1)} t/ha</span></div>
                      <div><span className="text-muted-foreground">CV:</span> <span className="font-bold">{(12 - i).toFixed(1)}%</span></div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
