function readBlobWithFileReader<T>(blob: Blob, mode: 'text' | 'arrayBuffer') {
  return new Promise<T>((resolve, reject) => {
    const reader = new FileReader()

    reader.onerror = () => {
      reject(reader.error ?? new Error(`Unable to read blob as ${mode}`))
    }

    reader.onload = () => {
      resolve(reader.result as T)
    }

    if (mode === 'text') {
      reader.readAsText(blob)
      return
    }

    reader.readAsArrayBuffer(blob)
  })
}

export async function readBlobAsText(blob: Blob) {
  const readableBlob = blob as Blob & {
    text?: () => Promise<string>
  }

  if (typeof readableBlob.text === 'function') {
    return readableBlob.text()
  }

  if (typeof FileReader !== 'undefined') {
    return readBlobWithFileReader<string>(blob, 'text')
  }

  return new Response(blob).text()
}

export async function readBlobAsArrayBuffer(blob: Blob) {
  const readableBlob = blob as Blob & {
    arrayBuffer?: () => Promise<ArrayBuffer>
  }

  if (typeof readableBlob.arrayBuffer === 'function') {
    return readableBlob.arrayBuffer()
  }

  if (typeof Response !== 'undefined') {
    return new Response(blob).arrayBuffer()
  }

  if (typeof FileReader !== 'undefined') {
    return readBlobWithFileReader<ArrayBuffer>(blob, 'arrayBuffer')
  }

  throw new Error('Unable to read blob as arrayBuffer')
}