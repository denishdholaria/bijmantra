/**
 * Breeding Analytics Charts
 * Advanced visualization components for breeding data
 * 
 * APEX FEATURE: Interactive, publication-quality visualizations
 */

import { useState, useMemo } from 'react'
import { cn } from '@/lib/utils'

// ============================================
// GENETIC GAIN CHART
// ============================================

interface GeneticGainData {
  year: number
  gain: number
  cumulative: number
  target: number
}

interface GeneticGainChartProps {
  data: GeneticGainData[]
  title?: string
  className?: string
}

export function GeneticGainChart({ data, title = 'Genetic Gain Over Time', className }: GeneticGainChartProps) {
  const [hoveredPoint, setHoveredPoint] = useState<number | null>(null)

  const maxGain = Math.max(...data.map(d => Math.max(d.cumulative, d.target)))
  const minYear = Math.min(...data.map(d => d.year))
  const maxYear = Math.max(...data.map(d => d.year))

  const chartWidth = 600
  const chartHeight = 300
  const padding = { top: 20, right: 20, bottom: 40, left: 50 }
  const innerWidth = chartWidth - padding.left - padding.right
  const innerHeight = chartHeight - padding.top - padding.bottom

  const xScale = (year: number) => 
    padding.left + ((year - minYear) / (maxYear - minYear)) * innerWidth

  const yScale = (value: number) => 
    padding.top + innerHeight - (value / maxGain) * innerHeight

  // Generate path for cumulative line
  const cumulativePath = data
    .map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(d.year)} ${yScale(d.cumulative)}`)
    .join(' ')

  // Generate path for target line
  const targetPath = data
    .map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(d.year)} ${yScale(d.target)}`)
    .join(' ')

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4', className)}>
      <h3 className="font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
      
      <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full">
        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map(pct => {
          const y = yScale((pct / 100) * maxGain)
          return (
            <g key={pct}>
              <line
                x1={padding.left}
                y1={y}
                x2={chartWidth - padding.right}
                y2={y}
                stroke="currentColor"
                strokeOpacity={0.1}
                className="text-gray-400"
              />
              <text
                x={padding.left - 8}
                y={y}
                textAnchor="end"
                alignmentBaseline="middle"
                className="text-xs fill-gray-500"
              >
                {((pct / 100) * maxGain).toFixed(1)}%
              </text>
            </g>
          )
        })}

        {/* X-axis labels */}
        {data.map(d => (
          <text
            key={d.year}
            x={xScale(d.year)}
            y={chartHeight - 10}
            textAnchor="middle"
            className="text-xs fill-gray-500"
          >
            {d.year}
          </text>
        ))}

        {/* Target line (dashed) */}
        <path
          d={targetPath}
          fill="none"
          stroke="#94a3b8"
          strokeWidth={2}
          strokeDasharray="5,5"
        />

        {/* Cumulative gain line */}
        <path
          d={cumulativePath}
          fill="none"
          stroke="#f59e0b"
          strokeWidth={3}
        />

        {/* Area under curve */}
        <path
          d={`${cumulativePath} L ${xScale(maxYear)} ${yScale(0)} L ${xScale(minYear)} ${yScale(0)} Z`}
          fill="url(#gainGradient)"
          opacity={0.3}
        />

        {/* Gradient definition */}
        <defs>
          <linearGradient id="gainGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
          </linearGradient>
        </defs>

        {/* Data points */}
        {data.map((d, i) => (
          <g key={i}>
            <circle
              cx={xScale(d.year)}
              cy={yScale(d.cumulative)}
              r={hoveredPoint === i ? 8 : 5}
              fill="#f59e0b"
              stroke="white"
              strokeWidth={2}
              className="cursor-pointer transition-all"
              onMouseEnter={() => setHoveredPoint(i)}
              onMouseLeave={() => setHoveredPoint(null)}
            />
            
            {/* Tooltip */}
            {hoveredPoint === i && (
              <g>
                <rect
                  x={xScale(d.year) - 50}
                  y={yScale(d.cumulative) - 50}
                  width={100}
                  height={40}
                  rx={4}
                  fill="#1f2937"
                />
                <text
                  x={xScale(d.year)}
                  y={yScale(d.cumulative) - 35}
                  textAnchor="middle"
                  className="text-xs fill-white font-medium"
                >
                  {d.year}: {d.cumulative.toFixed(2)}%
                </text>
                <text
                  x={xScale(d.year)}
                  y={yScale(d.cumulative) - 20}
                  textAnchor="middle"
                  className="text-xs fill-gray-400"
                >
                  Annual: +{d.gain.toFixed(2)}%
                </text>
              </g>
            )}
          </g>
        ))}

        {/* Legend */}
        <g transform={`translate(${chartWidth - 150}, 10)`}>
          <line x1={0} y1={8} x2={20} y2={8} stroke="#f59e0b" strokeWidth={3} />
          <text x={25} y={12} className="text-xs fill-gray-600 dark:fill-gray-400">Actual Gain</text>
          
          <line x1={0} y1={28} x2={20} y2={28} stroke="#94a3b8" strokeWidth={2} strokeDasharray="5,5" />
          <text x={25} y={32} className="text-xs fill-gray-600 dark:fill-gray-400">Target</text>
        </g>
      </svg>
    </div>
  )
}

// ============================================
// HERITABILITY GAUGE
// ============================================

interface HeritabilityGaugeProps {
  value: number
  trait: string
  className?: string
}

export function HeritabilityGauge({ value, trait, className }: HeritabilityGaugeProps) {
  const percentage = value * 100
  const angle = (percentage / 100) * 180 - 90 // -90 to 90 degrees

  const getColor = (val: number) => {
    if (val >= 0.7) return '#22c55e' // High heritability
    if (val >= 0.4) return '#f59e0b' // Medium
    return '#ef4444' // Low
  }

  const getLabel = (val: number) => {
    if (val >= 0.7) return 'High'
    if (val >= 0.4) return 'Medium'
    return 'Low'
  }

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center', className)}>
      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">{trait}</h4>
      
      <svg viewBox="0 0 200 120" className="w-full max-w-[200px] mx-auto">
        {/* Background arc */}
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={12}
          strokeLinecap="round"
        />
        
        {/* Value arc */}
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke={getColor(value)}
          strokeWidth={12}
          strokeLinecap="round"
          strokeDasharray={`${(percentage / 100) * 251.2} 251.2`}
        />

        {/* Needle */}
        <g transform={`rotate(${angle}, 100, 100)`}>
          <line
            x1={100}
            y1={100}
            x2={100}
            y2={35}
            stroke="#1f2937"
            strokeWidth={3}
            strokeLinecap="round"
          />
          <circle cx={100} cy={100} r={8} fill="#1f2937" />
        </g>

        {/* Labels */}
        <text x={20} y={115} className="text-xs fill-gray-500">0</text>
        <text x={95} y={25} className="text-xs fill-gray-500">0.5</text>
        <text x={175} y={115} className="text-xs fill-gray-500">1.0</text>
      </svg>

      <div className="mt-2">
        <span className="text-2xl font-bold" style={{ color: getColor(value) }}>
          {value.toFixed(2)}
        </span>
        <span 
          className="ml-2 text-sm px-2 py-0.5 rounded-full"
          style={{ 
            backgroundColor: `${getColor(value)}20`,
            color: getColor(value)
          }}
        >
          {getLabel(value)}
        </span>
      </div>
    </div>
  )
}

// ============================================
// SELECTION RESPONSE CHART
// ============================================

interface SelectionData {
  generation: number
  mean: number
  variance: number
  selected: number
}

interface SelectionResponseChartProps {
  data: SelectionData[]
  title?: string
  className?: string
}

export function SelectionResponseChart({ 
  data, 
  title = 'Selection Response', 
  className 
}: SelectionResponseChartProps) {
  const chartWidth = 500
  const chartHeight = 250
  const padding = { top: 20, right: 20, bottom: 40, left: 50 }

  const maxMean = Math.max(...data.map(d => d.mean + d.variance))
  const minMean = Math.min(...data.map(d => d.mean - d.variance))

  const xScale = (gen: number) => 
    padding.left + (gen / (data.length - 1)) * (chartWidth - padding.left - padding.right)

  const yScale = (val: number) => 
    padding.top + ((maxMean - val) / (maxMean - minMean)) * (chartHeight - padding.top - padding.bottom)

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4', className)}>
      <h3 className="font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
      
      <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full">
        {/* Variance bands */}
        <path
          d={
            data.map((d, i) => 
              `${i === 0 ? 'M' : 'L'} ${xScale(d.generation)} ${yScale(d.mean + d.variance)}`
            ).join(' ') +
            data.slice().reverse().map((d, i) => 
              `L ${xScale(d.generation)} ${yScale(d.mean - d.variance)}`
            ).join(' ') +
            ' Z'
          }
          fill="#3b82f6"
          opacity={0.2}
        />

        {/* Mean line */}
        <path
          d={data.map((d, i) => 
            `${i === 0 ? 'M' : 'L'} ${xScale(d.generation)} ${yScale(d.mean)}`
          ).join(' ')}
          fill="none"
          stroke="#3b82f6"
          strokeWidth={3}
        />

        {/* Selected line */}
        <path
          d={data.map((d, i) => 
            `${i === 0 ? 'M' : 'L'} ${xScale(d.generation)} ${yScale(d.selected)}`
          ).join(' ')}
          fill="none"
          stroke="#22c55e"
          strokeWidth={2}
          strokeDasharray="5,5"
        />

        {/* Data points */}
        {data.map((d, i) => (
          <g key={i}>
            <circle
              cx={xScale(d.generation)}
              cy={yScale(d.mean)}
              r={5}
              fill="#3b82f6"
              stroke="white"
              strokeWidth={2}
            />
            <circle
              cx={xScale(d.generation)}
              cy={yScale(d.selected)}
              r={4}
              fill="#22c55e"
              stroke="white"
              strokeWidth={2}
            />
          </g>
        ))}

        {/* X-axis */}
        {data.map(d => (
          <text
            key={d.generation}
            x={xScale(d.generation)}
            y={chartHeight - 10}
            textAnchor="middle"
            className="text-xs fill-gray-500"
          >
            G{d.generation}
          </text>
        ))}

        {/* Y-axis label */}
        <text
          x={15}
          y={chartHeight / 2}
          textAnchor="middle"
          transform={`rotate(-90, 15, ${chartHeight / 2})`}
          className="text-xs fill-gray-500"
        >
          Trait Value
        </text>

        {/* Legend */}
        <g transform={`translate(${chartWidth - 120}, 10)`}>
          <circle cx={5} cy={5} r={4} fill="#3b82f6" />
          <text x={15} y={9} className="text-xs fill-gray-600 dark:fill-gray-400">Population Mean</text>
          
          <circle cx={5} cy={25} r={4} fill="#22c55e" />
          <text x={15} y={29} className="text-xs fill-gray-600 dark:fill-gray-400">Selected Mean</text>
        </g>
      </svg>
    </div>
  )
}

// ============================================
// CORRELATION HEATMAP
// ============================================

interface CorrelationHeatmapProps {
  traits: string[]
  correlations: number[][]
  title?: string
  className?: string
}

export function CorrelationHeatmap({ 
  traits, 
  correlations, 
  title = 'Trait Correlations',
  className 
}: CorrelationHeatmapProps) {
  const [hoveredCell, setHoveredCell] = useState<{ i: number; j: number } | null>(null)

  const getColor = (value: number) => {
    if (value > 0) {
      const intensity = Math.min(value, 1)
      return `rgba(34, 197, 94, ${intensity})`
    } else {
      const intensity = Math.min(Math.abs(value), 1)
      return `rgba(239, 68, 68, ${intensity})`
    }
  }

  const cellSize = 50
  const labelWidth = 80
  const width = labelWidth + traits.length * cellSize
  const height = labelWidth + traits.length * cellSize

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4', className)}>
      <h3 className="font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
      
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full max-w-[500px]">
        {/* Column labels */}
        {traits.map((trait, i) => (
          <text
            key={`col-${i}`}
            x={labelWidth + i * cellSize + cellSize / 2}
            y={labelWidth - 10}
            textAnchor="middle"
            className="text-xs fill-gray-600 dark:fill-gray-400"
            transform={`rotate(-45, ${labelWidth + i * cellSize + cellSize / 2}, ${labelWidth - 10})`}
          >
            {trait}
          </text>
        ))}

        {/* Row labels and cells */}
        {traits.map((trait, i) => (
          <g key={`row-${i}`}>
            <text
              x={labelWidth - 10}
              y={labelWidth + i * cellSize + cellSize / 2 + 4}
              textAnchor="end"
              className="text-xs fill-gray-600 dark:fill-gray-400"
            >
              {trait}
            </text>

            {traits.map((_, j) => (
              <g key={`cell-${i}-${j}`}>
                <rect
                  x={labelWidth + j * cellSize}
                  y={labelWidth + i * cellSize}
                  width={cellSize - 2}
                  height={cellSize - 2}
                  fill={getColor(correlations[i][j])}
                  stroke={hoveredCell?.i === i && hoveredCell?.j === j ? '#1f2937' : 'transparent'}
                  strokeWidth={2}
                  rx={4}
                  className="cursor-pointer transition-all"
                  onMouseEnter={() => setHoveredCell({ i, j })}
                  onMouseLeave={() => setHoveredCell(null)}
                />
                <text
                  x={labelWidth + j * cellSize + cellSize / 2}
                  y={labelWidth + i * cellSize + cellSize / 2 + 4}
                  textAnchor="middle"
                  className="text-xs fill-gray-800 dark:fill-gray-200 font-medium pointer-events-none"
                >
                  {correlations[i][j].toFixed(2)}
                </text>
              </g>
            ))}
          </g>
        ))}

        {/* Color legend */}
        <g transform={`translate(${width - 80}, ${height - 30})`}>
          <rect x={0} y={0} width={15} height={15} fill="rgba(239, 68, 68, 0.8)" rx={2} />
          <text x={20} y={12} className="text-xs fill-gray-500">Negative</text>
          
          <rect x={0} y={20} width={15} height={15} fill="rgba(34, 197, 94, 0.8)" rx={2} />
          <text x={20} y={32} className="text-xs fill-gray-500">Positive</text>
        </g>
      </svg>
    </div>
  )
}

export default {
  GeneticGainChart,
  HeritabilityGauge,
  SelectionResponseChart,
  CorrelationHeatmap
}
