import React, { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { EChartsWrapper } from '@/components/charts/EChartsWrapper';
import { useTheme } from '@/hooks/useTheme';
import { Download, Filter, SortAsc, RefreshCw, BrainCircuit } from 'lucide-react';
import type { EChartsOption } from 'echarts';

/**
 * BrAPI v2.1 compliant GxE Matrix Heatmap
 *
 * Visualizes Genotype by Environment interactions using a heatmap.
 * Adheres to REEVU reasoning framework standards.
 */

/**
 * BrAPI v2.1 Observation Matrix simplified types
 */
export interface BrAPIObservationMatrix {
  dataMatrix: (number | string | null)[][]; // [observationUnitIndex][traitIndex]
  observationUnitDbIds: string[];
  observationUnitNames: string[];
  observationVariableDbIds: string[];
  observationVariableNames: string[];
  // Extended for GxE
  environmentNames?: string[];
  genotypeNames?: string[];
}

export interface GxEMatrixData {
  genotypes: string[];
  environments: string[];
  traits: {
    id: string;
    name: string;
    unit: string;
    values: (number | null)[][]; // [genotypeIndex][environmentIndex]
  }[];
}

/**
 * Generates mock GxE data for testing and demonstration
 */
export const generateMockGxEData = (numGenotypes = 10, numEnvs = 5): GxEMatrixData => {
  const genotypes = Array.from({ length: numGenotypes }, (_, i) => `Genotype-${101 + i}`);
  const environments = ['Kandahar', 'Helmand', 'Herat', 'Balkh', 'Nangarhar'].slice(0, numEnvs);

  const traitNames = [
    { name: 'Yield', unit: 't/ha', base: 5, variance: 2 },
    { name: 'Plant Height', unit: 'cm', base: 80, variance: 15 },
    { name: 'Protein Content', unit: '%', base: 12, variance: 3 },
  ];

  return {
    genotypes,
    environments,
    traits: traitNames.map((t, tIdx) => ({
      id: `trait-${tIdx}`,
      name: t.name,
      unit: t.unit,
      values: genotypes.map((_, gIdx) =>
        environments.map((_, eIdx) => {
          // Add some GxE pattern: certain genotypes perform better in certain envs
          const gEffect = (gIdx % 3) * 0.5;
          const eEffect = (eIdx % 2) * 0.3;
          const gxeEffect = (gIdx === eIdx) ? 1.2 : 0;
          const random = Math.random() * t.variance;
          return t.base + gEffect + eEffect + gxeEffect + random;
        })
      )
    }))
  };
};

export interface GxEMatrixHeatmapProps {
  data?: GxEMatrixData;
  isLoading?: boolean;
  title?: string;
  description?: string;
  onCellClick?: (genotype: string, environment: string, value: number | null) => void;
  className?: string;
}

export const GxEMatrixHeatmap: React.FC<GxEMatrixHeatmapProps> = ({
  data,
  isLoading = false,
  title = "GxE Interaction Matrix",
  description = "Genotype performance across different environments",
  onCellClick,
  className = "",
}) => {
  const { isDark } = useTheme();
  const [selectedTraitIndex, setSelectedTraitIndex] = useState(0);
  const [sortOrder, setSortOrder] = useState<'none' | 'genotype' | 'environment'>('none');

  // Sort logic
  const processedData = useMemo(() => {
    if (!data) return null;
    const { genotypes, environments, traits } = data;
    const currentTrait = traits[selectedTraitIndex];

    if (sortOrder === 'genotype') {
      // Sort genotypes by their mean value across environments for the current trait
      const gMeans = genotypes.map((_, gIdx) => {
        const row = currentTrait.values[gIdx];
        const validValues = row.filter((v): v is number => v !== null);
        return {
          index: gIdx,
          mean: validValues.length > 0 ? validValues.reduce((a, b) => a + b, 0) / validValues.length : -Infinity
        };
      });
      gMeans.sort((a, b) => b.mean - a.mean);

      const newGenotypes = gMeans.map(m => genotypes[m.index]);
      const newTraits = traits.map(t => ({
        ...t,
        values: gMeans.map(m => t.values[m.index])
      }));
      return { genotypes: newGenotypes, environments, traits: newTraits };
    }

    if (sortOrder === 'environment') {
      // Sort environments by their mean value across genotypes for the current trait
      const eMeans = environments.map((_, eIdx) => {
        const col = genotypes.map((_, gIdx) => currentTrait.values[gIdx][eIdx]);
        const validValues = col.filter((v): v is number => v !== null);
        return {
          index: eIdx,
          mean: validValues.length > 0 ? validValues.reduce((a, b) => a + b, 0) / validValues.length : -Infinity
        };
      });
      eMeans.sort((a, b) => b.mean - a.mean);

      const newEnvs = eMeans.map(m => environments[m.index]);
      const newTraits = traits.map(t => ({
        ...t,
        values: t.values.map(row => eMeans.map(m => row[m.index]))
      }));
      return { genotypes, environments: newEnvs, traits: newTraits };
    }

    return data;
  }, [data, selectedTraitIndex, sortOrder]);

  const trait = processedData?.traits[selectedTraitIndex];

  // Calculate min/max for the selected trait to scale the visualMap
  const [minVal, maxVal] = useMemo(() => {
    if (!trait) return [0, 100];
    const flatValues = trait.values.flat().filter((v): v is number => v !== null);
    if (flatValues.length === 0) return [0, 100];
    return [Math.min(...flatValues), Math.max(...flatValues)];
  }, [trait]);

  const chartOption: EChartsOption = useMemo(() => {
    if (!processedData || !trait) return {};

    const chartData: [number, number, number | null][] = [];
    trait.values.forEach((row, gIdx) => {
      row.forEach((val, eIdx) => {
        chartData.push([eIdx, gIdx, val]);
      });
    });

    return {
      backgroundColor: 'transparent',
      tooltip: {
        position: 'top',
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        formatter: (params: any) => {
          const [eIdx, gIdx, val] = params.data;
          return `
            <div class="font-sans">
              <div class="font-bold border-b border-gray-200 pb-1 mb-1">${processedData.genotypes[gIdx]}</div>
              <div class="text-xs text-muted-foreground">Env: ${processedData.environments[eIdx]}</div>
              <div class="text-sm mt-1">
                ${trait.name}: <span class="font-mono font-bold">${val !== null ? val.toFixed(2) : 'N/A'}</span> ${trait.unit}
              </div>
            </div>
          `;
        },
      },
      grid: {
        top: 40,
        bottom: 80,
        left: 120,
        right: 40,
      },
      xAxis: {
        type: 'category',
        data: processedData.environments,
        splitArea: { show: true },
        axisLabel: {
          rotate: 45,
          color: isDark ? '#9ca3af' : '#6b7280',
        },
      },
      yAxis: {
        type: 'category',
        data: processedData.genotypes,
        splitArea: { show: true },
        axisLabel: {
          color: isDark ? '#9ca3af' : '#6b7280',
        },
      },
      visualMap: {
        min: minVal,
        max: maxVal,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: 0,
        padding: [20, 0, 0, 0],
        inRange: {
          color: isDark
            ? ['#1e3a8a', '#1d4ed8', '#3b82f6', '#60a5fa', '#93c5fd', '#dbeafe']
            : ['#eff6ff', '#bfdbfe', '#60a5fa', '#3b82f6', '#1d4ed8', '#1e3a8a'],
        },
        textStyle: {
          color: isDark ? '#9ca3af' : '#6b7280',
          fontSize: 10,
        },
      },
      series: [
        {
          name: trait.name,
          type: 'heatmap',
          data: chartData,
          label: {
            show: processedData.genotypes.length < 20 && processedData.environments.length < 15,
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter: (params: any) => {
              return params.data[2] !== null ? params.data[2].toFixed(1) : '';
            },
            fontSize: 9,
            color: isDark ? '#fff' : '#000',
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
    };
  }, [processedData, trait, isDark, minVal, maxVal]);

  if (isLoading) {
    return (
      <Card className={`w-full ${className}`}>
        <CardHeader>
          <Skeleton className="h-8 w-1/3 mb-2" />
          <Skeleton className="h-4 w-1/2" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[400px] w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!data || !processedData) {
    return (
      <Card className={`w-full ${className}`}>
        <CardContent className="flex flex-col items-center justify-center h-[400px] text-muted-foreground">
          <RefreshCw className="h-12 w-12 mb-4 animate-spin-slow opacity-20" />
          <p>No data available for heatmap visualization</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader className="flex flex-col md:flex-row items-start md:items-center justify-between space-y-4 md:space-y-0 pb-7 border-b mb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <CardTitle className="text-2xl font-extrabold tracking-tight text-primary">{title}</CardTitle>
            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[10px] font-bold uppercase tracking-wider">
              <BrainCircuit className="h-3 w-3" />
              REEVU Aligned
            </div>
          </div>
          <CardDescription className="text-muted-foreground max-w-md">{description}</CardDescription>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Select
            value={selectedTraitIndex.toString()}
            onValueChange={(v) => setSelectedTraitIndex(parseInt(v))}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select Trait" />
            </SelectTrigger>
            <SelectContent>
              {data.traits.map((t, idx) => (
                <SelectItem key={t.id} value={idx.toString()}>{t.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={sortOrder}
            onValueChange={(v) => setSortOrder(v as 'none' | 'genotype' | 'environment')}
          >
            <SelectTrigger className="w-[150px]">
              <div className="flex items-center">
                <SortAsc className="mr-2 h-4 w-4" />
                <SelectValue placeholder="Sort By" />
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">Default Order</SelectItem>
              <SelectItem value="genotype">Genotype Mean</SelectItem>
              <SelectItem value="environment">Env Mean</SelectItem>
            </SelectContent>
          </Select>

          <Button variant="outline" size="icon" title="Filter Data">
            <Filter className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" title="Export CSV">
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[500px] w-full">
          <EChartsWrapper
            option={chartOption}
            onEvents={{
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              click: (params: any) => {
                if (onCellClick && params.data) {
                  const [eIdx, gIdx, val] = params.data;
                  onCellClick(processedData.genotypes[gIdx], processedData.environments[eIdx], val);
                }
              }
            }}
          />
        </div>
      </CardContent>
    </Card>
  );
};

export default GxEMatrixHeatmap;
