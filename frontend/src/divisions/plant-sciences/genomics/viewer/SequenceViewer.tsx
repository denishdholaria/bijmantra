import React, { useRef, useEffect } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { SequenceRecord } from './parsers';

interface SequenceViewerProps {
  data: SequenceRecord;
  basesPerRow?: number;
}

const NUCLEOTIDE_COLORS: Record<string, string> = {
  'A': '#22c55e', // Green
  'T': '#ef4444', // Red
  'C': '#3b82f6', // Blue
  'G': '#000000', // Black
  'N': '#9ca3af', // Gray
};

const ROW_HEIGHT = 50; // Text + Quality
const CHAR_WIDTH = 16; // Fixed pixel width per character for alignment

function QualityCanvas({ quality, width, height = 16, charWidth }: { quality: string, width: number, height?: number, charWidth: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Handle high DPI displays
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    ctx.clearRect(0, 0, width, height);

    quality.split('').forEach((char, i) => {
        // Phred+33
        const score = char.charCodeAt(0) - 33;
        // Normalize score (usually 0-40) to height
        const barHeight = Math.min(height, (score / 40) * height);

        // Color
        ctx.fillStyle = score >= 30 ? '#22c55e' : score >= 20 ? '#eab308' : '#ef4444';

        // Draw bar centered in the char slot, with some padding
        const barWidth = charWidth - 4;
        const x = i * charWidth + 2;
        const y = height - barHeight;

        ctx.fillRect(x, y, barWidth, barHeight);
    });
  }, [quality, width, height, charWidth]);

  return <canvas ref={canvasRef} />;
}

export function SequenceViewer({ data, basesPerRow = 60 }: SequenceViewerProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const rowCount = Math.ceil(data.sequence.length / basesPerRow);

  const rowVirtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: () => parentRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 5,
  });

  return (
    <div
      ref={parentRef}
      className="h-[600px] w-full overflow-auto border border-slate-200 rounded-lg bg-white shadow-sm"
    >
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const startIdx = virtualRow.index * basesPerRow;
          const endIdx = Math.min(startIdx + basesPerRow, data.sequence.length);
          const seqChunk = data.sequence.slice(startIdx, endIdx);
          const qualChunk = data.quality ? data.quality.slice(startIdx, endIdx) : null;

          return (
            <div
              key={virtualRow.index}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
              className="flex items-start px-4 py-2 font-mono text-sm hover:bg-slate-50 transition-colors"
            >
              {/* Index */}
              <div className="w-20 text-slate-400 select-none text-xs pt-1 border-r border-slate-100 mr-4 flex-shrink-0">
                {startIdx + 1}
              </div>

              {/* Sequence & Quality Container */}
              <div className="flex-1 relative overflow-x-auto">
                {/* Sequence Text */}
                <div className="flex select-text whitespace-nowrap" style={{ width: basesPerRow * CHAR_WIDTH }}>
                  {seqChunk.split('').map((char, i) => (
                    <span
                      key={i}
                      className="inline-flex justify-center font-bold"
                      style={{
                        color: NUCLEOTIDE_COLORS[char.toUpperCase()] || NUCLEOTIDE_COLORS['N'],
                        width: `${CHAR_WIDTH}px`,
                        display: 'inline-block',
                        textAlign: 'center'
                      }}
                    >
                      {char}
                    </span>
                  ))}
                </div>

                {/* Quality Canvas */}
                {qualChunk && (
                  <div className="mt-1" style={{ width: seqChunk.length * CHAR_WIDTH, height: 16 }}>
                    <QualityCanvas
                      quality={qualChunk}
                      width={seqChunk.length * CHAR_WIDTH}
                      charWidth={CHAR_WIDTH}
                    />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
