/**
 * Allele Matrix Page - BrAPI Genotyping Module
 * Visual matrix of genotypes across samples and variants
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'

interface MatrixData {
  callSetDbIds: string[]
  variantDbIds: string[]
  dataMatrices: Array<{
    dataMatrix: string[][]
    dataMatrixAbbreviation: string
    dataMatrixName: string
    dataType: string
  }>
}

// Mock matrix data
const mockMatrix: MatrixData = {
  callSetDbIds: ['Sample_001', 'Sample_002', 'Sample_003', 'Sample_004', 'Sample_005'],
  variantDbIds: ['SNP_Chr1_12345', 'SNP_Chr1_23456', 'INDEL_Chr2_5678', 'SNP_Chr3_78901', 'MNP_Chr4_11111'],
  dataMatrices: [{
    dataMatrix: [
      ['0/1', '1/1', '0/0', '0/1', '0/0'],
      ['0/0', '0/1', '0/1', '1/1', '0/0'],
      ['1/1', '0/0', '0/1', '0/0', '0/1'],
      ['0/1', '0/1', '0/0', '0/1', '1/1'],
      ['0/0', '1/1', '1/1', '0/0', '0/1'],
    ],
    dataMatrixAbbreviation: 'GT',
    dataMatrixName: 'Genotype',
    dataType: 'string',
  }],
}

export function AlleleMatrix() {
  const [variantSet, setVariantSet] = useState<string>('all')

  const { data, isLoading } = useQuery({
    queryKey: ['alleleMatrix', variantSet],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 600))
      return mockMatrix
    },
  })

  const getGenotypeColor = (gt: string) => {
    if (gt === '0/0') return 'bg-green-500'
    if (gt === '1/1') return 'bg-red-500'
    if (gt === '0/1' || gt === '1/0') return 'bg-yellow-500'
    if (gt === './.') return 'bg-gray-300'
    return 'bg-blue-500'
  }

  const getGenotypeLabel = (gt: string) => {
    if (gt === '0/0') return 'Ref'
    if (gt === '1/1') return 'Alt'
    if (gt === '0/1' || gt === '1/0') return 'Het'
    if (gt === './.') return 'NA'
    return gt
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Allele Matrix</h1>
          <p className="text-muted-foreground mt-1">Genotype matrix visualization</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => toast.success('Export started (demo)')}>
            📥 Export TSV
          </Button>
          <Button variant="outline" onClick={() => toast.success('Export started (demo)')}>
            📥 Export VCF
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <div className="space-y-1">
              <label className="text-sm font-medium">Variant Set</label>
              <Select value={variantSet} onValueChange={setVariantSet}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Select variant set" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Variants</SelectItem>
                  <SelectItem value="snps">SNPs Only</SelectItem>
                  <SelectItem value="indels">InDels Only</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-green-500"></div>
                <span>Ref (0/0)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-yellow-500"></div>
                <span>Het (0/1)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-red-500"></div>
                <span>Alt (1/1)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-gray-300"></div>
                <span>Missing</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Genotype Matrix</CardTitle>
            <CardDescription>
              {data?.callSetDbIds.length} samples × {data?.variantDbIds.length} variants
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className="p-2 text-left font-medium border-b sticky left-0 bg-background">Sample</th>
                    {data?.variantDbIds.map((variant) => (
                      <th key={variant} className="p-2 text-center font-medium border-b text-xs">
                        <div className="transform -rotate-45 origin-center whitespace-nowrap">
                          {variant}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data?.callSetDbIds.map((sample, sampleIdx) => (
                    <tr key={sample} className="hover:bg-muted/50">
                      <td className="p-2 font-medium border-b sticky left-0 bg-background">
                        {sample}
                      </td>
                      {data?.dataMatrices[0].dataMatrix[sampleIdx].map((gt, variantIdx) => (
                        <td key={variantIdx} className="p-1 border-b text-center">
                          <div
                            className={`w-8 h-8 rounded flex items-center justify-center text-white text-xs font-bold mx-auto cursor-pointer hover:opacity-80 ${getGenotypeColor(gt)}`}
                            title={`${sample} @ ${data?.variantDbIds[variantIdx]}: ${gt}`}
                          >
                            {getGenotypeLabel(gt)}
                          </div>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Summary Statistics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total Genotypes</span>
              <span className="font-medium">{(data?.callSetDbIds.length || 0) * (data?.variantDbIds.length || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Samples</span>
              <span className="font-medium">{data?.callSetDbIds.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Variants</span>
              <span className="font-medium">{data?.variantDbIds.length}</span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Genotype Distribution</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Homozygous Ref</span>
              <Badge className="bg-green-100 text-green-800">40%</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Heterozygous</span>
              <Badge className="bg-yellow-100 text-yellow-800">36%</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Homozygous Alt</span>
              <Badge className="bg-red-100 text-red-800">24%</Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Data Quality</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Call Rate</span>
              <span className="font-medium">98.5%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Avg Depth</span>
              <span className="font-medium">42x</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Avg Quality</span>
              <span className="font-medium">96.2</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
