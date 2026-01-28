/**
 * Fertilizer Calculator Page
 * Calculate fertilizer requirements based on soil tests and crop needs
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from 'sonner'

interface FertilizerResult {
  nitrogen: number
  phosphorus: number
  potassium: number
  urea: number
  dap: number
  mop: number
  totalCost: number
}

const cropRequirements: Record<string, { N: number; P: number; K: number }> = {
  wheat: { N: 120, P: 60, K: 40 },
  rice: { N: 100, P: 50, K: 50 },
  maize: { N: 150, P: 75, K: 60 },
  soybean: { N: 30, P: 60, K: 40 },
  cotton: { N: 120, P: 60, K: 60 },
}

const fertilizerPrices = {
  urea: 350, // per 50kg bag
  dap: 1350,
  mop: 850,
}

export function FertilizerCalculator() {
  const [crop, setCrop] = useState('wheat')
  const [area, setArea] = useState(1)
  const [soilN, setSoilN] = useState(40)
  const [soilP, setSoilP] = useState(25)
  const [soilK, setSoilK] = useState(150)
  const [targetYield, setTargetYield] = useState(5)
  const [result, setResult] = useState<FertilizerResult | null>(null)

  const calculate = () => {
    const req = cropRequirements[crop]
    if (!req) return

    // Adjust for target yield (base is 4 t/ha)
    const yieldFactor = targetYield / 4

    // Calculate nutrient requirements minus soil supply
    const nNeeded = Math.max(0, (req.N * yieldFactor) - soilN)
    const pNeeded = Math.max(0, (req.P * yieldFactor) - (soilP * 2.29)) // Convert P to P2O5
    const kNeeded = Math.max(0, (req.K * yieldFactor) - (soilK * 0.12)) // Convert K to K2O

    // Calculate fertilizer amounts (kg/ha)
    const urea = (nNeeded / 0.46) * area // Urea is 46% N
    const dap = (pNeeded / 0.46) * area // DAP is 46% P2O5
    const mop = (kNeeded / 0.60) * area // MOP is 60% K2O

    // Calculate cost
    const totalCost = (urea / 50) * fertilizerPrices.urea +
                      (dap / 50) * fertilizerPrices.dap +
                      (mop / 50) * fertilizerPrices.mop

    setResult({
      nitrogen: nNeeded * area,
      phosphorus: pNeeded * area,
      potassium: kNeeded * area,
      urea: Math.round(urea),
      dap: Math.round(dap),
      mop: Math.round(mop),
      totalCost: Math.round(totalCost),
    })

    toast.success('Fertilizer requirements calculated')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Fertilizer Calculator</h1>
          <p className="text-muted-foreground mt-1">Calculate fertilizer requirements</p>
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
                    <SelectItem value="wheat">Wheat</SelectItem>
                    <SelectItem value="rice">Rice</SelectItem>
                    <SelectItem value="maize">Maize</SelectItem>
                    <SelectItem value="soybean">Soybean</SelectItem>
                    <SelectItem value="cotton">Cotton</SelectItem>
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

            <Button onClick={calculate} className="w-full">🧮 Calculate</Button>
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
