import type { RiskDriverViewModel } from '@/types/resultsViewModel';

export interface RiskDriversProps {
  drivers: RiskDriverViewModel[];
}

export default function RiskDrivers(props: RiskDriversProps) {
  if (props.drivers.length === 0) {
    return (
      <div>
        <h2>Primary risk drivers contributing to the overall risk score</h2>
        <p style={{ fontStyle: 'italic', color: '#6b7280' }}>
          No dominant risk drivers identified. Risk is distributed across multiple minor factors.
        </p>
      </div>
    );
  }

  // Visual emphasis: highlight top drivers (first in array) and high impact (presentational only)
  const isTopDriver = (index: number) => index < 3;
  const isHighImpact = (impact: number) => impact >= 70;

  return (
    <div>
      <h2>Primary risk drivers contributing to the overall risk score</h2>
      <p style={{ fontStyle: 'italic', marginBottom: '1.5em', color: '#4b5563' }}>
        The overall risk is primarily driven by the following factors, ranked by impact.
      </p>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {props.drivers.map((driver, index) => (
          <li
            key={index}
            style={{
              borderLeft: isTopDriver(index) ? '4px solid #dc2626' : '2px solid #e5e7eb',
              paddingLeft: '1em',
              marginBottom: '1em',
              paddingTop: isTopDriver(index) ? '0.5em' : '0.25em',
              paddingBottom: isTopDriver(index) ? '0.5em' : '0.25em',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75em', marginBottom: '0.25em' }}>
              <strong style={{ fontSize: isTopDriver(index) ? '1.15em' : '1em', color: '#111827' }}>
                {driver.name}
              </strong>
              <span
                style={{
                  fontSize: isHighImpact(driver.impact) ? '1.1em' : '1em',
                  fontWeight: isHighImpact(driver.impact) ? 'bold' : '600',
                  color: isHighImpact(driver.impact) ? '#dc2626' : '#f59e0b',
                }}
              >
                {driver.impact}% impact
              </span>
            </div>
            {driver.description && (
              <p style={{ marginLeft: '0', fontSize: '0.9em', color: '#6b7280', marginTop: '0.25em' }}>
                {driver.description}
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

