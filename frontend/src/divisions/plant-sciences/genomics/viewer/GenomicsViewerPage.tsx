import React, { useState, useEffect } from 'react';
import { SequenceViewer } from './SequenceViewer';
import { CircularGenomeMap } from './CircularGenomeMap';
import { parseFasta, parseFastq, parseGff3, SequenceRecord, GFFFeature } from './parsers';
import { initWasm, BijmantraGenomicsWasm, AlignmentResult, MotifMatch } from '../../../../wasm';
import { FileText, Circle, Activity, Upload, Search, GitMerge } from 'lucide-react';

export default function GenomicsViewerPage() {
  const [activeTab, setActiveTab] = useState<'sequence' | 'map' | 'analysis'>('sequence');
  const [sequenceData, setSequenceData] = useState<SequenceRecord | null>(null);
  const [features, setFeatures] = useState<GFFFeature[]>([]);
  const [wasm, setWasm] = useState<BijmantraGenomicsWasm | null>(null);

  // Analysis State
  const [analysisMode, setAnalysisMode] = useState<'alignment' | 'motif'>('alignment');
  const [alignSeq1, setAlignSeq1] = useState('');
  const [alignSeq2, setAlignSeq2] = useState('');
  const [motifPattern, setMotifPattern] = useState('');
  const [alignmentResult, setAlignmentResult] = useState<AlignmentResult | null>(null);
  const [motifMatches, setMotifMatches] = useState<MotifMatch[]>([]);
  const [isWasmLoading, setIsWasmLoading] = useState(true);

  useEffect(() => {
    initWasm().then(w => {
      setWasm(w);
      setIsWasmLoading(false);
    });
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, type: 'fasta' | 'fastq' | 'gff3') => {
    const file = e.target.files?.[0];
    if (!file) return;

    const text = await file.text();

    if (type === 'fasta') {
      const records = parseFasta(text);
      if (records.length > 0) {
        setSequenceData(records[0]);
        // Auto-fill alignment input if empty
        if (!alignSeq1) setAlignSeq1(records[0].sequence.slice(0, 100));
      }
    } else if (type === 'fastq') {
      const records = parseFastq(text);
      if (records.length > 0) setSequenceData(records[0]);
    } else if (type === 'gff3') {
      const parsed = parseGff3(text);
      setFeatures(parsed);
    }
  };

  const runAlignment = () => {
    if (!wasm || !alignSeq1 || !alignSeq2) return;
    try {
      // Needleman-Wunsch global alignment
      const result = wasm.needleman_wunsch(alignSeq1, alignSeq2, 1, -1, -2);
      setAlignmentResult(result);
    } catch (err) {
      console.error(err);
      alert("WASM execution failed (check console)");
    }
  };

  const runSmithWaterman = () => {
    if (!wasm || !alignSeq1 || !alignSeq2) return;
    try {
      // Smith-Waterman local alignment
      const result = wasm.smith_waterman(alignSeq1, alignSeq2, 1, -1, -2);
      setAlignmentResult(result);
    } catch (err) {
      console.error(err);
      alert("WASM execution failed (check console)");
    }
  };

  const runMotifSearch = () => {
    if (!wasm || !sequenceData || !motifPattern) return;
    try {
      const results = wasm.search_motif(sequenceData.sequence, motifPattern);
      setMotifMatches(results);
    } catch (err) {
      console.error(err);
      alert("WASM execution failed (check console)");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm">
        <h1 className="text-xl font-bold flex items-center gap-2 text-slate-800">
          <Activity className="w-6 h-6 text-emerald-600" />
          Genomics Viewer
        </h1>
        <div className="text-xs text-slate-500 font-mono">
          WASM Status: {isWasmLoading ? 'Loading...' : (wasm && wasm.is_wasm_ready()) ? 'Ready' : 'Fallback (Build WASM)'}
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        {/* Controls */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-white rounded-lg shadow-sm border border-slate-200">
            <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
              <Upload className="w-4 h-4" /> Load Sequence (FASTA/FASTQ)
            </label>
            <input
              type="file"
              accept=".fasta,.fna,.fastq,.fq"
              onChange={(e) => handleFileUpload(e, e.target.files?.[0]?.name.endsWith('q') ? 'fastq' : 'fasta')}
              className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100"
            />
          </div>
          <div className="p-4 bg-white rounded-lg shadow-sm border border-slate-200">
            <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
              <Upload className="w-4 h-4" /> Load Annotations (GFF3)
            </label>
            <input
              type="file"
              accept=".gff,.gff3"
              onChange={(e) => handleFileUpload(e, 'gff3')}
              className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>
          <div className="p-4 bg-white rounded-lg shadow-sm border border-slate-200 flex items-center gap-2">
            <div className="text-sm">
              <div className="font-medium text-slate-700">Loaded Data</div>
              <div className="text-slate-500">
                {sequenceData ? `${sequenceData.id} (${sequenceData.sequence.length.toLocaleString()} bp)` : 'No sequence'}
              </div>
              <div className="text-slate-500">
                {features.length > 0 ? `${features.length} features` : 'No features'}
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-slate-200">
          <div className="flex gap-6">
            <button
              onClick={() => setActiveTab('sequence')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors ${
                activeTab === 'sequence'
                  ? 'border-emerald-500 text-emerald-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <FileText className="w-4 h-4" /> Sequence Viewer
            </button>
            <button
              onClick={() => setActiveTab('map')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors ${
                activeTab === 'map'
                  ? 'border-emerald-500 text-emerald-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Circle className="w-4 h-4" /> Circular Map
            </button>
            <button
              onClick={() => setActiveTab('analysis')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors ${
                activeTab === 'analysis'
                  ? 'border-emerald-500 text-emerald-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Activity className="w-4 h-4" /> Analysis (WASM)
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="min-h-[500px]">
          {activeTab === 'sequence' && (
            sequenceData ? (
              <SequenceViewer data={sequenceData} />
            ) : (
              <div className="text-center py-20 text-slate-400 bg-white rounded-lg border border-slate-200 border-dashed">
                <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Upload a FASTA/FASTQ file to view sequence.</p>
              </div>
            )
          )}

          {activeTab === 'map' && (
            sequenceData ? (
              <div className="flex justify-center bg-white rounded-lg border border-slate-200 p-8">
                <CircularGenomeMap
                  sequenceLength={sequenceData.sequence.length}
                  features={features}
                />
              </div>
            ) : (
              <div className="text-center py-20 text-slate-400 bg-white rounded-lg border border-slate-200 border-dashed">
                <Circle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Upload a FASTA/FASTQ file to view map.</p>
              </div>
            )
          )}

          {activeTab === 'analysis' && (
            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <div className="flex gap-4 mb-6">
                <button
                  onClick={() => setAnalysisMode('alignment')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    analysisMode === 'alignment' ? 'bg-emerald-100 text-emerald-700' : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  Sequence Alignment
                </button>
                <button
                  onClick={() => setAnalysisMode('motif')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    analysisMode === 'motif' ? 'bg-emerald-100 text-emerald-700' : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  Motif Search
                </button>
              </div>

              {analysisMode === 'alignment' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Sequence 1</label>
                      <textarea
                        value={alignSeq1}
                        onChange={e => setAlignSeq1(e.target.value)}
                        className="w-full h-32 p-3 border border-slate-300 rounded-lg font-mono text-xs"
                        placeholder="Enter sequence or load from file..."
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Sequence 2</label>
                      <textarea
                        value={alignSeq2}
                        onChange={e => setAlignSeq2(e.target.value)}
                        className="w-full h-32 p-3 border border-slate-300 rounded-lg font-mono text-xs"
                        placeholder="Enter comparison sequence..."
                      />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={runAlignment}
                      className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 flex items-center gap-2"
                    >
                      <GitMerge className="w-4 h-4" /> Global Alignment (Needleman-Wunsch)
                    </button>
                    <button
                      onClick={runSmithWaterman}
                      className="px-4 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 flex items-center gap-2"
                    >
                      <GitMerge className="w-4 h-4" /> Local Alignment (Smith-Waterman)
                    </button>
                  </div>

                  {alignmentResult && (
                    <div className="mt-6 p-4 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="text-sm font-bold text-slate-700 mb-2">Score: {alignmentResult.score}</div>
                      <div className="font-mono text-xs overflow-x-auto whitespace-nowrap p-2 bg-white border border-slate-200 rounded">
                        <div className="tracking-[0.2em]">{alignmentResult.align1}</div>
                        <div className="tracking-[0.2em]">{alignmentResult.align2}</div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {analysisMode === 'motif' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Motif Pattern</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={motifPattern}
                        onChange={e => setMotifPattern(e.target.value)}
                        className="flex-1 px-3 py-2 border border-slate-300 rounded-lg font-mono text-sm"
                        placeholder="e.g. ATGC"
                      />
                      <button
                        onClick={runMotifSearch}
                        className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 flex items-center gap-2"
                      >
                        <Search className="w-4 h-4" /> Search
                      </button>
                    </div>
                  </div>

                  {motifMatches.length > 0 ? (
                    <div className="mt-4">
                      <h3 className="text-sm font-medium text-slate-700 mb-2">Found {motifMatches.length} matches</h3>
                      <div className="max-h-60 overflow-auto border border-slate-200 rounded-lg">
                        <table className="w-full text-sm text-left">
                          <thead className="bg-slate-50 text-slate-500">
                            <tr>
                              <th className="px-4 py-2">Start</th>
                              <th className="px-4 py-2">End</th>
                              <th className="px-4 py-2">Match</th>
                            </tr>
                          </thead>
                          <tbody>
                            {motifMatches.map((m, i) => (
                              <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                                <td className="px-4 py-2 font-mono text-xs">{m.start}</td>
                                <td className="px-4 py-2 font-mono text-xs">{m.end}</td>
                                <td className="px-4 py-2 font-mono text-xs text-emerald-600">{m.match_str}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-slate-500 italic mt-4">
                      {motifPattern ? 'No matches found.' : 'Enter a motif to search.'}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
