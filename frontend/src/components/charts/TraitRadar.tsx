/**
 * Trait Radar Chart Component
 *
 * Multi-trait comparison visualization for breeding selections.
 * Uses Recharts RadarChart for declarative rendering.
 */

import { useMemo } from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface TraitValue {
  trait: string;
  value: number;
  min?: number;
  max?: number;
}

interface Entry {
  name: string;
  color?: string;
  traits: TraitValue[];
}

interface TraitRadarProps {
  entries: Entry[];
  traits: string[];
  showLegend?: boolean;
  showTooltip?: boolean;
  height?: number;
  colorblindSafe?: boolean;
}

// Colorblind-safe palette (Okabe-Ito)
const COLORBLIND_SAFE_COLORS = [
  '#0072B2', // Blue
  '#E69F00', // Orange
  '#009E73', // Teal
  '#CC79A7', // Pink
  '#56B4E9', // Sky Blue
  '#D55E00', // Vermillion
  '#F0E442', // Yellow
  '#000000', // Black
];

// Standard palette
const STANDARD_COLORS = [
  'hsl(230, 70%, 55%)',
  'hsl(35, 95%, 55%)',
  'hsl(150, 60%, 45%)',
  'hsl(325, 65%, 55%)',
  'hsl(190, 75%, 50%)',
  'hsl(0, 70%, 55%)',
  'hsl(270, 60%, 55%)',
  'hsl(60, 70%, 50%)',
];

export function TraitRadar({
  entries,
  traits,
  showLegend = true,
  showTooltip = true,
  height = 400,
  colorblindSafe = false,
}: TraitRadarProps) {
  const colors = colorblindSafe ? COLORBLIND_SAFE_COLORS : STANDARD_COLORS;

  // Transform data for Recharts format
  const chartData = useMemo(() => {
    return traits.map((trait) => {
      const dataPoint: Record<string, string | number> = { trait };
      entries.forEach((entry) => {
        const traitData = entry.traits.find((t) => t.trait === trait);
        if (traitData) {
          // Normalize to 0-100 scale if min/max provided
          if (traitData.min !== undefined && traitData.max !== undefined) {
            const range = traitData.max - traitData.min;
            dataPoint[entry.name] = range > 0
              ? ((traitData.value - traitData.min) / range) * 100
              : 50;
          } else {
            dataPoint[entry.name] = traitData.value;
          }
        }
      });
      return dataPoint;
    });
  }, [entries, traits]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={chartData} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
        <PolarGrid stroke="hsl(var(--border))" />
        <PolarAngleAxis
          dataKey="trait"
          tick={{ fill: 'hsl(var(--foreground))', fontSize: 12 }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
        />
        {entries.map((entry, index) => (
          <Radar
            key={entry.name}
            name={entry.name}
            dataKey={entry.name}
            stroke={entry.color || colors[index % colors.length]}
            fill={entry.color || colors[index % colors.length]}
            fillOpacity={0.2}
            strokeWidth={2}
          />
        ))}
        {showTooltip && (
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--background))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '6px',
            }}
          />
        )}
        {showLegend && <Legend />}
      </RadarChart>
    </ResponsiveContainer>
  );
}

export default TraitRadar;
