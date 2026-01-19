import type { BreakdownViewModel } from '@/types/resultsViewModel';

export interface RiskBreakdownProps extends BreakdownViewModel {}

export default function RiskBreakdown(props: RiskBreakdownProps) {
  return (
    <div>
      <h2>Risk distribution across operational and environmental layers</h2>
      <p style={{ fontStyle: 'italic', marginBottom: '1.5em', color: '#4b5563' }}>
        The breakdown below shows how different layers contribute to the overall risk profile.
      </p>

      <div style={{ marginBottom: '2em' }}>
        <h3 style={{ fontSize: '1.1em', fontWeight: '600', marginBottom: '0.75em', color: '#374151' }}>
          Risk Layers
        </h3>
        {props.layers.length === 0 ? (
          <p style={{ color: '#6b7280', fontStyle: 'italic' }}>No layer data available.</p>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {props.layers.map((layer, index) => (
              <li
                key={index}
                style={{
                  borderBottom: '1px solid #e5e7eb',
                  padding: '0.75em 0',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <strong style={{ color: '#111827' }}>{layer.name}</strong>
                <div style={{ display: 'flex', gap: '1.5em', fontSize: '0.95em', color: '#6b7280' }}>
                  <span>
                    Score: <strong style={{ color: '#374151' }}>{layer.score}</strong>
                  </span>
                  <span>
                    Contribution: <strong style={{ color: '#374151' }}>{layer.contribution}%</strong>
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <h3 style={{ fontSize: '1.1em', fontWeight: '600', marginBottom: '0.75em', color: '#374151' }}>
          Risk Factors
        </h3>
        {Object.keys(props.factors).length === 0 ? (
          <p style={{ color: '#6b7280', fontStyle: 'italic' }}>No factor data available.</p>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: '0.75em',
            }}
          >
            {Object.entries(props.factors).map(([key, value]) => (
              <div
                key={key}
                style={{
                  border: '1px solid #e5e7eb',
                  padding: '0.75em',
                  borderRadius: '4px',
                  backgroundColor: '#f9fafb',
                }}
              >
                <div style={{ fontSize: '0.85em', color: '#6b7280', marginBottom: '0.25em' }}>{key}</div>
                <div style={{ fontSize: '1.1em', fontWeight: '600', color: '#111827' }}>{value}%</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

