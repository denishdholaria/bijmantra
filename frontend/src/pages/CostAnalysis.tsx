import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  DollarSign, TrendingUp, TrendingDown, PieChart,
  BarChart3, Download, Calculator, Loader2, RefreshCw
} from 'lucide-react'

// Interfaces
interface BudgetCategory {
  id: number
  name: string
  allocated: number
  spent: number
  color: string
  year: number
}

interface Expense {
  id: number
  budget_category_id: number
  category_name?: string
  description: string
  amount: number
  date: string
  project?: string
}

interface CostAnalysisSummary {
  total_budget: number
  total_spent: number
  remaining: number
  utilization_rate: number
}

export function CostAnalysis() {
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedPeriod, setSelectedPeriod] = useState('month')
  const [_selectedProject, _setSelectedProject] = useState('all')

  const { data: summary, isLoading: loadingSummary, refetch: refetchSummary } = useQuery<CostAnalysisSummary>({
    queryKey: ['cost-analysis', 'summary'],
    queryFn: () => apiClient.get('/api/v2/cost-analysis/summary'),
  })

  const { data: categories, isLoading: loadingCategories, refetch: refetchCategories } = useQuery<BudgetCategory[]>({
    queryKey: ['cost-analysis', 'categories'],
    queryFn: () => apiClient.get('/api/v2/cost-analysis/budget-categories'),
  })

  const { data: expenses, isLoading: loadingExpenses, refetch: refetchExpenses } = useQuery<Expense[]>({
    queryKey: ['cost-analysis', 'expenses'],
    queryFn: () => apiClient.get('/api/v2/cost-analysis/expenses'),
  })

  const refreshData = () => {
    refetchSummary()
    refetchCategories()
    refetchExpenses()
  }

  if (loadingSummary || loadingCategories || loadingExpenses) {
      return <div className="flex h-[50vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
  }

  const budgetCategories = categories || []
  const recentCosts = expenses || []

  // Fallback if API returns empty (for demo/mock purposes, or just show 0)
  // But wait, the previous code had mock data. If the API returns empty, the UI will look empty.
  // Ideally I should seed data, but that's out of scope.
  // I'll stick to displaying what the API returns.

  const totalAllocated = summary?.total_budget || 0
  const totalSpent = summary?.total_spent || 0
  const remaining = summary?.remaining || 0
  const utilizationRate = summary?.utilization_rate ? Math.round(summary.utilization_rate) : 0

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Cost Analysis</h1>
          <p className="text-muted-foreground">Track and analyze breeding program expenses</p>
        </div>
        <div className="flex gap-2">
           <Button variant="outline" size="icon" onClick={refreshData} title="Refresh Data">
            <RefreshCw className="h-4 w-4" />
          </Button>
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
            <p className="text-xs text-muted-foreground">{Math.max(0, 100 - utilizationRate)}% available</p>
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
                  {budgetCategories.length > 0 ? (
                    budgetCategories.map((cat) => {
                      const percentage = cat.allocated > 0 ? Math.round((cat.spent / cat.allocated) * 100) : 0
                      return (
                        <div key={cat.id} className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="font-medium">{cat.name}</span>
                            <span className="text-muted-foreground">${cat.spent.toLocaleString()} / ${cat.allocated.toLocaleString()}</span>
                          </div>
                          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div className={`h-full ${cat.color} rounded-full`} style={{ width: `${Math.min(percentage, 100)}%` }} />
                          </div>
                          <p className="text-xs text-muted-foreground text-right">{percentage}% used</p>
                        </div>
                      )
                    })
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">No budget categories defined</div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Recent Expenses</CardTitle><CardDescription>Latest transactions</CardDescription></CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentCosts.length > 0 ? (
                    recentCosts.map((cost) => (
                      <div key={cost.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <p className="font-medium text-sm">{cost.description}</p>
                          <p className="text-xs text-muted-foreground">{cost.project || 'General'} • {new Date(cost.date).toLocaleDateString()}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">${cost.amount.toLocaleString()}</p>
                          <Badge variant="outline" className="text-xs">{cost.category_name || 'Uncategorized'}</Badge>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">No expenses recorded</div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="expenses"><Card><CardContent className="pt-6"><p className="text-muted-foreground">Detailed expense tracking coming soon</p></CardContent></Card></TabsContent>
        <TabsContent value="budget"><Card><CardContent className="pt-6"><p className="text-muted-foreground">Budget planning and forecasting coming soon</p></CardContent></Card></TabsContent>
      </Tabs>
    </div>
  )
}
