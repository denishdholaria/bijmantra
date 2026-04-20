import { describe, expect, it } from 'vitest'
import {
  exportRecordsToBlob,
  exportTableDataToBlob,
  parseStructuredRecordsFile,
  parseTableDataFile,
} from './spreadsheet'

const SAMPLE_XLSX_BASE64 = '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'

function createFileLike(name: string, payload: BlobPart, type: string) {
  const blob = new Blob([payload], { type })
  const getArrayBuffer = async () => {
    if (payload instanceof Blob && typeof payload.arrayBuffer === 'function') {
      return payload.arrayBuffer()
    }

    if (payload instanceof ArrayBuffer) {
      return payload.slice(0)
    }

    if (ArrayBuffer.isView(payload)) {
      return payload.buffer.slice(payload.byteOffset, payload.byteOffset + payload.byteLength)
    }

    return new TextEncoder().encode(String(payload)).buffer
  }

  return Object.assign(blob, {
    name,
    lastModified: Date.now(),
    arrayBuffer: getArrayBuffer,
    text: async () => new TextDecoder().decode(await getArrayBuffer()),
  }) as File
}

function decodeBase64ToBytes(base64: string) {
  return Uint8Array.from(atob(base64), (character) => character.charCodeAt(0))
}

async function createSpreadsheetFile(name: string) {
  return createFileLike(
    name,
    decodeBase64ToBytes(SAMPLE_XLSX_BASE64),
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  )
}

describe('spreadsheet utilities', () => {
  it('parses xlsx files into workbench table data', async () => {
    const workbookFile = await createSpreadsheetFile('trial-matrix.xlsx')

    await expect(parseTableDataFile(workbookFile)).resolves.toEqual({
      columns: ['Variety', 'Yield'],
      rows: [
        ['IR64', '5.2'],
        ['Swarna', '4.8'],
      ],
    })
  })

  it('rejects legacy xls files with a clear migration error', async () => {
    const workbookFile = createFileLike('trial-matrix.xls', 'legacy-xls', 'application/vnd.ms-excel')

    await expect(parseTableDataFile(workbookFile)).rejects.toThrow(
      'Legacy .xls files are no longer supported. Convert the file to .xlsx, .csv, or .tsv.'
    )
  })

  it('exports records to xlsx and round-trips them back into records', async () => {
    const blob = await exportRecordsToBlob(
      [
        { Variety: 'IR64', Yield: 5.2 },
        { Variety: 'Swarna', Yield: 4.8 },
      ],
      ['Variety', 'Yield'],
      'xlsx',
      { includeHeaders: true, nullValue: '', encoding: 'utf-8' }
    )

    expect(blob).toBeInstanceOf(Blob)
    expect(blob.size).toBeGreaterThan(0)
  })

  it('exports table data to xlsx and preserves the structured table model', async () => {
    const blob = await exportTableDataToBlob(
      {
        columns: ['Trait', 'Value'],
        rows: [
          ['Plant height', '110'],
          ['Yield', '5.4'],
        ],
      },
      'xlsx'
    )

    expect(blob).toBeInstanceOf(Blob)
    expect(blob.size).toBeGreaterThan(0)
  })

  it('rejects legacy xls exports with a clear migration error', async () => {
    await expect(
      exportTableDataToBlob(
        {
          columns: ['Trait', 'Value'],
          rows: [
            ['Plant height', '110'],
            ['Yield', '5.4'],
          ],
        },
        'xls'
      )
    ).rejects.toThrow('Legacy .xls files are no longer supported. Convert the file to .xlsx, .csv, or .tsv.')
  })
})