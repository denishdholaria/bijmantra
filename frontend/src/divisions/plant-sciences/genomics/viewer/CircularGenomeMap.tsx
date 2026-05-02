import React, { useMemo, useState } from 'react';
import { GFFFeature } from './parsers';

interface CircularGenomeMapProps {
  sequenceLength: number;
  features: GFFFeature[];
  width?: number;
  height?: number;
}

interface Point {
  x: number;
  y: number;
}

export function CircularGenomeMap({
  sequenceLength,
  features,
  width = 600,
  height = 600
}: CircularGenomeMapProps) {
  const [hoveredFeature, setHoveredFeature] = useState<GFFFeature | null>(null);
  const [mousePos, setMousePos] = useState<Point>({ x: 0, y: 0 });

  const center = { x: width / 2, y: height / 2 };
  const radius = Math.min(width, height) / 2 - 50; // Padding
  const trackWidth = 20;

  // Helper to convert polar to cartesian
  const polarToCartesian = (centerX: number, centerY: number, radius: number, angleInDegrees: number) => {
    const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
    return {
      x: centerX + (radius * Math.cos(angleInRadians)),
      y: centerY + (radius * Math.sin(angleInRadians))
    };
  };

  // Helper to create SVG arc path
  const describeArc = (x: number, y: number, radius: number, startAngle: number, endAngle: number) => {
    const start = polarToCartesian(x, y, radius, endAngle);
    const end = polarToCartesian(x, y, radius, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";

    return [
      "M", start.x, start.y,
      "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y
    ].join(" ");
  };

  // Helper to create a filled arc slice (donut sector)
  const describeSector = (x: number, y: number, innerRadius: number, outerRadius: number, startAngle: number, endAngle: number) => {
    const startOuter = polarToCartesian(x, y, outerRadius, endAngle);
    const endOuter = polarToCartesian(x, y, outerRadius, startAngle);
    const startInner = polarToCartesian(x, y, innerRadius, endAngle);
    const endInner = polarToCartesian(x, y, innerRadius, startAngle);

    const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";

    return [
      "M", startOuter.x, startOuter.y,
      "A", outerRadius, outerRadius, 0, largeArcFlag, 0, endOuter.x, endOuter.y,
      "L", endInner.x, endInner.y,
      "A", innerRadius, innerRadius, 0, largeArcFlag, 1, startInner.x, startInner.y,
      "Z"
    ].join(" ");
  };

  const featureArcs = useMemo(() => {
    return features.map((feature, index) => {
      // Map coordinates to angles
      const startAngle = (feature.start / sequenceLength) * 360;
      const endAngle = (feature.end / sequenceLength) * 360;

      // Determine radius based on strand or type
      // + strand: slightly outside
      // - strand: slightly inside
      const isPositiveStrand = feature.strand !== '-';
      const innerR = isPositiveStrand ? radius : radius - trackWidth;
      const outerR = isPositiveStrand ? radius + trackWidth : radius;

      // Color based on type
      let color = '#cbd5e1'; // slate-300
      if (feature.type === 'gene') color = '#3b82f6'; // blue
      else if (feature.type === 'CDS') color = '#22c55e'; // green
      else if (feature.type === 'rRNA') color = '#eab308'; // yellow
      else if (feature.type === 'tRNA') color = '#ef4444'; // red

      return {
        feature,
        path: describeSector(center.x, center.y, innerR, outerR, startAngle, endAngle),
        color
      };
    });
  }, [features, sequenceLength, radius, center, trackWidth]);

  return (
    <div className="relative inline-block">
      <svg width={width} height={height} className="block">
        {/* Backbone Circle */}
        <circle
          cx={center.x}
          cy={center.y}
          r={radius}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth="1"
        />

        {/* Features */}
        {featureArcs.map((item, i) => (
          <path
            key={i}
            d={item.path}
            fill={item.color}
            stroke="white"
            strokeWidth="0.5"
            className="hover:opacity-80 transition-opacity cursor-pointer"
            onMouseEnter={(e) => {
              setHoveredFeature(item.feature);
              setMousePos({ x: e.clientX, y: e.clientY });
            }}
            onMouseLeave={() => setHoveredFeature(null)}
          />
        ))}

        {/* Center Label */}
        <text
          x={center.x}
          y={center.y}
          textAnchor="middle"
          dominantBaseline="middle"
          className="text-sm fill-slate-500 font-mono pointer-events-none"
        >
          {sequenceLength.toLocaleString()} bp
        </text>
      </svg>

      {/* Tooltip */}
      {hoveredFeature && (
        <div
          className="fixed z-50 p-3 bg-slate-900 text-white text-xs rounded shadow-xl pointer-events-none border border-slate-700 max-w-xs"
          style={{
            left: mousePos.x + 10,
            top: mousePos.y + 10,
          }}
        >
          <div className="font-bold text-emerald-400 mb-1">{hoveredFeature.attributes.ID || hoveredFeature.type}</div>
          <div className="grid grid-cols-[auto,1fr] gap-x-3 gap-y-1">
            <span className="text-slate-400">Type:</span>
            <span>{hoveredFeature.type}</span>
            <span className="text-slate-400">Loc:</span>
            <span>{hoveredFeature.start.toLocaleString()} - {hoveredFeature.end.toLocaleString()}</span>
            <span className="text-slate-400">Strand:</span>
            <span>{hoveredFeature.strand}</span>
            {Object.entries(hoveredFeature.attributes).slice(0, 3).map(([key, val]) => (
              <React.Fragment key={key}>
                <span className="text-slate-400">{key}:</span>
                <span className="truncate">{val}</span>
              </React.Fragment>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
