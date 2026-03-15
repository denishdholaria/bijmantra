import React from 'react';
import {
  FileText,
  Table as TableIcon,
  Info,
  ShieldCheck,
  AlertCircle,
  Calendar,
  User,
  Hash,
  Printer,
  Download
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

/**
 * REEVU Evidence reference structure following the Agent Contract
 */
export interface ReevuEvidenceRef {
  source_type: string;
  entity_id: string;
  retrieved_at: string;
  query_or_method: string;
  freshness_seconds: number;
}

/**
 * REEVU Insight following the Evidence Envelope structure
 */
export interface ReevuInsight {
  claims: string[];
  evidence_refs: ReevuEvidenceRef[];
  calculation_steps?: {
    formula: string;
    inputs: Record<string, unknown>;
    computation_id: string;
  }[];
  uncertainty: {
    score: number;
    missing_data_indicators: string[];
  };
  policy_flags?: string[];
}

/**
 * Data Table structure, inspired by BrAPI
 */
export interface ReportDataTable {
  title: string;
  headers: string[];
  rows: (string | number | boolean | null)[][];
  footer?: string;
}

/**
 * Metric/Summary item
 */
export interface ReportMetric {
  label: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'neutral';
}

/**
 * Main Data structure for the report
 */
export interface PdfReportData {
  title: string;
  subtitle?: string;
  generatedAt: string;
  generatedBy: string;
  logoUrl?: string;
  metrics?: ReportMetric[];
  tables?: ReportDataTable[];
  reevuInsights?: ReevuInsight[];
  summary?: string;
  footerText?: string;
}

/**
 * Template configuration
 */
export interface PdfReportTemplate {
  id: string;
  name: string;
  pageSize: 'A4' | 'Letter';
  orientation: 'portrait' | 'landscape';
  showPageNumbers: boolean;
  showTableOfContents: boolean;
  themeColor: string;
}

export interface PdfReportTemplateRendererProps {
  data: PdfReportData;
  template: PdfReportTemplate;
  isDraft?: boolean;
  className?: string;
}

const PAGE_DIMENSIONS = {
  A4: {
    portrait: { width: '210mm', minHeight: '297mm' },
    landscape: { width: '297mm', minHeight: '210mm' }
  },
  Letter: {
    portrait: { width: '8.5in', minHeight: '11in' },
    landscape: { width: '11in', minHeight: '8.5in' }
  }
};

/**
 * PdfReportTemplateRenderer - A component for rendering high-quality printable reports.
 * Designed for isolation and strictly follows REEVU Agent Contract for AI insights.
 */
export const PdfReportTemplateRenderer: React.FC<PdfReportTemplateRendererProps> = ({
  data,
  template,
  isDraft = false,
  className
}) => {
  const dimensions = PAGE_DIMENSIONS[template.pageSize][template.orientation];

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className={cn("pdf-report-root flex flex-col items-center py-8 bg-slate-100 min-h-screen", className)}>
      {/* Control Bar (Hidden on print) */}
      <div className="w-full max-w-[210mm] mb-6 flex justify-between items-center bg-white p-4 rounded-lg shadow-sm print:hidden">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          <span className="font-semibold">{data.title}</span>
          <Badge variant="outline" className="ml-2 uppercase text-[10px]">{template.pageSize} {template.orientation}</Badge>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handlePrint}>
            <Printer className="h-4 w-4 mr-2" />
            Print
          </Button>
          <Button size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export PDF
          </Button>
        </div>
      </div>

      {/* Page Container */}
      <div
        className="pdf-page bg-white shadow-2xl relative overflow-hidden print:shadow-none print:m-0"
        style={{
          width: dimensions.width,
          minHeight: dimensions.minHeight,
          padding: '20mm',
        }}
      >
        {/* Draft Watermark */}
        {isDraft && (
          <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-[0.03] rotate-[-45deg] select-none">
            <span className="text-[120px] font-bold border-[20px] border-black px-12 py-4 rounded-3xl">DRAFT</span>
          </div>
        )}

        <style dangerouslySetInnerHTML={{ __html: `
          @media print {
            @page {
              size: ${template.pageSize} ${template.orientation};
              margin: 0;
            }
            body {
              background-color: white !important;
              padding: 0 !important;
              margin: 0 !important;
            }
            .pdf-report-root {
              padding: 0 !important;
              background-color: white !important;
            }
            .pdf-page {
              box-shadow: none !important;
              width: 100% !important;
              min-height: auto !important;
              margin: 0 !important;
              padding: 20mm !important;
            }
          }
        `}} />

        {/* Content goes here */}
        <div className="relative z-10 flex flex-col gap-8 h-full">
          {/* Header */}
          <header className="flex justify-between items-start border-b-2 border-primary pb-6">
            <div className="flex flex-col gap-1">
              {data.logoUrl && <img src={data.logoUrl} alt="Logo" className="h-12 w-auto mb-2" />}
              {!data.logoUrl && (
                <div className="h-12 w-12 bg-primary flex items-center justify-center rounded-lg mb-2">
                  <FileText className="h-8 w-8 text-white" />
                </div>
              )}
              <h1 className="text-3xl font-bold text-slate-900 tracking-tight">{data.title}</h1>
              {data.subtitle && <p className="text-lg text-slate-500">{data.subtitle}</p>}
            </div>
            <div className="text-right text-sm text-slate-400 flex flex-col gap-1 pt-2">
              <div className="flex items-center justify-end gap-2">
                <span>{data.generatedAt}</span>
                <Calendar className="h-3.5 w-3.5" />
              </div>
              <div className="flex items-center justify-end gap-2">
                <span>{data.generatedBy}</span>
                <User className="h-3.5 w-3.5" />
              </div>
              <div className="flex items-center justify-end gap-2">
                <span>REF: {data.title.substring(0, 3).toUpperCase()}-{new Date().getFullYear()}</span>
                <Hash className="h-3.5 w-3.5" />
              </div>
            </div>
          </header>

          {/* Summary / Metrics */}
          {data.metrics && data.metrics.length > 0 && (
            <section className="grid grid-cols-4 gap-4">
              {data.metrics.map((metric, i) => (
                <div key={i} className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">{metric.label}</p>
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-bold text-slate-900">{metric.value}</span>
                    {metric.unit && <span className="text-xs text-slate-400 font-medium">{metric.unit}</span>}
                  </div>
                </div>
              ))}
            </section>
          )}

          {/* Main Summary Text */}
          {data.summary && (
            <section className="space-y-3">
              <h2 className="text-sm font-bold uppercase tracking-widest text-primary flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Executive Summary
              </h2>
              <div className="p-4 bg-slate-50/50 rounded-lg border border-slate-100/50 text-slate-700 leading-relaxed text-sm">
                {data.summary}
              </div>
            </section>
          )}

          {/* Space for dynamic content */}
          <div className="flex-1 space-y-8">
            {/* Data Tables */}
            {data.tables && data.tables.map((table, tableIdx) => (
              <section key={tableIdx} className="space-y-3">
                <h3 className="text-sm font-bold uppercase tracking-widest text-slate-900 flex items-center gap-2">
                  <TableIcon className="h-4 w-4 text-primary" />
                  {table.title}
                </h3>
                <div className="rounded-md border border-slate-200 overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-slate-50 hover:bg-slate-50">
                        {table.headers.map((header, i) => (
                          <TableHead key={i} className="text-[10px] font-bold uppercase text-slate-500 py-2">
                            {header}
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {table.rows.map((row, rowIdx) => (
                        <TableRow key={rowIdx} className="hover:bg-transparent">
                          {row.map((cell, cellIdx) => (
                            <TableCell key={cellIdx} className="text-xs py-2 text-slate-700">
                              {cell === null ? '-' : String(cell)}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                {table.footer && <p className="text-[10px] text-slate-400 italic">{table.footer}</p>}
              </section>
            ))}

            {/* REEVU Insights */}
            {data.reevuInsights && data.reevuInsights.map((insight, insightIdx) => (
              <section key={insightIdx} className="space-y-4 bg-slate-50/30 p-6 rounded-xl border border-primary/10">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold uppercase tracking-widest text-primary flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4" />
                    REEVU Scientific Insight
                  </h3>
                  <Badge variant="outline" className="text-[9px] bg-white">
                    CONFIDENCE: {(insight.uncertainty.score * 100).toFixed(0)}%
                  </Badge>
                </div>

                <div className="space-y-3">
                  {insight.claims.map((claim, i) => (
                    <div key={i} className="flex gap-3">
                      <div className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                      <p className="text-sm text-slate-800 leading-relaxed font-medium">{claim}</p>
                    </div>
                  ))}
                </div>

                {/* Evidence References */}
                <div className="pt-4 border-t border-slate-100 mt-4">
                  <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                    <Info className="h-3 w-3" />
                    Evidence Assembly (Traceable Provenance)
                  </h4>
                  <div className="grid grid-cols-2 gap-3">
                    {insight.evidence_refs.map((ref, i) => (
                      <div key={i} className="bg-white p-2 rounded border border-slate-100 flex flex-col gap-1">
                        <div className="flex justify-between items-center">
                          <span className="text-[9px] font-bold text-primary uppercase">{ref.source_type}</span>
                          <span className="text-[8px] text-slate-400">{ref.retrieved_at}</span>
                        </div>
                        <p className="text-[10px] text-slate-600 truncate">ID: {ref.entity_id}</p>
                        <p className="text-[8px] text-slate-400 italic truncate">{ref.query_or_method}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Missing Data Warnings */}
                {insight.uncertainty.missing_data_indicators.length > 0 && (
                  <div className="flex gap-2 items-center text-[10px] text-amber-600 bg-amber-50 p-2 rounded border border-amber-100">
                    <AlertCircle className="h-3 w-3" />
                    <span className="font-semibold uppercase">Missing Data:</span>
                    <span>{insight.uncertainty.missing_data_indicators.join(', ')}</span>
                  </div>
                )}
              </section>
            ))}
          </div>

          {/* Footer */}
          <footer className="mt-auto pt-6 border-t border-slate-100 flex justify-between items-center text-[10px] text-slate-400 uppercase tracking-widest">
            <div>{data.footerText || "BijMantra Platform - Confidential Scientific Report"}</div>
            {template.showPageNumbers && <div>Page 1 of 1</div>}
          </footer>
        </div>
      </div>
    </div>
  );
};

export default PdfReportTemplateRenderer;
