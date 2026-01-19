import type { ScenarioViewModel } from '@/types/resultsViewModel';

export interface MitigationScenariosProps {
  scenarios: ScenarioViewModel[];
}

export default function MitigationScenarios(props: MitigationScenariosProps) {
  if (props.scenarios.length === 0) {
    return null;
  }

  // Visual emphasis helpers (presentational only)
  const isHighRiskReduction = (reduction: number) => reduction >= 20;

  return (
    <div>
      <h2>Alternative mitigation scenarios and their impact</h2>
      <p style={{ fontStyle: 'italic', marginBottom: '1.5em', color: '#4b5563' }}>
        The scenarios below illustrate how different actions could reduce risk and affect cost.
      </p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1em' }}>
        {props.scenarios.map((scenario) => (
          <div
            key={scenario.id}
            style={{
              border: scenario.isRecommended ? '3px solid #10b981' : '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '1.5em',
              backgroundColor: scenario.isRecommended ? '#f0fdf4' : '#f9fafb',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75em' }}>
              <strong
                style={{
                  fontSize: scenario.isRecommended ? '1.25em' : '1.1em',
                  fontWeight: '600',
                  color: '#111827',
                }}
              >
                {scenario.title}
              </strong>
              {scenario.isRecommended && (
                <span
                  style={{
                    fontSize: '0.85em',
                    fontWeight: 'bold',
                    color: '#10b981',
                    backgroundColor: '#dcfce7',
                    padding: '0.25em 0.75em',
                    borderRadius: '4px',
                  }}
                >
                  RECOMMENDED
                </span>
              )}
            </div>
            {scenario.isRecommended && (
              <p style={{ fontStyle: 'italic', color: '#166534', marginBottom: '0.75em', fontSize: '0.95em' }}>
                This scenario offers the highest risk reduction relative to cost.
              </p>
            )}
            <p style={{ fontSize: '0.95em', color: '#4b5563', marginBottom: '1em', lineHeight: '1.5' }}>
              {scenario.description}
            </p>
            <div style={{ display: 'flex', gap: '1.5em', fontSize: '0.9em' }}>
              <div>
                <span style={{ color: '#6b7280' }}>Risk Reduction: </span>
                <span
                  style={{
                    fontWeight: isHighRiskReduction(scenario.riskReduction) ? 'bold' : '600',
                    color: isHighRiskReduction(scenario.riskReduction) ? '#10b981' : '#374151',
                    fontSize: isHighRiskReduction(scenario.riskReduction) ? '1.05em' : '1em',
                  }}
                >
                  {scenario.riskReduction} points
                </span>
              </div>
              <div>
                <span style={{ color: '#6b7280' }}>Cost Impact: </span>
                <strong style={{ color: '#374151' }}>${scenario.costImpact.toLocaleString()}</strong>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

