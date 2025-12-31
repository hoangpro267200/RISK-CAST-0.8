export interface RiskTimelineProps {
  projections: Array<{
    date: string;
    p10: number;
    p50: number;
    p90: number;
    phase: string;
  }>;
  hasData: boolean;
}

export default function RiskTimeline(props: RiskTimelineProps) {
  if (!props.hasData) {
    return (
      <div>
        <h2>Projected risk evolution across the shipment journey</h2>
        <p style={{ fontStyle: 'italic', color: '#6b7280' }}>
          Insufficient data to project risk evolution over time.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h2>Projected risk evolution across the shipment journey</h2>
      <p style={{ fontStyle: 'italic', marginBottom: '1.5em', color: '#4b5563' }}>
        Risk is expected to fluctuate across the shipment lifecycle, with potential peaks during specific phases.
      </p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1em' }}>
        {props.projections.map((projection, index) => (
          <div
            key={index}
            style={{
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              padding: '1em',
              backgroundColor: '#f9fafb',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75em' }}>
              <strong style={{ fontSize: '1.1em', color: '#111827' }}>{projection.date}</strong>
              {projection.phase && (
                <span style={{ fontSize: '0.9em', color: '#6b7280', fontStyle: 'italic' }}>
                  {projection.phase}
                </span>
              )}
            </div>
            <div style={{ display: 'flex', gap: '1.5em', fontSize: '0.95em' }}>
              <div>
                <span style={{ color: '#6b7280' }}>P10 (optimistic):</span>{' '}
                <strong style={{ color: '#10b981' }}>{projection.p10}</strong>
              </div>
              <div>
                <span style={{ color: '#6b7280' }}>P50 (median):</span>{' '}
                <strong style={{ color: '#374151' }}>{projection.p50}</strong>
              </div>
              <div>
                <span style={{ color: '#6b7280' }}>P90 (pessimistic):</span>{' '}
                <strong style={{ color: '#dc2626' }}>{projection.p90}</strong>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

