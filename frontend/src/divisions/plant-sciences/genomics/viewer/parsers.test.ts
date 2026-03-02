import { describe, it, expect } from 'vitest';
import { parseFasta, parseFastq, parseGff3 } from './parsers';

describe('Parsers', () => {
  it('parses FASTA correctly', () => {
    const fasta = `>seq1 description
ATGC
ATGC
>seq2
GGCC`;
    const result = parseFasta(fasta);
    expect(result).toHaveLength(2);
    expect(result[0].id).toBe('seq1');
    expect(result[0].description).toBe('description');
    expect(result[0].sequence).toBe('ATGCATGC');
    expect(result[1].id).toBe('seq2');
    expect(result[1].sequence).toBe('GGCC');
  });

  it('parses FASTQ correctly', () => {
    const fastq = `@seq1 description
ATGC
+
IIII
@seq2
GGCC
+
JJJJ`;
    const result = parseFastq(fastq);
    expect(result).toHaveLength(2);
    expect(result[0].id).toBe('seq1');
    expect(result[0].sequence).toBe('ATGC');
    expect(result[0].quality).toBe('IIII');
    expect(result[1].id).toBe('seq2');
    expect(result[1].sequence).toBe('GGCC');
    expect(result[1].quality).toBe('JJJJ');
  });

  it('parses GFF3 correctly', () => {
    const gff = `##gff-version 3
seq1\tsource\tgene\t100\t200\t.\t+\t.\tID=gene1;Name=Gene 1`;
    const result = parseGff3(gff);
    expect(result).toHaveLength(1);
    expect(result[0].seqid).toBe('seq1');
    expect(result[0].type).toBe('gene');
    expect(result[0].start).toBe(100);
    expect(result[0].end).toBe(200);
    expect(result[0].attributes['ID']).toBe('gene1');
    expect(result[0].attributes['Name']).toBe('Gene 1');
  });
});
