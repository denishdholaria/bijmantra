import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  DollarSign, TrendingUp, TrendingDown, PieChart,
  BarChart3, Download, Calculator
} from 'lucide-react'

interface CostItem {
  id: string
  category: string
  description: string
  amount: number
  date: string
  project: string
}

interface BudgetCategory {
  name: string
  allocated: number
  spent: number
  color: string
}

export function CostAnalysis() {
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedPeriod, setSelectedPeriod] = useState('month')
  const [_selectedProject, _setSelectedProject] = useState('all')

  const budgetCategories: BudgetCategory[] = [
    { name: 'Labor', allocated: 50000, spent: 42500, color: 'bg-blue-500' },
    { name: 'Supplies', allocated: 25000, spent: 18200, color: 'bg-green-500' },
    { name: 'Equipment', allocated: 30000, spent: 28500, color: 'bg-orange-500' },
    { name: 'Genotyping', allocated: 40000, spent: 35000, color: 'bg-purple-500' },
    { name: 'Field Operations', allocated: 35000, spent: 31200, color: 'bg-cyan-500' },
  ]

  const recentCosts: CostItem[] = [
    { id: '1', category: 'Genotyping', description: 'SNP array analysis - 500 samples', amount: 12500, date: '2025-12-01', project: 'Rice Yield Trial' },
    { id: '2', category: 'Labor', description: 'Field technician wages - November', amount: 8500, date: '2025-11-30', project: 'All Projects' },
    { id: '3', category: 'Supplies', description: 'Fertilizer and pesticides', amount: 3200, date: '2025-11-28', project: 'Wheat Breeding' },
    { id: '4', category: 'Equipment', description: 'Drone maintenance', amount: 1500, date: '2025-11-25', project: 'Field Operations' },
    { id: '5', category: 'Field Operations', description: 'Irrigation system repair', amount: 2800, date: '2025-11-22', project: 'Rice Yield Trial' },
  ]

  const totalAllocated = budgetCategories.reduce((sum, c) => sum + c.allocated, 0)
  const totalSpent = budgetCategories.reduce((sum, c) => sum + c.spent, 0)
  const remaining = totalAllocated - totalSpent
  const utilizationRate = Math.round((totalSpent / totalAllocated) * 100)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Cost Analysis</h1>
          <p className="text-muted-foreground">Track and analyze breeding program expenses</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-[150px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="week">This Week</SelectItem>
              <SelectItem value="month">This Month</SelectItem>
              <SelectItem value="quarter">This Quarter</SelectItem>
              <SelectItem value="year">This Year</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline"><Download className="mr-2 h-4 w-4" />Export</Button>
          <Button><Calculator className="mr-2 h-4 w-4" />Add Expense</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Budget</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${totalAllocated.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Allocated for FY2025</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Spent</CardTitle>
            <TrendingUp className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${totalSpent.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">{utilizationRate}% utilized</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Remaining</CardTitle>
            <TrendingDown className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${remaining.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">{100 - utilizationRate}% available</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cost/Entry</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$42.50</div>
            <p className="text-xs text-muted-foreground">Average per germplasm</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview"><PieChart className="mr-2 h-4 w-4" />Overview</TabsTrigger>
          <TabsTrigger value="expenses"><DollarSign className="mr-2 h-4 w-4" />Expenses</TabsTrigger>
          <TabsTrigger value="budget"><BarChart3 className="mr-2 h-4 w-4" />Budget</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Budget by Category</CardTitle><CardDescription>Allocation vs spending</CardDescription></CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {budgetCategories.map((cat) => {
                    const percentage = Math.round((cat.spent / cat.allocated) * 100)
                    return (
                      <div key={cat.name} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium">{cat.name}</span>
                          <span className="text-muted-foreground">${cat.spent.toLocaleString()} / ${cat.allocated.toLocaleString()}</span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div className={`h-full ${cat.color} rounded-full`} style={{ width: `${percentage}%` }} />
                        </div>
                        <p className="text-xs text-muted-foreground text-right">{percentage}% used</p>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Recent Expenses</CardTitle><CardDescription>Latest transactions</CardDescription></CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentCosts.map((cost) => (
                    <div key={cost.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium text-sm">{cost.description}</p>
                        <p className="text-xs text-muted-foreground">{cost.project} • {cost.date}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">${cost.amount.toLocaleString()}</p>
                        <Badge variant="outline" className="text-xs">{cost.category}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="expenses"><Card><CardContent className="pt-6"><p className="text-muted-foreground">Detailed expense tracking</p></CardContent></Card></TabsContent>
        <TabsContent value="budget"><Card><CardContent className="pt-6"><p className="text-muted-foreground">Budget planning and forecasting</p></CardContent></Card></TabsContent>
      </Tabs>
    </div>
  )
}
