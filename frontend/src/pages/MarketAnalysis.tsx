import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  TrendingUp, TrendingDown, DollarSign, Globe,
  BarChart3, PieChart, Users, Wheat, Download
} from 'lucide-react'

interface MarketData {
  crop: string
  region: string
  price: number
  change: number
  demand: 'high' | 'medium' | 'low'
  trend: 'up' | 'down' | 'stable'
}

interface TraitDemand {
  trait: string
  demand: number
  growth: number
  regions: string[]
}

export function MarketAnalysis() {
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedCrop, setSelectedCrop] = useState('all')
  const [selectedRegion, setSelectedRegion] = useState('all')

  const marketData: MarketData[] = [
    { crop: 'Rice', region: 'South Asia', price: 450, change: 5.2, demand: 'high', trend: 'up' },
    { crop: 'Rice', region: 'Southeast Asia', price: 420, change: 3.1, demand: 'high', trend: 'up' },
    { crop: 'Wheat', region: 'South Asia', price: 380, change: -2.5, demand: 'medium', trend: 'down' },
    { crop: 'Wheat', region: 'Europe', price: 410, change: 1.8, demand: 'medium', trend: 'stable' },
    { crop: 'Maize', region: 'Africa', price: 320, change: 8.5, demand: 'high', trend: 'up' },
    { crop: 'Maize', region: 'Americas', price: 290, change: -1.2, demand: 'medium', trend: 'stable' },
  ]

  const traitDemands: TraitDemand[] = [
    { trait: 'Drought Tolerance', demand: 92, growth: 15, regions: ['South Asia', 'Africa', 'Australia'] },
    { trait: 'Disease Resistance', demand: 88, growth: 12, regions: ['Southeast Asia', 'Americas'] },
    { trait: 'High Yield', demand: 95, growth: 8, regions: ['Global'] },
    { trait: 'Short Duration', demand: 78, growth: 20, regions: ['South Asia', 'Africa'] },
    { trait: 'Premium Quality', demand: 72, growth: 18, regions: ['Japan', 'Europe', 'Middle East'] },
    { trait: 'Heat Tolerance', demand: 85, growth: 25, regions: ['South Asia', 'Africa', 'Middle East'] },
  ]

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'down': return <TrendingDown className="h-4 w-4 text-red-500" />
      default: return <span className="h-4 w-4 text-gray-400">—</span>
    }
  }

  const getDemandColor = (demand: string) => {
    const colors: Record<string, string> = { high: 'bg-green-100 text-green-800', medium: 'bg-yellow-100 text-yellow-800', low: 'bg-gray-100 text-gray-800' }
    return colors[demand] || 'bg-gray-100 text-gray-800'
  }

  const filteredData = marketData.filter(d => 
    (selectedCrop === 'all' || d.crop === selectedCrop) &&
    (selectedRegion === 'all' || d.region === selectedRegion)
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Market Analysis</h1>
          <p className="text-muted-foreground">Understand market trends and trait demands</p>
        </div>
        <Button variant="outline"><Download className="mr-2 h-4 w-4" />Export Report</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Price</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${Math.round(marketData.reduce((s, d) => s + d.price, 0) / marketData.length)}/ton</div>
            <p className="text-xs text-muted-foreground flex items-center gap-1"><TrendingUp className="h-3 w-3 text-green-500" />+3.2% this month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Demand</CardTitle>
            <BarChart3 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{marketData.filter(d => d.demand === 'high').length}</div>
            <p className="text-xs text-muted-foreground">Markets with high demand</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Top Trait</CardTitle>
            <Wheat className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">High Yield</div>
            <p className="text-xs text-muted-foreground">95% demand score</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Regions</CardTitle>
            <Globe className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{new Set(marketData.map(d => d.region)).size}</div>
            <p className="text-xs text-muted-foreground">Active markets</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex gap-4">
        <Select value={selectedCrop} onValueChange={setSelectedCrop}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Crop" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Crops</SelectItem>
            <SelectItem value="Rice">Rice</SelectItem>
            <SelectItem value="Wheat">Wheat</SelectItem>
            <SelectItem value="Maize">Maize</SelectItem>
          </SelectContent>
        </Select>
        <Select value={selectedRegion} onValueChange={setSelectedRegion}>
          <SelectTrigger className="w-[180px]"><SelectValue placeholder="Region" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Regions</SelectItem>
            {[...new Set(marketData.map(d => d.region))].map(r => (<SelectItem key={r} value={r}>{r}</SelectItem>))}
          </SelectContent>
        </Select>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview"><BarChart3 className="mr-2 h-4 w-4" />Market Overview</TabsTrigger>
          <TabsTrigger value="traits"><Wheat className="mr-2 h-4 w-4" />Trait Demands</TabsTrigger>
          <TabsTrigger value="trends"><TrendingUp className="mr-2 h-4 w-4" />Trends</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Market Prices</CardTitle><CardDescription>Current prices by crop and region</CardDescription></CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredData.map((data, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center"><Wheat className="h-5 w-5 text-primary" /></div>
                      <div>
                        <p className="font-medium">{data.crop}</p>
                        <p className="text-sm text-muted-foreground">{data.region}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="font-medium">${data.price}/ton</p>
                        <p className={`text-sm flex items-center gap-1 ${data.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {getTrendIcon(data.trend)}{data.change >= 0 ? '+' : ''}{data.change}%
                        </p>
                      </div>
                      <Badge className={getDemandColor(data.demand)}>{data.demand} demand</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="traits" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {traitDemands.map((trait) => (
              <Card key={trait.trait}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{trait.trait}</CardTitle>
                    <Badge variant="outline">+{trait.growth}% growth</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm"><span>Demand Score</span><span className="font-medium">{trait.demand}%</span></div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden"><div className="h-full bg-primary rounded-full" style={{ width: `${trait.demand}%` }} /></div>
                    <div className="flex gap-1 flex-wrap">{trait.regions.map(r => (<Badge key={r} variant="secondary" className="text-xs">{r}</Badge>))}</div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="trends"><Card><CardContent className="pt-6"><p className="text-muted-foreground">Historical trends and forecasts</p></CardContent></Card></TabsContent>
      </Tabs>
    </div>
  )
}
