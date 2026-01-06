import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
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
import { trialSummaryAPI, TrialInfo, TopPerformer, TraitSummaryItem, LocationPerformance } from '@/lib/api-client'

export function TrialSummary() {
  const [selectedTrial, setSelectedTrial] = useState('trial-1')

  // Fetch trials list
  const { data: trialsData, isLoading: trialsLoading } = useQuery({
    queryKey: ['trial-summary-trials'],
    queryFn: () => trialSummaryAPI.getTrials(),
  })

  const trials = trialsData?.data || []

  // Fetch summary for selected trial
  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ['trial-summary', selectedTrial],
    queryFn: () => trialSummaryAPI.getSummary(selectedTrial),
    enabled: !!selectedTrial,
  })

  const trial = summaryData?.trial
  const topPerformers = summaryData?.topPerformers || []
  const traitSummary = summaryData?.traitSummary || []
  const locationPerformance = summaryData?.locationPerformance || []
  const statistics = summaryData?.statistics

  const handleExport = async () => {
    try {
      const result = await trialSummaryAPI.exportSummary(selectedTrial, 'pdf')
      toast.success(result.message)
    } catch {
      toast.error('Export failed')
    }
  }

  if (trialsLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

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
              {trials.map((t: TrialInfo) => (
                <SelectItem key={t.trialDbId} value={t.trialDbId}>{t.trialName}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />Export Report
          </Button>
        </div>
      </div>

      {summaryLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : trial ? (
        <>
          {/* Trial Info */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold">{trial.trialName}</h2>
                  <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1"><Calendar className="h-4 w-4" />{trial.startDate} - {trial.endDate}</span>
                    <span className="flex items-center gap-1"><MapPin className="h-4 w-4" />{trial.locations} locations</span>
                    <span className="flex items-center gap-1"><Users className="h-4 w-4" />{trial.leadScientist}</span>
                  </div>
                </div>
                <Badge variant="default" className="text-lg py-1 px-3">
                  <CheckCircle2 className="h-4 w-4 mr-2" />{trial.completionRate}% Complete
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <Card>
              <CardContent className="p-4 text-center">
                <Leaf className="h-8 w-8 mx-auto text-green-600 mb-2" />
                <div className="text-2xl font-bold">{trial.entries}</div>
                <div className="text-sm text-muted-foreground">Entries</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <MapPin className="h-8 w-8 mx-auto text-blue-600 mb-2" />
                <div className="text-2xl font-bold">{trial.locations}</div>
                <div className="text-sm text-muted-foreground">Locations</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <Target className="h-8 w-8 mx-auto text-purple-600 mb-2" />
                <div className="text-2xl font-bold">{trial.traits}</div>
                <div className="text-sm text-muted-foreground">Traits</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <BarChart3 className="h-8 w-8 mx-auto text-orange-600 mb-2" />
                <div className="text-2xl font-bold">{trial.observations.toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">Observations</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <Clock className="h-8 w-8 mx-auto text-pink-600 mb-2" />
                <div className="text-2xl font-bold">{trial.completionRate}%</div>
                <div className="text-sm text-muted-foreground">Complete</div>
              </CardContent>
            </Card>
          </div>

          <Tabs defaultValue="performance" className="space-y-4">
            <TabsList>
              <TabsTrigger value="performance">Top Performers</TabsTrigger>
              <TabsTrigger value="traits">Trait Summary</TabsTrigger>
              <TabsTrigger value="locations">By Location</TabsTrigger>
              <TabsTrigger value="statistics">Statistics</TabsTrigger>
            </TabsList>

            <TabsContent value="performance">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><TrendingUp className="h-5 w-5" />Top Performing Entries</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {topPerformers.slice(0, 5).map((entry: TopPerformer) => (
                      <div key={entry.rank} className="flex items-center gap-4 p-4 border rounded-lg">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${entry.rank === 1 ? 'bg-yellow-100 text-yellow-700' : entry.rank === 2 ? 'bg-gray-100 text-gray-700' : entry.rank === 3 ? 'bg-orange-100 text-orange-700' : 'bg-muted'}`}>
                          #{entry.rank}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium">{entry.germplasmName}</div>
                          <div className="flex gap-1 mt-1">
                            {entry.traits.map((trait: string, ti: number) => (
                              <Badge key={ti} variant="secondary" className="text-xs">{trait}</Badge>
                            ))}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-xl font-bold">{entry.yield_value} t/ha</div>
                          <div className="text-sm text-green-600">{entry.change_percent}</div>
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
                        <th className="text-right p-3">Sig.</th>
                      </tr>
                    </thead>
                    <tbody>
                      {traitSummary.map((trait: TraitSummaryItem, i: number) => (
                        <tr key={i} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-medium">{trait.trait}</td>
                          <td className="p-3 text-right">{trait.mean}</td>
                          <td className="p-3 text-right">{trait.cv}</td>
                          <td className="p-3 text-right">{trait.lsd}</td>
                          <td className="p-3 text-right">{trait.fValue}</td>
                          <td className="p-3 text-right">{trait.significance}</td>
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
                    {locationPerformance.map((loc: LocationPerformance) => (
                      <div key={loc.locationDbId} className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium">{loc.locationName}</h4>
                          <Badge variant="outline">{loc.entries} entries</Badge>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div><span className="text-muted-foreground">Mean Yield:</span> <span className="font-bold">{loc.meanYield} t/ha</span></div>
                          <div><span className="text-muted-foreground">CV:</span> <span className="font-bold">{loc.cv}%</span></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="statistics">
              <Card>
                <CardHeader>
                  <CardTitle>Statistical Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  {statistics && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-4 border rounded-lg">
                        <div className="text-sm text-muted-foreground">Grand Mean</div>
                        <div className="text-2xl font-bold">{statistics.grand_mean}</div>
                      </div>
                      <div className="p-4 border rounded-lg">
                        <div className="text-sm text-muted-foreground">Overall CV</div>
                        <div className="text-2xl font-bold">{statistics.overall_cv}%</div>
                      </div>
                      <div className="p-4 border rounded-lg">
                        <div className="text-sm text-muted-foreground">Heritability</div>
                        <div className="text-2xl font-bold">{statistics.heritability}</div>
                      </div>
                      <div className="p-4 border rounded-lg">
                        <div className="text-sm text-muted-foreground">LSD (5%)</div>
                        <div className="text-2xl font-bold">{statistics.lsd_5_percent}</div>
                      </div>
                      <div className="p-4 border rounded-lg">
                        <div className="text-sm text-muted-foreground">Genetic Variance</div>
                        <div className="text-2xl font-bold">{statistics.genetic_variance}</div>
                      </div>
                      <div className="p-4 border rounded-lg">
                        <div className="text-sm text-muted-foreground">Error Variance</div>
                        <div className="text-2xl font-bold">{statistics.error_variance}</div>
                      </div>
                      <div className="p-4 border rounded-lg">
                        <div className="text-sm text-muted-foreground">Selection Intensity</div>
                        <div className="text-2xl font-bold">{statistics.selection_intensity}</div>
                      </div>
                      <div className="p-4 border rounded-lg">
                        <div className="text-sm text-muted-foreground">Expected Gain</div>
                        <div className="text-2xl font-bold">{statistics.expected_gain}%</div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">Select a trial to view its summary</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
