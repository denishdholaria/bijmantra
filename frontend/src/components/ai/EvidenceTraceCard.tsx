/**
 * EvidenceTraceCard — Stage B
 *
 * Renders the REEVU evidence envelope metadata as a collapsible
 * card below each assistant message.  Displays:
 *  - confidence score (colour-coded)
 *  - evidence refs (count + expandable list)
 *  - calculation steps (if any)
 *  - policy flags (warnings)
 *  - missing-data gaps
 */

import React, { useState } from 'react';

/* ── Types --------------------------------------------------------- */

export interface EvidenceRef {
    source_type: string;
    entity_id: string;
    retrieved_at?: string;
    query_or_method?: string;
    freshness_seconds?: number | null;
}

export interface CalculationStep {
    step_id: string;
    formula?: string | null;
    inputs?: Record<string, unknown> | null;
}

export interface UncertaintyInfo {
    confidence?: number | null;
    missing_data?: string[];
}

export interface ClaimTrace {
    statement: string;
    support_type: 'retrieval_backed' | 'calculation_backed' | 'model_synthesis';
    evidence_refs?: string[];
    calculation_ids?: string[];
}

export interface EvidenceEnvelope {
    claims: string[];
    claim_traces?: ClaimTrace[];
    evidence_refs: EvidenceRef[];
    calculation_steps: CalculationStep[];
    uncertainty: UncertaintyInfo;
    missing_evidence_signals?: string[];
    policy_flags: string[];
}

/* ── Helpers -------------------------------------------------------- */

function confidenceColor(c: number | null | undefined): string {
    if (c == null) return 'var(--text-muted, #888)';
    if (c >= 0.8) return 'var(--color-success, #22c55e)';
    if (c >= 0.5) return 'var(--color-warning, #f59e0b)';
    return 'var(--color-error, #ef4444)';
}

function confidenceLabel(c: number | null | undefined): string {
    if (c == null) return 'Unknown';
    if (c >= 0.8) return 'High';
    if (c >= 0.5) return 'Medium';
    return 'Low';
}

function pluralize(count: number, singular: string, plural: string): string {
    return `${count} ${count === 1 ? singular : plural}`;
}

function formatSourceType(sourceType: string | null | undefined): string {
    const normalized = (sourceType ?? '').trim().toLowerCase();
    if (normalized === 'database') return 'Database';
    if (normalized === 'function') return 'Function';
    if (normalized === 'rag') return 'Retrieved Context';
    if (normalized === 'api') return 'API';
    if (normalized === 'external') return 'External';
    if (!normalized) return 'Unknown';
    return normalized
        .split(/[_\s-]+/)
        .filter(Boolean)
        .map(token => token.charAt(0).toUpperCase() + token.slice(1))
        .join(' ');
}

function getSourceLabels(refs: EvidenceRef[]): string[] {
    return Array.from(new Set(refs.map(ref => formatSourceType(ref.source_type))));
}

function buildSourceCue(refs: EvidenceRef[]): string {
    const labels = getSourceLabels(refs);
    return labels.length > 0 ? labels.join(' + ') : 'none';
}

function buildCalculationCue(steps: CalculationStep[]): string {
    return steps.length > 0 ? pluralize(steps.length, 'step', 'steps') : 'none';
}

function buildUncertaintyCue(
    uncertainty: UncertaintyInfo | null | undefined,
    missingEvidenceSignals: string[] | undefined,
): string {
    const confidence = confidenceLabel(uncertainty?.confidence);
    const issueCount = (uncertainty?.missing_data?.length ?? 0) + (missingEvidenceSignals?.length ?? 0);
    return issueCount > 0 ? `${confidence} · ${pluralize(issueCount, 'issue', 'issues')}` : confidence;
}

function groupClaimTraces(claimTraces: ClaimTrace[] | undefined): Record<ClaimTrace['support_type'], ClaimTrace[]> {
    return (claimTraces ?? []).reduce<Record<ClaimTrace['support_type'], ClaimTrace[]>>(
        (groups, claimTrace) => {
            groups[claimTrace.support_type].push(claimTrace);
            return groups;
        },
        {
            retrieval_backed: [],
            calculation_backed: [],
            model_synthesis: [],
        },
    );
}

function claimSupportTitle(supportType: ClaimTrace['support_type']): string {
    if (supportType === 'retrieval_backed') return 'Retrieval-Backed Claims';
    if (supportType === 'calculation_backed') return 'Calculation-Backed Claims';
    return 'Model Synthesis Text';
}

function claimSupportBadge(supportType: ClaimTrace['support_type']): string {
    if (supportType === 'retrieval_backed') return 'Retrieved';
    if (supportType === 'calculation_backed') return 'Computed';
    return 'Synthesis';
}

/* ── Component ------------------------------------------------------ */

interface Props {
    envelope: EvidenceEnvelope;
}

const EvidenceTraceCard: React.FC<Props> = ({ envelope }) => {
    const [expanded, setExpanded] = useState(false);
    const conf = envelope.uncertainty?.confidence;
    const hasFlags = envelope.policy_flags.length > 0;
    const hasMissing = (envelope.uncertainty?.missing_data?.length ?? 0) > 0;
    const hasMissingEvidenceSignals = (envelope.missing_evidence_signals?.length ?? 0) > 0;
    const sourceCue = buildSourceCue(envelope.evidence_refs);
    const calculationCue = buildCalculationCue(envelope.calculation_steps);
    const uncertaintyCue = buildUncertaintyCue(envelope.uncertainty, envelope.missing_evidence_signals);
    const claimTraceGroups = groupClaimTraces(envelope.claim_traces);
    const hasClaimTraces = Object.values(claimTraceGroups).some(group => group.length > 0);

    return (
        <div style={cardStyle}>
            {/* Header — always visible */}
            <button
                onClick={() => setExpanded((p) => !p)}
                style={headerStyle}
                aria-expanded={expanded}
                aria-label="Toggle evidence trace details"
            >
                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span
                        style={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            background: confidenceColor(conf),
                            display: 'inline-block',
                        }}
                    />
                    <span style={{ fontWeight: 600, fontSize: 12 }}>
                        Evidence · {confidenceLabel(conf)}
                    </span>
                </span>

                <span style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 11, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                    <span title="Source trust cue">Source: {sourceCue}</span>
                    <span title="Calculation trust cue">Calculation: {calculationCue}</span>
                    <span title="Uncertainty trust cue">Uncertainty: {uncertaintyCue}</span>
                    <span title="Evidence refs">{envelope.evidence_refs.length} refs</span>
                    {hasFlags && (
                        <span style={{ color: 'var(--color-warning, #f59e0b)' }} title="Policy flags">
                            ⚠ {envelope.policy_flags.length}
                        </span>
                    )}
                    <span style={{ fontSize: 10 }}>{expanded ? '▲' : '▼'}</span>
                </span>
            </button>

            {/* Body — expandable */}
            {expanded && (
                <div style={bodyStyle}>
                    <section style={sectionStyle}>
                        <h4 style={sectionTitleStyle}>Trust Cues</h4>
                        <dl style={detailListStyle}>
                            <div>
                                <dt style={detailTermStyle}>Source coverage</dt>
                                <dd style={detailDescriptionStyle}>{sourceCue}</dd>
                            </div>
                            <div>
                                <dt style={detailTermStyle}>Calculation provenance</dt>
                                <dd style={detailDescriptionStyle}>{calculationCue}</dd>
                            </div>
                            <div>
                                <dt style={detailTermStyle}>Uncertainty</dt>
                                <dd style={detailDescriptionStyle}>{uncertaintyCue}</dd>
                            </div>
                        </dl>
                    </section>

                    {/* Claims */}
                    {hasClaimTraces ? (
                        <section style={sectionStyle}>
                            <h4 style={sectionTitleStyle}>Claim Support</h4>
                            {(['retrieval_backed', 'calculation_backed', 'model_synthesis'] as const).map(supportType => {
                                const traces = claimTraceGroups[supportType];
                                if (traces.length === 0) {
                                    return null;
                                }

                                return (
                                    <div key={supportType} style={claimTraceSectionStyle}>
                                        <h5 style={claimTraceTitleStyle}>
                                            {claimSupportTitle(supportType)} ({traces.length})
                                        </h5>
                                        <ul style={listStyle}>
                                            {traces.map((claimTrace, i) => (
                                                <li key={`${supportType}-${i}`} style={listItemStyle}>
                                                    <div style={claimTraceStatementStyle}>
                                                        <span style={claimTraceBadgeStyle}>{claimSupportBadge(supportType)}</span>
                                                        <span>{claimTrace.statement}</span>
                                                    </div>
                                                    {((claimTrace.evidence_refs?.length ?? 0) > 0 || (claimTrace.calculation_ids?.length ?? 0) > 0) && (
                                                        <div style={evidenceMetaStyle}>
                                                            {(claimTrace.evidence_refs?.length ?? 0) > 0 && (
                                                                <span>Refs: {(claimTrace.evidence_refs ?? []).join(', ')}</span>
                                                            )}
                                                            {(claimTrace.calculation_ids?.length ?? 0) > 0 && (
                                                                <span>Calcs: {(claimTrace.calculation_ids ?? []).join(', ')}</span>
                                                            )}
                                                        </div>
                                                    )}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                );
                            })}
                        </section>
                    ) : envelope.claims.length > 0 && (
                        <section style={sectionStyle}>
                            <h4 style={sectionTitleStyle}>Claims ({envelope.claims.length})</h4>
                            <ul style={listStyle}>
                                {envelope.claims.map((c, i) => (
                                    <li key={i} style={listItemStyle}>{c}</li>
                                ))}
                            </ul>
                        </section>
                    )}

                    {/* Evidence Refs */}
                    {envelope.evidence_refs.length > 0 && (
                        <section style={sectionStyle}>
                            <h4 style={sectionTitleStyle}>Evidence ({envelope.evidence_refs.length})</h4>
                            <ul style={listStyle}>
                                {envelope.evidence_refs.map((r, i) => (
                                    <li key={i} style={listItemStyle}>
                                        <div>
                                            <code style={codeStyle}>{formatSourceType(r.source_type)}</code> {r.entity_id}
                                            {r.freshness_seconds != null && (
                                                <span style={{ marginLeft: 6, opacity: 0.7, fontSize: 10 }}>
                                                    ({Math.round(r.freshness_seconds / 60)}m ago)
                                                </span>
                                            )}
                                        </div>
                                        {(r.query_or_method || r.retrieved_at) && (
                                            <div style={evidenceMetaStyle}>
                                                {r.query_or_method && <span>Method: {r.query_or_method}</span>}
                                                {r.retrieved_at && <span>Retrieved: {r.retrieved_at}</span>}
                                            </div>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        </section>
                    )}

                    {/* Calculations */}
                    {envelope.calculation_steps.length > 0 && (
                        <section style={sectionStyle}>
                            <h4 style={sectionTitleStyle}>Calculations</h4>
                            <ul style={listStyle}>
                                {envelope.calculation_steps.map((s, i) => (
                                    <li key={i} style={listItemStyle}>
                                        <code style={codeStyle}>{s.step_id}</code>
                                        {s.formula && <span style={{ marginLeft: 6, opacity: 0.7 }}>→ {s.formula}</span>}
                                    </li>
                                ))}
                            </ul>
                        </section>
                    )}

                    {/* Policy Flags */}
                    {hasFlags && (
                        <section style={sectionStyle}>
                            <h4 style={{ ...sectionTitleStyle, color: 'var(--color-warning, #f59e0b)' }}>
                                ⚠ Policy Flags
                            </h4>
                            <ul style={listStyle}>
                                {envelope.policy_flags.map((f, i) => (
                                    <li key={i} style={{ ...listItemStyle, color: 'var(--color-warning, #f59e0b)' }}>
                                        {f}
                                    </li>
                                ))}
                            </ul>
                        </section>
                    )}

                    {/* Missing Evidence Signals */}
                    {hasMissingEvidenceSignals && (
                        <section style={sectionStyle}>
                            <h4 style={{ ...sectionTitleStyle, color: 'var(--color-warning, #f59e0b)' }}>
                                Missing Evidence Signals
                            </h4>
                            <ul style={listStyle}>
                                {(envelope.missing_evidence_signals ?? []).map((signal, i) => (
                                    <li key={i} style={{ ...listItemStyle, color: 'var(--color-warning, #f59e0b)' }}>
                                        {signal}
                                    </li>
                                ))}
                            </ul>
                        </section>
                    )}

                    {/* Missing Data */}
                    {hasMissing && (
                        <section style={sectionStyle}>
                            <h4 style={sectionTitleStyle}>Missing Data</h4>
                            <ul style={listStyle}>
                                {envelope.uncertainty.missing_data!.map((m, i) => (
                                    <li key={i} style={listItemStyle}>{m}</li>
                                ))}
                            </ul>
                        </section>
                    )}
                </div>
            )}
        </div>
    );
};

export default EvidenceTraceCard;

/* ── Inline styles -------------------------------------------------- */

const cardStyle: React.CSSProperties = {
    border: '1px solid var(--border-color, rgba(255,255,255,0.08))',
    borderRadius: 8,
    marginTop: 6,
    overflow: 'hidden',
    fontSize: 12,
    background: 'var(--card-bg, rgba(255,255,255,0.03))',
};

const headerStyle: React.CSSProperties = {
    width: '100%',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '6px 10px',
    cursor: 'pointer',
    background: 'transparent',
    border: 'none',
    color: 'inherit',
};

const bodyStyle: React.CSSProperties = {
    padding: '4px 10px 8px',
    borderTop: '1px solid var(--border-color, rgba(255,255,255,0.06))',
};

const sectionStyle: React.CSSProperties = {
    marginBottom: 6,
};

const sectionTitleStyle: React.CSSProperties = {
    margin: '4px 0 2px',
    fontSize: 11,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
    opacity: 0.7,
};

const listStyle: React.CSSProperties = {
    listStyle: 'none',
    padding: 0,
    margin: 0,
};

const listItemStyle: React.CSSProperties = {
    padding: '1px 0',
    fontSize: 11,
};

const codeStyle: React.CSSProperties = {
    fontFamily: 'monospace',
    fontSize: 10,
    background: 'var(--code-bg, rgba(255,255,255,0.06))',
    padding: '1px 4px',
    borderRadius: 3,
};

const detailListStyle: React.CSSProperties = {
    display: 'grid',
    gap: 6,
    margin: 0,
};

const detailTermStyle: React.CSSProperties = {
    fontSize: 10,
    fontWeight: 600,
    letterSpacing: 0.3,
    opacity: 0.7,
    textTransform: 'uppercase',
};

const detailDescriptionStyle: React.CSSProperties = {
    margin: '2px 0 0',
    fontSize: 11,
};

const evidenceMetaStyle: React.CSSProperties = {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 2,
    marginLeft: 4,
    fontSize: 10,
    opacity: 0.75,
};

const claimTraceSectionStyle: React.CSSProperties = {
    marginTop: 8,
};

const claimTraceTitleStyle: React.CSSProperties = {
    margin: '0 0 4px',
    fontSize: 11,
    fontWeight: 600,
};

const claimTraceStatementStyle: React.CSSProperties = {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 6,
    alignItems: 'center',
};

const claimTraceBadgeStyle: React.CSSProperties = {
    border: '1px solid var(--border-color, rgba(255,255,255,0.12))',
    borderRadius: 999,
    fontSize: 10,
    padding: '1px 6px',
    opacity: 0.85,
};
