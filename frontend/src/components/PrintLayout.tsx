import { useState, useRef, useCallback } from 'react';
import { Printer, Download, Settings2, FileText, Image, Table2, BarChart3 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

type PageSize = 'a4' | 'letter' | 'legal';
type Orientation = 'portrait' | 'landscape';

interface PrintSection {
  id: string;
  title: string;
  type: 'header' | 'summary' | 'table' | 'chart' | 'notes';
  content: React.ReactNode;
  enabled: boolean;
}

interface PrintLayoutProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  subtitle?: string;
  sections: PrintSection[];
  logo?: string;
  footer?: string;
}

interface PrintOptions {
  pageSize: PageSize;
  orientation: Orientation;
  includeHeader: boolean;
  includeFooter: boolean;
  includePageNumbers: boolean;
  includeLogo: boolean;
  includeDate: boolean;
}

const PAGE_SIZES: Record<PageSize, { width: string; height: string; label: string }> = {
  a4: { width: '210mm', height: '297mm', label: 'A4 (210 × 297 mm)' },
  letter: { width: '8.5in', height: '11in', label: 'Letter (8.5 × 11 in)' },
  legal: { width: '8.5in', height: '14in', label: 'Legal (8.5 × 14 in)' },
};

export function PrintLayout({
  open,
  onOpenChange,
  title,
  subtitle,
  sections: initialSections,
  logo,
  footer = '© 2025 Bijmantra - Plant Breeding Platform',
}: PrintLayoutProps) {
  const printRef = useRef<HTMLDivElement>(null);
  const [sections, setSections] = useState(initialSections);
  const [options, setOptions] = useState<PrintOptions>({
    pageSize: 'a4',
    orientation: 'portrait',
    includeHeader: true,
    includeFooter: true,
    includePageNumbers: true,
    includeLogo: true,
    includeDate: true,
  });
  const [showPreview, setShowPreview] = useState(false);

  const toggleSection = (id: string) => {
    setSections(secs => secs.map(s => s.id === id ? { ...s, enabled: !s.enabled } : s));
  };

  const handlePrint = useCallback(() => {
    const printContent = printRef.current;
    if (!printContent) return;

    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    const pageSize = PAGE_SIZES[options.pageSize];
    const isLandscape = options.orientation === 'landscape';

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>${title}</title>
          <style>
            @page {
              size: ${isLandscape ? `${pageSize.height} ${pageSize.width}` : `${pageSize.width} ${pageSize.height}`};
              margin: 20mm;
            }
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              font-size: 12px;
              line-height: 1.5;
              color: #1a1a1a;
              margin: 0;
              padding: 0;
            }
            .print-header {
              display: flex;
              justify-content: space-between;
              align-items: flex-start;
              margin-bottom: 24px;
              padding-bottom: 16px;
              border-bottom: 2px solid #e5e5e5;
            }
            .print-logo {
              height: 40px;
              width: auto;
            }
            .print-title {
              font-size: 24px;
              font-weight: 700;
              margin: 0;
              color: #1a1a1a;
            }
            .print-subtitle {
              font-size: 14px;
              color: #666;
              margin: 4px 0 0 0;
            }
            .print-date {
              font-size: 11px;
              color: #888;
              text-align: right;
            }
            .print-section {
              margin-bottom: 24px;
              page-break-inside: avoid;
            }
            .print-section-title {
              font-size: 16px;
              font-weight: 600;
              margin: 0 0 12px 0;
              padding-bottom: 8px;
              border-bottom: 1px solid #e5e5e5;
            }
            .print-table {
              width: 100%;
              border-collapse: collapse;
              font-size: 11px;
            }
            .print-table th,
            .print-table td {
              padding: 8px 12px;
              text-align: left;
              border: 1px solid #e5e5e5;
            }
            .print-table th {
              background: #f5f5f5;
              font-weight: 600;
            }
            .print-table tr:nth-child(even) {
              background: #fafafa;
            }
            .print-footer {
              position: fixed;
              bottom: 0;
              left: 0;
              right: 0;
              padding: 12px 20mm;
              font-size: 10px;
              color: #888;
              border-top: 1px solid #e5e5e5;
              display: flex;
              justify-content: space-between;
            }
            .print-summary {
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
              gap: 16px;
            }
            .print-stat {
              padding: 12px;
              background: #f5f5f5;
              border-radius: 8px;
            }
            .print-stat-value {
              font-size: 24px;
              font-weight: 700;
              color: #1a1a1a;
            }
            .print-stat-label {
              font-size: 11px;
              color: #666;
            }
            @media print {
              .no-print { display: none !important; }
            }
          </style>
        </head>
        <body>
          ${printContent.innerHTML}
        </body>
      </html>
    `);

    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 250);
  }, [title, options]);

  const enabledSections = sections.filter(s => s.enabled);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Printer className="h-5 w-5" />
            Print Report
          </DialogTitle>
          <DialogDescription>
            Configure and preview your printable report
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex gap-4">
          {/* Settings Panel */}
          <div className="w-64 flex-shrink-0 space-y-4 overflow-y-auto">
            {/* Page Settings */}
            <div className="space-y-3">
              <h4 className="font-medium text-sm">Page Settings</h4>
              
              <div className="space-y-2">
                <Label className="text-xs">Page Size</Label>
                <Select
                  value={options.pageSize}
                  onValueChange={(v) => setOptions({ ...options, pageSize: v as PageSize })}
                >
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(PAGE_SIZES).map(([key, { label }]) => (
                      <SelectItem key={key} value={key}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-xs">Orientation</Label>
                <RadioGroup
                  value={options.orientation}
                  onValueChange={(v: string) => setOptions({ ...options, orientation: v as Orientation })}
                  className="flex gap-4"
                >
                  <label className="flex items-center gap-2 text-xs">
                    <RadioGroupItem value="portrait" />
                    Portrait
                  </label>
                  <label className="flex items-center gap-2 text-xs">
                    <RadioGroupItem value="landscape" />
                    Landscape
                  </label>
                </RadioGroup>
              </div>
            </div>

            <Separator />

            {/* Include Options */}
            <div className="space-y-3">
              <h4 className="font-medium text-sm">Include</h4>
              <div className="space-y-2">
                {[
                  { key: 'includeHeader', label: 'Header' },
                  { key: 'includeFooter', label: 'Footer' },
                  { key: 'includePageNumbers', label: 'Page Numbers' },
                  { key: 'includeLogo', label: 'Logo' },
                  { key: 'includeDate', label: 'Date' },
                ].map(({ key, label }) => (
                  <label key={key} className="flex items-center gap-2 text-xs">
                    <Checkbox
                      checked={options[key as keyof PrintOptions] as boolean}
                      onCheckedChange={(checked) => setOptions({ ...options, [key]: !!checked })}
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>

            <Separator />

            {/* Sections */}
            <div className="space-y-3">
              <h4 className="font-medium text-sm">Sections</h4>
              <div className="space-y-2">
                {sections.map((section) => (
                  <label key={section.id} className="flex items-center gap-2 text-xs">
                    <Checkbox
                      checked={section.enabled}
                      onCheckedChange={() => toggleSection(section.id)}
                    />
                    <span className="flex items-center gap-1.5">
                      {section.type === 'table' && <Table2 className="h-3 w-3" />}
                      {section.type === 'chart' && <BarChart3 className="h-3 w-3" />}
                      {section.type === 'summary' && <FileText className="h-3 w-3" />}
                      {section.title}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Preview */}
          <div className="flex-1 overflow-auto bg-muted/30 rounded-lg p-4">
            <div
              ref={printRef}
              className="bg-white shadow-lg mx-auto p-8"
              style={{
                width: options.orientation === 'landscape' ? '297mm' : '210mm',
                minHeight: options.orientation === 'landscape' ? '210mm' : '297mm',
                transform: 'scale(0.5)',
                transformOrigin: 'top center',
              }}
            >
              {/* Header */}
              {options.includeHeader && (
                <div className="print-header flex justify-between items-start mb-6 pb-4 border-b-2">
                  <div>
                    <h1 className="print-title text-2xl font-bold">{title}</h1>
                    {subtitle && <p className="print-subtitle text-gray-600">{subtitle}</p>}
                  </div>
                  <div className="text-right">
                    {options.includeLogo && logo && (
                      <img src={logo} alt="Logo" className="print-logo h-10 mb-2" />
                    )}
                    {options.includeDate && (
                      <p className="print-date text-xs text-gray-500">
                        Generated: {new Date().toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Sections */}
              {enabledSections.map((section) => (
                <div key={section.id} className="print-section mb-6">
                  <h2 className="print-section-title text-lg font-semibold mb-3 pb-2 border-b">
                    {section.title}
                  </h2>
                  <div>{section.content}</div>
                </div>
              ))}

              {/* Footer */}
              {options.includeFooter && (
                <div className="print-footer fixed bottom-0 left-0 right-0 p-3 text-xs text-gray-500 border-t flex justify-between">
                  <span>{footer}</span>
                  {options.includePageNumbers && <span>Page 1</span>}
                </div>
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handlePrint}>
            <Printer className="h-4 w-4 mr-2" />
            Print
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Helper component for print-ready tables
export function PrintTable({ 
  headers, 
  rows 
}: { 
  headers: string[]; 
  rows: (string | number)[][] 
}) {
  return (
    <table className="print-table w-full border-collapse text-sm">
      <thead>
        <tr>
          {headers.map((header, i) => (
            <th key={i} className="p-2 text-left bg-gray-100 border font-semibold">
              {header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i} className={i % 2 === 0 ? '' : 'bg-gray-50'}>
            {row.map((cell, j) => (
              <td key={j} className="p-2 border">
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// Helper component for print-ready stats
export function PrintStats({ 
  stats 
}: { 
  stats: { label: string; value: string | number }[] 
}) {
  return (
    <div className="print-summary grid grid-cols-4 gap-4">
      {stats.map((stat, i) => (
        <div key={i} className="print-stat p-3 bg-gray-100 rounded-lg">
          <div className="print-stat-value text-2xl font-bold">{stat.value}</div>
          <div className="print-stat-label text-xs text-gray-600">{stat.label}</div>
        </div>
      ))}
    </div>
  );
}
