import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

interface FertilizerResult {
  nitrogen: number
  phosphorus: number
  potassium: number
  urea: number
  dap: number
  mop: number
  totalCost: number
}

export function FertilizerCalculator() {
  const [crop, setCrop] = useState('wheat')
  const [crops, setCrops] = useState<string[]>([])
  const [area, setArea] = useState(1)
  const [soilN, setSoilN] = useState(40)
  const [soilP, setSoilP] = useState(25)
  const [soilK, setSoilK] = useState(150)
  const [targetYield, setTargetYield] = useState(5)
  const [result, setResult] = useState<FertilizerResult | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const fetchCrops = async () => {
      try {
        const response = await apiClient.agronomyService.getSupportedCrops()
        setCrops(response.crops)
      } catch (error) {
        console.error('Failed to fetch crops:', error)
        // Fallback or just show error toast
        toast.error('Failed to load crop list')
      }
    }
    fetchCrops()
  }, [])

  const calculate = async () => {
    setLoading(true)
    try {
      const response = await apiClient.agronomyService.calculateFertilizer({
        crop,
        area,
        target_yield: targetYield,
        soil_n: soilN,
        soil_p: soilP,
        soil_k: soilK
      })

      setResult({
        nitrogen: response.nitrogen_needed,
        phosphorus: response.phosphorus_needed,
        potassium: response.potassium_needed,
        urea: response.urea,
        dap: response.dap,
        mop: response.mop,
        totalCost: response.total_cost
      })
      toast.success('Fertilizer requirements calculated')
    } catch (error) {
      console.error('Calculation failed:', error)
      toast.error('Failed to calculate fertilizer requirements')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Fertilizer Calculator</h1>
          <p className="text-muted-foreground mt-1">Calculate fertilizer requirements (Powered by Agronomy Engine)</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <Card>
          <CardHeader>
            <CardTitle>Input Parameters</CardTitle>
            <CardDescription>Enter crop and soil information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Crop</Label>
                <Select value={crop} onValueChange={setCrop}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {crops.length > 0 ? (
                      crops.map(c => (
                        <SelectItem key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</SelectItem>
                      ))
                    ) : (
                      <SelectItem value="wheat">Loading...</SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Area (ha)</Label>
                <Input type="number" value={area} onChange={(e) => setArea(parseFloat(e.target.value) || 0)} />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Target Yield (t/ha)</Label>
              <Input type="number" step="0.5" value={targetYield} onChange={(e) => setTargetYield(parseFloat(e.target.value) || 0)} />
            </div>

            <div className="p-4 bg-muted rounded-lg">
              <p className="font-medium mb-3">Soil Test Results (ppm)</p>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Nitrogen</Label>
                  <Input type="number" value={soilN} onChange={(e) => setSoilN(parseFloat(e.target.value) || 0)} />
                </div>
                <div className="space-y-2">
                  <Label>Phosphorus</Label>
                  <Input type="number" value={soilP} onChange={(e) => setSoilP(parseFloat(e.target.value) || 0)} />
                </div>
                <div className="space-y-2">
                  <Label>Potassium</Label>
                  <Input type="number" value={soilK} onChange={(e) => setSoilK(parseFloat(e.target.value) || 0)} />
                </div>
              </div>
            </div>

            <Button onClick={calculate} className="w-full" disabled={loading}>
              {loading ? 'Calculating...' : '🧮 Calculate'}
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        <Card>
          <CardHeader>
            <CardTitle>Fertilizer Recommendation</CardTitle>
            <CardDescription>Based on soil test and crop requirements</CardDescription>
          </CardHeader>
          <CardContent>
            {!result ? (
              <div className="text-center py-12 text-muted-foreground">
                <span className="text-4xl">🌾</span>
                <p className="mt-2">Enter parameters and click Calculate</p>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg text-center">
                    <p className="text-2xl font-bold text-blue-700">{result.urea}</p>
                    <p className="text-sm text-blue-600">Urea (kg)</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg text-center">
                    <p className="text-2xl font-bold text-green-700">{result.dap}</p>
                    <p className="text-sm text-green-600">DAP (kg)</p>
                  </div>
                  <div className="p-4 bg-orange-50 rounded-lg text-center">
                    <p className="text-2xl font-bold text-orange-700">{result.mop}</p>
                    <p className="text-sm text-orange-600">MOP (kg)</p>
                  </div>
                </div>

                <div className="p-4 bg-purple-50 rounded-lg">
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-purple-700">Estimated Cost</span>
                    <span className="text-2xl font-bold text-purple-700">₹{result.totalCost.toLocaleString()}</span>
                  </div>
                </div>

                <div className="text-sm text-muted-foreground">
                  <p className="font-medium mb-2">Nutrient Requirements:</p>
                  <ul className="space-y-1">
                    <li>• Nitrogen (N): {result.nitrogen.toFixed(1)} kg</li>
                    <li>• Phosphorus (P₂O₅): {result.phosphorus.toFixed(1)} kg</li>
                    <li>• Potassium (K₂O): {result.potassium.toFixed(1)} kg</li>
                  </ul>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
