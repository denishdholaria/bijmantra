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

export interface EvidenceEnvelope {
    claims: string[];
    evidence_refs: EvidenceRef[];
    calculation_steps: CalculationStep[];
    uncertainty: UncertaintyInfo;
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

/* ── Component ------------------------------------------------------ */

interface Props {
    envelope: EvidenceEnvelope;
}

const EvidenceTraceCard: React.FC<Props> = ({ envelope }) => {
    const [expanded, setExpanded] = useState(false);
    const conf = envelope.uncertainty?.confidence;
    const hasFlags = envelope.policy_flags.length > 0;
    const hasMissing = (envelope.uncertainty?.missing_data?.length ?? 0) > 0;

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

                <span style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 11 }}>
                    <span title="Evidence refs">{envelope.evidence_refs.length} refs</span>
                    {envelope.calculation_steps.length > 0 && (
                        <span title="Calculation steps">{envelope.calculation_steps.length} calcs</span>
                    )}
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
                    {/* Claims */}
                    {envelope.claims.length > 0 && (
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
                                        <code style={codeStyle}>{r.source_type}</code> {r.entity_id}
                                        {r.freshness_seconds != null && (
                                            <span style={{ marginLeft: 6, opacity: 0.7, fontSize: 10 }}>
                                                ({Math.round(r.freshness_seconds / 60)}m ago)
                                            </span>
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
