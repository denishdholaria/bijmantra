
import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2, Calculator } from 'lucide-react'
import { mixedModelApi, MixedModelSolution } from '@/api/mixed_model'
import { toast } from 'sonner'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

export default function MixedModelTool() {
  const [loading, setLoading] = useState(false)
  const [formula, setFormula] = useState('yield ~ location + (1|genotype)')
  const [result, setResult] = useState<MixedModelSolution | null>(null)

  const runDemo = async () => {
    setLoading(true)
    try {
      // Create small demo dataset
      // 3 locations, 5 genotypes, 2 reps = 30 obs
      const locs = []
      const genos = []
      const yields = []
      
      for (let l=1; l<=3; l++) {
        for (let g=1; g<=5; g++) {
             for (let r=1; r<=2; r++) {
                 locs.push(`Loc${l}`)
                 genos.push(`Geno${g}`)
                 // Random yield: Loc effect + Geno effect + noise
                 const y = 100 + (l*10) + (g*5) + Math.random()*5
                 yields.push(y)
             }
        }
      }
      
      const data = {
         formula: formula,
         data_dict: {
            "location": locs,
            "genotype": genos,
            "yield": yields
         }
      }
      
      const solution = await mixedModelApi.solveMixedModel(data)
      setResult(solution)
      toast.success("Model Solved")
    } catch (error: any) {
      console.error(error)
      toast.error("Solver Failed: " + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Mixed Model Analysis</h1>
          <p className="text-muted-foreground">BLUEs and BLUPs estimation using Henderson's Mixed Model Equations</p>
        </div>
        <Button onClick={runDemo} disabled={loading}>
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Calculator className="mr-2 h-4 w-4" />}
          Solve (Demo Data)
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Model Specification</CardTitle>
            <CardDescription>Wilkinson Notation</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Formula</Label>
              <Input 
                value={formula} 
                onChange={(e) => setFormula(e.target.value)} 
                placeholder="y ~ fixed + (1|random)"
              />
              <p className="text-xs text-muted-foreground">
                Example: yield ~ location + year + (1|genotype)
              </p>
            </div>
            
            <div className="p-4 bg-muted rounded-md text-sm">
               <h4 className="font-semibold mb-2">Dataset Info (Demo)</h4>
               <ul className="list-disc pl-4 space-y-1">
                 <li>Locations: 3</li>
                 <li>Genotypes: 5</li>
                 <li>Replications: 2</li>
                 <li>Total Obs: 30</li>
               </ul>
            </div>
          </CardContent>
        </Card>

        <div className="col-span-2 space-y-6">
           {result ? (
             <>
               <Card>
                 <CardHeader>
                   <CardTitle>Variance Components</CardTitle>
                 </CardHeader>
                 <CardContent>
                   <Table>
                     <TableHeader>
                       <TableRow>
                         <TableHead>Component</TableHead>
                         <TableHead className="text-right">Estimate</TableHead>
                       </TableRow>
                     </TableHeader>
                     <TableBody>
                        <TableRow>
                           <TableCell>Residual (Error)</TableCell>
                           {/* In our simple solver, we usually pass fixed variances or estimate.
                               If `solveMixedModel` returned estimates, show them.
                               Our mock solver might just return effects if using fixed variance.
                               Let's check `MixedModelSolution` interface. It has fixed/random effects.
                               Variance components might be in separate call for REML.
                               For this demo, we assume solver used defaults or provided specific return.
                               Actually interface has `aic`, `bic`.
                            */}
                           <TableCell className="text-right">-</TableCell>
                        </TableRow>
                     </TableBody>
                   </Table>
                   <p className="mt-4 text-sm text-muted-foreground">
                      * Note: This demo uses the BLUE/BLUP solver with fixed variance priors. For variance estimation, use the REML tool.
                   </p>
                 </CardContent>
               </Card>

               <Card>
                 <CardHeader>
                   <CardTitle>Fixed Effects (BLUEs)</CardTitle>
                 </CardHeader>
                 <CardContent max-h="300px" className="overflow-auto">
                    <Table>
                       <TableHeader>
                          <TableRow>
                             <TableHead>Level</TableHead>
                             <TableHead className="text-right">Value</TableHead>
                          </TableRow>
                       </TableHeader>
                       <TableBody>
                          {Object.entries(result.fixed_effects).map(([k, v]) => (
                             <TableRow key={k}>
                                <TableCell>{k}</TableCell>
                                <TableCell className="text-right">{v.toFixed(4)}</TableCell>
                             </TableRow>
                          ))}
                       </TableBody>
                    </Table>
                 </CardContent>
               </Card>

               <Card>
                 <CardHeader>
                   <CardTitle>Random Effects (BLUPs)</CardTitle>
                 </CardHeader>
                 <CardContent max-h="300px" className="overflow-auto">
                    <Table>
                       <TableHeader>
                          <TableRow>
                             <TableHead>Level</TableHead>
                             <TableHead className="text-right">Value</TableHead>
                          </TableRow>
                       </TableHeader>
                       <TableBody>
                          {Object.entries(result.random_effects).map(([k, v]) => (
                             <TableRow key={k}>
                                <TableCell>{k}</TableCell>
                                <TableCell className="text-right">{v.toFixed(4)}</TableCell>
                             </TableRow>
                          ))}
                       </TableBody>
                    </Table>
                 </CardContent>
               </Card>
             </>
           ) : (
             <div className="h-full flex items-center justify-center border-2 border-dashed rounded-lg text-muted-foreground p-12">
                Click "Solve (Demo Data)" to run analysis
             </div>
           )}
        </div>
      </div>
    </div>
  )
}
