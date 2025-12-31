import type { LossViewModel } from '@/types/resultsViewModel';

export interface LossEstimationProps {
  loss: LossViewModel | null;
  cargoValue: number;
}

export default function LossEstimation(props: LossEstimationProps) {
  if (props.loss === null) {
    return (
      <div>
        <h2>Estimated financial exposure if risks materialize</h2>
        <p style={{ fontStyle: 'italic', color: '#6b7280' }}>Loss estimation not available.</p>
      </div>
    );
  }

  // Check if cargo value is missing or all loss values are 0
  const hasNoCargoValue = props.cargoValue === 0 || props.cargoValue === undefined;
  const hasNoLossData = props.loss.expectedLoss === 0 && props.loss.p95 === 0 && props.loss.p99 === 0;

  if (hasNoCargoValue || hasNoLossData) {
    return (
      <div>
        <h2>Estimated financial exposure if risks materialize</h2>
        <div
          style={{
            border: '1px solid #6b7280',
            borderRadius: '8px',
            padding: '1.5em',
            backgroundColor: '#1f2937',
            marginBottom: '1.5em',
          }}
        >
          <p style={{ color: '#9ca3af', marginBottom: '0.5em' }}>
            ⚠️ <strong>Loss estimation unavailable</strong>
          </p>
          <p style={{ fontSize: '0.9em', color: '#6b7280' }}>
            {hasNoCargoValue 
              ? 'No cargo value was provided. Please enter a cargo value in the Input form to see financial risk estimates.'
              : 'The risk engine did not calculate any financial losses for this shipment. This may indicate very low risk exposure.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2>Estimated financial exposure if risks materialize</h2>
      <p style={{ fontStyle: 'italic', marginBottom: '1.5em', color: '#4b5563' }}>
        Without mitigation, the expected financial exposure for this shipment is shown below.
      </p>
      <div
        style={{
          border: '2px solid #dc2626',
          borderRadius: '8px',
          padding: '1.5em',
          backgroundColor: '#fef2f2',
          marginBottom: '1.5em',
        }}
      >
        <div style={{ fontSize: '0.9em', color: '#6b7280', marginBottom: '0.5em' }}>Most likely loss</div>
        <div
          style={{
            fontSize: '2.5em',
            fontWeight: 'bold',
            color: '#dc2626',
            marginBottom: '0.25em',
          }}
        >
          ${props.loss.expectedLoss.toLocaleString()}
        </div>
        <div style={{ fontSize: '0.85em', color: '#6b7280', fontStyle: 'italic' }}>Expected Loss</div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1em' }}>
        <div
          style={{
            border: '1px solid #f59e0b',
            borderRadius: '6px',
            padding: '1em',
            backgroundColor: '#fffbeb',
          }}
        >
          <div style={{ fontSize: '0.85em', color: '#6b7280', marginBottom: '0.5em' }}>
            Severe but plausible loss
          </div>
          <div style={{ fontSize: '1.5em', fontWeight: 'bold', color: '#f59e0b', marginBottom: '0.25em' }}>
            ${props.loss.p95.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.8em', color: '#6b7280' }}>VaR (95%)</div>
        </div>
        <div
          style={{
            border: '1px solid #dc2626',
            borderRadius: '6px',
            padding: '1em',
            backgroundColor: '#fef2f2',
          }}
        >
          <div style={{ fontSize: '0.85em', color: '#6b7280', marginBottom: '0.5em' }}>
            Worst-case tail risk
          </div>
          <div style={{ fontSize: '1.5em', fontWeight: 'bold', color: '#dc2626', marginBottom: '0.25em' }}>
            ${props.loss.p99.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.8em', color: '#6b7280' }}>CVaR (99%)</div>
        </div>
      </div>
      {props.loss.tailContribution > 0 && (
        <div style={{ marginTop: '1em', fontSize: '0.9em', color: '#6b7280' }}>
          <strong>Tail Contribution:</strong> {props.loss.tailContribution}% of total risk exposure
        </div>
      )}
    </div>
  );
}

