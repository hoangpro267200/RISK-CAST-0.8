import type { OverviewViewModel } from '@/types/resultsViewModel';

export interface RiskOverviewProps extends OverviewViewModel {}

export default function RiskOverview(props: RiskOverviewProps) {
  // Visual emphasis based on risk level (presentational only)
  const isHighRisk = props.riskScore.level === 'High' || props.riskScore.level === 'Critical';
  const isLowConfidence = props.riskScore.confidence < 60;

  // Generate professional narrative text based on risk level
  const riskNarrative =
    props.riskScore.level === 'Critical' || props.riskScore.level === 'High'
      ? 'This shipment carries a High level of risk, indicating a significant likelihood of disruption or financial loss.'
      : props.riskScore.level === 'Medium'
        ? 'This shipment presents a moderate risk profile, requiring active monitoring.'
        : 'This shipment has a low risk profile with limited exposure to major disruptions.';

  return (
    <div>
      <h2>Risk Overview</h2>

      {/* Primary risk score - most prominent visual element */}
      <div style={{ marginBottom: '2em' }}>
        <div
          style={{
            fontSize: isHighRisk ? '3em' : '2.5em',
            fontWeight: 'bold',
            color: isHighRisk ? '#dc2626' : props.riskScore.level === 'Medium' ? '#f59e0b' : '#10b981',
            marginBottom: '0.25em',
          }}
        >
          {props.riskScore.score} / 100
        </div>
        <div
          style={{
            fontSize: '1.5em',
            fontWeight: 'bold',
            color: isHighRisk ? '#dc2626' : props.riskScore.level === 'Medium' ? '#f59e0b' : '#10b981',
            marginBottom: '0.5em',
          }}
        >
          {props.riskScore.level}
        </div>
        <p style={{ fontStyle: 'italic', fontSize: '1.1em', marginBottom: '1em', color: '#4b5563' }}>
          {riskNarrative}
        </p>
        <p style={{ fontSize: '0.95em', color: '#6b7280' }}>
          Assessment confidence: <strong style={{ color: isLowConfidence ? '#f59e0b' : '#4b5563' }}>{props.riskScore.confidence}%</strong>
          {isLowConfidence && (
            <span style={{ color: '#f59e0b', fontWeight: 'bold' }}> — Lower confidence assessment</span>
          )}
          , based on available shipment, network, and climate data.
        </p>
      </div>

      {/* Engine reasoning explanation (STEP 7B.2) - driver-based narrative */}
      {props.reasoning.explanation && (
        <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '1.5em', marginTop: '1.5em' }}>
          <h3 style={{ fontSize: '1.1em', fontWeight: '600', marginBottom: '0.75em', color: '#374151' }}>
            Risk Assessment Explanation
          </h3>
          <p style={{ fontSize: '0.95em', lineHeight: '1.6', color: '#4b5563', fontStyle: 'italic' }}>
            {props.reasoning.explanation}
          </p>
        </div>
      )}

      {/* Shipment information - secondary details */}
      <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '1.5em' }}>
        <h3 style={{ fontSize: '1.1em', fontWeight: '600', marginBottom: '0.75em', color: '#374151' }}>
          Shipment Information
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5em', fontSize: '0.95em' }}>
          <p>
            <strong>Route:</strong> {props.shipment.route || 'N/A'}
          </p>
          <p>
            <strong>Carrier:</strong> {props.shipment.carrier || 'N/A'}
          </p>
          {props.shipment.etd && (
            <p>
              <strong>ETD:</strong> {props.shipment.etd}
            </p>
          )}
          {props.shipment.eta && (
            <p>
              <strong>ETA:</strong> {props.shipment.eta}
            </p>
          )}
          {props.shipment.cargoValue > 0 && (
            <p>
              <strong>Cargo Value:</strong> ${props.shipment.cargoValue.toLocaleString()}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

