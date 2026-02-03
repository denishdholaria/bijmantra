export interface SequenceRecord {
  id: string;
  description?: string;
  sequence: string;
  quality?: string; // For FASTQ
}

export interface GFFFeature {
  seqid: string;
  source: string;
  type: string;
  start: number;
  end: number;
  score: string | number;
  strand: string;
  phase: string | number;
  attributes: Record<string, string>;
}

export function parseFasta(content: string): SequenceRecord[] {
  const lines = content.split(/\r?\n/);
  const records: SequenceRecord[] = [];
  let currentRecord: SequenceRecord | null = null;

  for (const line of lines) {
    if (line.startsWith('>')) {
      if (currentRecord) {
        records.push(currentRecord);
      }
      const header = line.slice(1);
      const spaceIdx = header.indexOf(' ');
      const id = spaceIdx === -1 ? header : header.slice(0, spaceIdx);
      const description = spaceIdx === -1 ? undefined : header.slice(spaceIdx + 1);

      currentRecord = {
        id,
        description,
        sequence: '',
      };
    } else if (currentRecord) {
      currentRecord.sequence += line.trim();
    }
  }

  if (currentRecord) {
    records.push(currentRecord);
  }

  return records;
}

export function parseFastq(content: string): SequenceRecord[] {
  const lines = content.split(/\r?\n/).filter(l => l.length > 0);
  const records: SequenceRecord[] = [];

  for (let i = 0; i < lines.length; i += 4) {
    if (i + 3 >= lines.length) break;

    const header = lines[i];
    if (!header.startsWith('@')) continue;

    const idLine = header.slice(1);
    const spaceIdx = idLine.indexOf(' ');
    const id = spaceIdx === -1 ? idLine : idLine.slice(0, spaceIdx);
    const description = spaceIdx === -1 ? undefined : idLine.slice(spaceIdx + 1);

    const sequence = lines[i + 1].trim();
    // lines[i+2] is '+'
    const quality = lines[i + 3].trim();

    records.push({
      id,
      description,
      sequence,
      quality,
    });
  }

  return records;
}

export function parseGff3(content: string): GFFFeature[] {
  const lines = content.split(/\r?\n/);
  const features: GFFFeature[] = [];

  for (const line of lines) {
    if (line.startsWith('#') || line.trim() === '') continue;

    const columns = line.split('\t');
    if (columns.length < 9) continue;

    const attributesStr = columns[8];
    const attributes: Record<string, string> = {};

    attributesStr.split(';').forEach(attr => {
      const parts = attr.split('=');
      if (parts.length === 2) {
        attributes[parts[0]] = parts[1];
      }
    });

    features.push({
      seqid: columns[0],
      source: columns[1],
      type: columns[2],
      start: parseInt(columns[3], 10),
      end: parseInt(columns[4], 10),
      score: columns[5] === '.' ? '.' : parseFloat(columns[5]),
      strand: columns[6],
      phase: columns[7] === '.' ? '.' : parseInt(columns[7], 10),
      attributes,
    });
  }

  return features;
}
