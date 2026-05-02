import { useMemo, useRef, useState, type ChangeEvent } from 'react'
import { Download, FileSpreadsheet, LoaderCircle, Plus, Rows3, Upload } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import {
  downloadBlob,
  exportTableDataToBlob,
  inferSpreadsheetFileFormat,
  parseTableDataFile,
} from '@/lib/spreadsheet'
import { cn } from '@/lib/utils'
import {
  createDefaultWorkbenchTableData,
  getWorkbenchTableDelimiter,
  parseDelimitedTable,
  serializeDelimitedTable,
  type WorkbenchTableData,
} from '@/lib/workbenchDocuments'

type WorkbenchTableEditorProps = {
  value?: string
  onChange?: (value: string) => void
  tableData?: WorkbenchTableData
  onTableDataChange?: (tableData: WorkbenchTableData) => void
  filePath?: string
  readOnly?: boolean
  className?: string
}

export function WorkbenchTableEditor({
  value,
  onChange,
  tableData: providedTableData,
  onTableDataChange,
  filePath,
  readOnly = false,
  className,
}: WorkbenchTableEditorProps) {
  const importInputRef = useRef<HTMLInputElement | null>(null)
  const [importError, setImportError] = useState<string | null>(null)
  const [isImporting, setIsImporting] = useState(false)
  const delimiter = getWorkbenchTableDelimiter(filePath)
  const tableData = useMemo(
    () => providedTableData ?? parseDelimitedTable(value ?? '', delimiter),
    [delimiter, providedTableData, value]
  )
  const preferredTextExportFormat = delimiter === '\t' ? 'tsv' : 'csv'
  const preferredTextExportLabel = preferredTextExportFormat.toUpperCase()
  const preferredExcelExportFormat = 'xlsx'
  const preferredExcelExportLabel = 'XLSX'
  const exportBaseName = useMemo(() => {
    const fileName = filePath?.split('/').pop() ?? 'workbench-table'
    return fileName.replace(/\.(csv|tsv|xlsx|xls)$/i, '') || 'workbench-table'
  }, [filePath])

  const emitTableChange = (nextTableData: WorkbenchTableData) => {
    const serializedTable = serializeDelimitedTable(nextTableData, delimiter)

    onTableDataChange?.(nextTableData)
    onChange?.(serializedTable)
  }

  const updateTable = (updater: typeof tableData | ((current: typeof tableData) => typeof tableData)) => {
    const nextTable = typeof updater === 'function' ? updater(tableData) : updater
    emitTableChange(nextTable)
  }

  const handleHeaderChange = (columnIndex: number, nextValue: string) => {
    updateTable((current) => ({
      ...current,
      columns: current.columns.map((column, index) => (index === columnIndex ? nextValue : column)),
    }))
  }

  const handleCellChange = (rowIndex: number, columnIndex: number, nextValue: string) => {
    updateTable((current) => ({
      ...current,
      rows: current.rows.map((row, currentRowIndex) =>
        currentRowIndex === rowIndex ? row.map((cell, currentColumnIndex) => (currentColumnIndex === columnIndex ? nextValue : cell)) : row
      ),
    }))
  }

  const handleAddRow = () => {
    updateTable((current) => ({
      ...current,
      rows: [...current.rows, Array.from({ length: current.columns.length }, () => '')],
    }))
  }

  const handleAddColumn = () => {
    updateTable((current) => {
      const nextColumnIndex = current.columns.length + 1
      return {
        columns: [...current.columns, `column_${nextColumnIndex}`],
        rows: current.rows.map((row) => [...row, '']),
      }
    })
  }

  const safeTableData = tableData.columns.length > 0 ? tableData : createDefaultWorkbenchTableData()

  const handleImportSelection = async (
    event: ChangeEvent<HTMLInputElement>
  ) => {
    const nextFile = event.target.files?.[0]

    event.target.value = ''
    if (!nextFile) {
      return
    }

    setImportError(null)
    setIsImporting(true)

    try {
      const importedTableData = await parseTableDataFile(nextFile)
      emitTableChange(importedTableData)
    } catch (error) {
      setImportError(
        error instanceof Error ? error.message : 'Unable to import this spreadsheet.'
      )
    } finally {
      setIsImporting(false)
    }
  }

  const handleExport = async (format: 'csv' | 'tsv' | 'xlsx') => {
    setImportError(null)
    const blob = await exportTableDataToBlob(safeTableData, format)
    downloadBlob(blob, `${exportBaseName}.${format}`)
  }

  return (
    <div className={cn('flex h-full min-h-[24rem] flex-col overflow-hidden', className)}>
      <div className="border-shell flex flex-wrap items-center gap-2 border-b bg-[hsl(var(--app-shell-panel)/0.74)] px-4 py-3">
        <Button type="button" variant="outline" size="sm" onClick={handleAddRow} disabled={readOnly}>
          <Rows3 className="mr-2 h-4 w-4" />
          Add row
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={handleAddColumn} disabled={readOnly}>
          <Plus className="mr-2 h-4 w-4" />
          Add column
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => importInputRef.current?.click()}
          disabled={readOnly || isImporting}
        >
          {isImporting ? (
            <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Upload className="mr-2 h-4 w-4" />
          )}
          Import sheet
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={() => handleExport(preferredTextExportFormat)}>
          <Download className="mr-2 h-4 w-4" />
          Export {preferredTextExportLabel}
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={() => handleExport(preferredExcelExportFormat)}>
          <FileSpreadsheet className="mr-2 h-4 w-4" />
          Export {preferredExcelExportLabel}
        </Button>
        <span className="ml-auto text-[11px] uppercase tracking-[0.22em] text-shell-muted">
          Structured table workspace · {safeTableData.columns.length} columns · {safeTableData.rows.length} rows · first-sheet values only
        </span>
        <input
          ref={importInputRef}
          type="file"
          accept=".csv,.tsv,.xlsx"
          aria-label="Import spreadsheet into workbench table"
          onChange={handleImportSelection}
          className="hidden"
        />
      </div>
      {importError && (
        <div className="border-b border-amber-300/50 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-700/40 dark:bg-amber-950/20 dark:text-amber-200">
          {importError}
        </div>
      )}
      <ScrollArea className="min-h-0 flex-1 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.96))] dark:bg-[linear-gradient(180deg,rgba(2,6,23,0.94),rgba(3,7,18,0.98))]">
        <div className="min-w-[48rem] p-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-16 text-xs uppercase tracking-[0.2em] text-muted-foreground">Row</TableHead>
                {safeTableData.columns.map((column, columnIndex) => (
                  <TableHead key={`${column}-${columnIndex}`}>
                    <Input
                      value={column}
                      onChange={(event) => handleHeaderChange(columnIndex, event.target.value)}
                      aria-label={`Column ${columnIndex + 1}`}
                      disabled={readOnly}
                      className="h-9 min-w-[10rem] border-transparent bg-transparent px-0 font-medium shadow-none focus-visible:ring-0"
                    />
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {safeTableData.rows.map((row, rowIndex) => (
                <TableRow key={`row-${rowIndex}`}>
                  <TableCell className="align-top text-xs font-medium text-muted-foreground">{rowIndex + 1}</TableCell>
                  {row.map((cell, columnIndex) => (
                    <TableCell key={`cell-${rowIndex}-${columnIndex}`}>
                      <Input
                        value={cell}
                        onChange={(event) => handleCellChange(rowIndex, columnIndex, event.target.value)}
                        aria-label={`Row ${rowIndex + 1}, column ${columnIndex + 1}`}
                        disabled={readOnly}
                        className="min-w-[10rem] border-slate-200/70 bg-white/80 dark:border-slate-800 dark:bg-slate-950/50"
                      />
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </ScrollArea>
    </div>
  )
}