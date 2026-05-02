export type WorkbenchDocumentType = 'code' | 'prose' | 'table'

export type WorkbenchTableData = {
  columns: string[]
  rows: string[][]
}

type DocumentTypeDescriptor = {
  name?: string
  path?: string
  language?: string
  type?: WorkbenchDocumentType | null
  tableData?: WorkbenchTableData | null
}

const PROSE_EXTENSIONS = new Set(['md', 'markdown', 'txt'])
const TABLE_EXTENSIONS = new Set(['csv', 'tsv', 'xlsx', 'xls'])
const PROSE_LANGUAGES = new Set(['markdown'])

function getFileExtension(path?: string) {
  if (!path) {
    return ''
  }

  return path.split('.').pop()?.toLowerCase() ?? ''
}

function normalizeColumns(columns: string[]) {
  return columns.map((column, index) => {
    const trimmedColumn = column.trim()
    return trimmedColumn.length > 0 ? trimmedColumn : `column_${index + 1}`
  })
}

function normalizeRows(rows: string[][], columnCount: number) {
  return rows.map((row) => Array.from({ length: columnCount }, (_, index) => row[index] ?? ''))
}

function parseDelimitedLine(line: string, delimiter: string) {
  const values: string[] = []
  let currentValue = ''
  let isQuoted = false

  for (let index = 0; index < line.length; index += 1) {
    const character = line[index]
    const nextCharacter = line[index + 1]

    if (character === '"') {
      if (isQuoted && nextCharacter === '"') {
        currentValue += '"'
        index += 1
      } else {
        isQuoted = !isQuoted
      }
      continue
    }

    if (character === delimiter && !isQuoted) {
      values.push(currentValue)
      currentValue = ''
      continue
    }

    currentValue += character
  }

  values.push(currentValue)
  return values
}

function escapeDelimitedCell(value: string, delimiter: string) {
  if (value.includes('"') || value.includes('\n') || value.includes('\r') || value.includes(delimiter)) {
    return `"${value.replace(/"/g, '""')}"`
  }

  return value
}

export function getWorkbenchTableDelimiter(path?: string) {
  return getFileExtension(path) === 'tsv' ? '\t' : ','
}

export function createDefaultWorkbenchTableData(): WorkbenchTableData {
  return {
    columns: ['column_a', 'column_b', 'column_c'],
    rows: [['', '', '']],
  }
}

export function parseDelimitedTable(input: string, delimiter = ','): WorkbenchTableData {
  const trimmedInput = input.replace(/\r\n/g, '\n').trim()
  if (!trimmedInput) {
    return createDefaultWorkbenchTableData()
  }

  const lines = trimmedInput.split('\n').filter((line) => line.length > 0)
  if (lines.length === 0) {
    return createDefaultWorkbenchTableData()
  }

  const [headerLine, ...rowLines] = lines
  const rawColumns = parseDelimitedLine(headerLine, delimiter)
  const columns = normalizeColumns(rawColumns.length > 0 ? rawColumns : createDefaultWorkbenchTableData().columns)
  const rows = normalizeRows(
    rowLines.map((line) => parseDelimitedLine(line, delimiter)),
    columns.length
  )

  return {
    columns,
    rows: rows.length > 0 ? rows : [['', '', ''].slice(0, columns.length)],
  }
}

export function serializeDelimitedTable(tableData: WorkbenchTableData, delimiter = ',') {
  const columns = normalizeColumns(tableData.columns.length > 0 ? tableData.columns : createDefaultWorkbenchTableData().columns)
  const rows = normalizeRows(tableData.rows.length > 0 ? tableData.rows : [['', '', ''].slice(0, columns.length)], columns.length)
  const headerLine = columns.map((column) => escapeDelimitedCell(column, delimiter)).join(delimiter)
  const bodyLines = rows.map((row) => row.map((value) => escapeDelimitedCell(value, delimiter)).join(delimiter))
  return `${[headerLine, ...bodyLines].join('\n')}\n`
}

export function normalizeWorkbenchTableData(
  tableData?: WorkbenchTableData | null,
  rawContent = '',
  path?: string
): WorkbenchTableData {
  if (tableData && Array.isArray(tableData.columns) && Array.isArray(tableData.rows)) {
    const normalizedColumns = normalizeColumns(tableData.columns)
    return {
      columns: normalizedColumns,
      rows: normalizeRows(tableData.rows, normalizedColumns.length),
    }
  }

  return parseDelimitedTable(rawContent, getWorkbenchTableDelimiter(path))
}

export function inferWorkbenchDocumentType(descriptor: DocumentTypeDescriptor): WorkbenchDocumentType {
  if (descriptor.type) {
    return descriptor.type
  }

  if (descriptor.tableData) {
    return 'table'
  }

  const extension = getFileExtension(descriptor.path ?? descriptor.name)
  if (TABLE_EXTENSIONS.has(extension)) {
    return 'table'
  }

  if (PROSE_LANGUAGES.has(descriptor.language ?? '') || PROSE_EXTENSIONS.has(extension)) {
    return 'prose'
  }

  return 'code'
}

export function isWorkbenchProseDocument(type: WorkbenchDocumentType) {
  return type === 'prose'
}

export function isWorkbenchTableDocument(type: WorkbenchDocumentType) {
  return type === 'table'
}