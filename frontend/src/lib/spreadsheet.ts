import { readSheet } from 'read-excel-file/universal'
import writeExcelFile from 'write-excel-file/universal'

import { readBlobAsArrayBuffer, readBlobAsText } from '@/lib/blob'
import {
  createDefaultWorkbenchTableData,
  getWorkbenchTableDelimiter,
  parseDelimitedTable,
  serializeDelimitedTable,
  type WorkbenchTableData,
} from '@/lib/workbenchDocuments'

export type SpreadsheetFileFormat = 'csv' | 'tsv' | 'xlsx' | 'xls' | 'json'

type SpreadsheetExportOptions = {
  includeHeaders?: boolean
  nullValue?: string
  encoding?: string
}

const BINARY_SPREADSHEET_FORMATS = new Set<SpreadsheetFileFormat>(['xlsx', 'xls'])
const LEGACY_XLS_ERROR = 'Legacy .xls files are no longer supported. Convert the file to .xlsx, .csv, or .tsv.'

function getFileExtension(fileName?: string) {
  if (!fileName) {
    return ''
  }

  return fileName.split('.').pop()?.toLowerCase() ?? ''
}

function stringifyCellValue(value: unknown) {
  if (value === null || value === undefined) {
    return ''
  }

  if (value instanceof Date) {
    return value.toISOString()
  }

  return String(value)
}

function normalizeColumns(columns: string[], columnCount: number) {
  return Array.from({ length: Math.max(columnCount, 1) }, (_, index) => {
    const nextColumn = columns[index]?.trim() ?? ''
    return nextColumn.length > 0 ? nextColumn : `column_${index + 1}`
  })
}

function normalizeRows(rows: string[][], columnCount: number) {
  if (rows.length === 0) {
    return [Array.from({ length: columnCount }, () => '')]
  }

  return rows.map((row) =>
    Array.from({ length: columnCount }, (_, index) => row[index] ?? '')
  )
}

function escapeDelimitedCell(value: string, delimiter: string) {
  if (
    value.includes(delimiter) ||
    value.includes('"') ||
    value.includes('\n') ||
    value.includes('\r')
  ) {
    return `"${value.replace(/"/g, '""')}"`
  }

  return value
}

function serializeRows(rows: string[][], delimiter: string) {
  return rows
    .map((row) => row.map((value) => escapeDelimitedCell(value, delimiter)).join(delimiter))
    .join('\n')
}

function sheetRowsToTableData(rows: unknown[][]): WorkbenchTableData {
  if (rows.length === 0) {
    return createDefaultWorkbenchTableData()
  }

  const [headerRow, ...bodyRows] = rows
  const normalizedHeaderRow = Array.isArray(headerRow)
    ? headerRow.map((value) => stringifyCellValue(value))
    : []
  const normalizedBodyRows = bodyRows
    .filter((row) => Array.isArray(row))
    .map((row) => row.map((value) => stringifyCellValue(value)))
  const columnCount = Math.max(
    normalizedHeaderRow.length,
    ...normalizedBodyRows.map((row) => row.length),
    1
  )

  return {
    columns: normalizeColumns(normalizedHeaderRow, columnCount),
    rows: normalizeRows(normalizedBodyRows, columnCount),
  }
}

function tableDataToSheetRows(
  tableData: WorkbenchTableData,
  options: Pick<SpreadsheetExportOptions, 'includeHeaders'> = {}
) {
  const includeHeaders = options.includeHeaders ?? true
  const rows = normalizeRows(tableData.rows, Math.max(tableData.columns.length, 1))

  return includeHeaders ? [tableData.columns, ...rows] : rows
}

function normalizeWorkbookCellValue(value: unknown) {
  if (value === null || value === undefined || value === '') {
    return null
  }

  if (
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean' ||
    value instanceof Date
  ) {
    return value
  }

  return stringifyCellValue(value)
}

async function buildWorkbookBlob(
  rows: unknown[][],
  format: Extract<SpreadsheetFileFormat, 'xlsx' | 'xls'>
) {
  if (format === 'xls') {
    throw new Error(LEGACY_XLS_ERROR)
  }

  return writeExcelFile(
    rows.map((row) => row.map((value) => normalizeWorkbookCellValue(value))),
    {
      sheet: 'Sheet1',
    }
  )
}

export function inferSpreadsheetFileFormat(
  fileName?: string
): SpreadsheetFileFormat | null {
  const extension = getFileExtension(fileName)

  switch (extension) {
    case 'csv':
      return 'csv'
    case 'tsv':
      return 'tsv'
    case 'xlsx':
      return 'xlsx'
    case 'xls':
      return 'xls'
    case 'json':
      return 'json'
    default:
      return null
  }
}

export function isBinarySpreadsheetFormat(fileName?: string) {
  const format = inferSpreadsheetFileFormat(fileName)
  return format ? BINARY_SPREADSHEET_FORMATS.has(format) : false
}

export function tableDataToRecords(tableData: WorkbenchTableData) {
  return normalizeRows(tableData.rows, Math.max(tableData.columns.length, 1)).map((row) =>
    Object.fromEntries(
      normalizeColumns(tableData.columns, Math.max(tableData.columns.length, 1)).map(
        (column, columnIndex) => [column, row[columnIndex] ?? '']
      )
    )
  )
}

export function recordsToTableData(
  records: Record<string, unknown>[],
  columnOrder?: string[]
) {
  if (records.length === 0) {
    return createDefaultWorkbenchTableData()
  }

  const inferredColumns =
    columnOrder && columnOrder.length > 0
      ? columnOrder
      : Array.from(
          records.reduce((columns, record) => {
            Object.keys(record).forEach((key) => columns.add(key))
            return columns
          }, new Set<string>())
        )
  const normalizedColumns = normalizeColumns(inferredColumns, inferredColumns.length)

  return {
    columns: normalizedColumns,
    rows: normalizeRows(
      records.map((record) =>
        normalizedColumns.map((column) => stringifyCellValue(record[column]))
      ),
      normalizedColumns.length
    ),
  }
}

export async function parseTableDataFile(file: File): Promise<WorkbenchTableData> {
  const format = inferSpreadsheetFileFormat(file.name)

  switch (format) {
    case 'csv':
    case 'tsv': {
      const delimiter = format === 'tsv' ? '\t' : ','
      return parseDelimitedTable(await readBlobAsText(file), delimiter)
    }
    case 'xlsx': {
      const rows = await readSheet(await readBlobAsArrayBuffer(file))
      return sheetRowsToTableData(rows)
    }
    case 'xls':
      throw new Error(LEGACY_XLS_ERROR)
    default:
      throw new Error('Unsupported tabular file format')
  }
}

export async function parseStructuredRecordsFile(file: File) {
  const format = inferSpreadsheetFileFormat(file.name)

  if (format === 'json') {
    const parsed = JSON.parse(await readBlobAsText(file))
    return Array.isArray(parsed) ? parsed : [parsed]
  }

  return tableDataToRecords(await parseTableDataFile(file))
}

export async function exportTableDataToBlob(
  tableData: WorkbenchTableData,
  format: Extract<SpreadsheetFileFormat, 'csv' | 'tsv' | 'xlsx' | 'xls'>
) {
  if (format === 'csv' || format === 'tsv') {
    const delimiter = format === 'tsv' ? '\t' : ','
    return new Blob([serializeDelimitedTable(tableData, delimiter)], {
      type:
        format === 'tsv'
          ? 'text/tab-separated-values;charset=utf-8'
          : 'text/csv;charset=utf-8',
    })
  }

  return buildWorkbookBlob(tableDataToSheetRows(tableData), format)
}

export async function exportRecordsToBlob(
  data: Record<string, unknown>[],
  columns: string[],
  format: SpreadsheetFileFormat,
  options: SpreadsheetExportOptions = {}
) {
  const filteredData = data.map((row) =>
    Object.fromEntries(
      columns.map((column) => [
        column,
        row[column] === null || row[column] === undefined
          ? options.nullValue ?? ''
          : row[column],
      ])
    )
  )

  if (format === 'json') {
    return new Blob([JSON.stringify(filteredData, null, 2)], {
      type: 'application/json;charset=utf-8',
    })
  }

  const tableData = recordsToTableData(filteredData, columns)

  if (format === 'xlsx' || format === 'xls') {
    return buildWorkbookBlob(
      tableDataToSheetRows(tableData, { includeHeaders: options.includeHeaders }),
      format
    )
  }

  const delimiter = format === 'tsv' ? '\t' : ','
  const content = options.includeHeaders === false
    ? `${serializeRows(
        normalizeRows(tableData.rows, Math.max(tableData.columns.length, 1)),
        delimiter
      )}\n`
    : serializeDelimitedTable(tableData, delimiter)

  return new Blob([content], {
    type:
      format === 'tsv'
        ? `text/tab-separated-values;charset=${options.encoding ?? 'utf-8'}`
        : `text/csv;charset=${options.encoding ?? 'utf-8'}`,
  })
}

export function downloadBlob(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}