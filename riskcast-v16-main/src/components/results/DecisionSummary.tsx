import type {
  InsuranceDecisionViewModel,
  TimingDecisionViewModel,
  RoutingDecisionViewModel,
} from '@/types/resultsViewModel';

export interface DecisionSummaryProps {
  insurance: InsuranceDecisionViewModel;
  timing: TimingDecisionViewModel;
  routing: RoutingDecisionViewModel;
}

export default function DecisionSummary(props: DecisionSummaryProps) {
  // Visual emphasis helpers (presentational only)
  const isRecommended = (status: string) => status === 'RECOMMENDED';
  const isActionRecommended = (recommendation: string) =>
    recommendation === 'BUY' || recommendation === 'CHANGE_ROUTE' || recommendation === 'ADJUST_ETD';

  // Check if all decisions are NOT_NEEDED (low risk scenario)
  const allNotNeeded = 
    props.insurance.status === 'NOT_NEEDED' && 
    props.timing.status === 'NOT_NEEDED' && 
    props.routing.status === 'NOT_NEEDED';

  return (
    <div>
      <h2>Recommended actions based on the current risk profile</h2>
      <p style={{ fontStyle: 'italic', marginBottom: '1.5em', color: '#4b5563' }}>
        Based on the assessed risk level and confidence, the following actions are recommended.
      </p>

      {allNotNeeded && (
        <div
          style={{
            border: '2px solid #10b981',
            borderRadius: '8px',
            padding: '1em 1.5em',
            backgroundColor: '#064e3b',
            marginBottom: '1.5em',
          }}
        >
          <p style={{ color: '#34d399', fontWeight: '600', marginBottom: '0.25em' }}>
            ✅ Low Risk - No Immediate Action Required
          </p>
          <p style={{ fontSize: '0.9em', color: '#a7f3d0' }}>
            This shipment has a low risk profile. Standard monitoring and procedures are sufficient.
          </p>
        </div>
      )}

      <div
        style={{
          border: isRecommended(props.insurance.status) ? '3px solid #dc2626' : '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '1.5em',
          marginBottom: '1.5em',
          backgroundColor: isRecommended(props.insurance.status) ? '#fef2f2' : '#f9fafb',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1em' }}>
          <h3 style={{ fontSize: '1.25em', fontWeight: '600', color: '#111827' }}>Insurance</h3>
          {isRecommended(props.insurance.status) && (
            <span
              style={{
                fontSize: '0.85em',
                fontWeight: 'bold',
                color: '#dc2626',
                backgroundColor: '#fee2e2',
                padding: '0.25em 0.75em',
                borderRadius: '4px',
              }}
            >
              RECOMMENDED
            </span>
          )}
        </div>
        {isRecommended(props.insurance.status) && (
          <p style={{ fontStyle: 'italic', color: '#991b1b', marginBottom: '1em', fontSize: '0.95em' }}>
            This action is recommended due to the elevated risk level and potential financial exposure.
          </p>
        )}
        <div style={{ marginBottom: '0.75em' }}>
          <span style={{ fontSize: '0.9em', color: '#6b7280' }}>Status: </span>
          <span
            style={{
              fontSize: '1em',
              fontWeight: isRecommended(props.insurance.status) ? 'bold' : '600',
              color: isRecommended(props.insurance.status) ? '#dc2626' : '#374151',
            }}
          >
            {props.insurance.status}
          </span>
        </div>
        <div style={{ marginBottom: '0.75em' }}>
          <span style={{ fontSize: '0.9em', color: '#6b7280' }}>Recommendation: </span>
          <span
            style={{
              fontSize: isActionRecommended(props.insurance.recommendation) ? '1.15em' : '1em',
              fontWeight: isActionRecommended(props.insurance.recommendation) ? 'bold' : '600',
              color: isActionRecommended(props.insurance.recommendation) ? '#dc2626' : '#374151',
            }}
          >
            {props.insurance.recommendation}
          </span>
        </div>
        <p style={{ fontSize: '0.95em', color: '#4b5563', marginBottom: '0.75em', lineHeight: '1.5' }}>
          {props.insurance.rationale}
        </p>
        <div style={{ display: 'flex', gap: '1.5em', fontSize: '0.9em', color: '#6b7280' }}>
          {props.insurance.riskDeltaPoints !== null && (
            <span>
              Risk Delta: <strong style={{ color: '#374151' }}>{props.insurance.riskDeltaPoints} points</strong>
            </span>
          )}
          {props.insurance.costImpactUsd !== null && (
            <span>
              Cost Impact: <strong style={{ color: '#374151' }}>${props.insurance.costImpactUsd.toLocaleString()}</strong>
            </span>
          )}
        </div>
      </div>

      <div
        style={{
          border: isRecommended(props.timing.status) ? '3px solid #dc2626' : '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '1.5em',
          marginBottom: '1.5em',
          backgroundColor: isRecommended(props.timing.status) ? '#fef2f2' : '#f9fafb',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1em' }}>
          <h3 style={{ fontSize: '1.25em', fontWeight: '600', color: '#111827' }}>Timing</h3>
          {isRecommended(props.timing.status) && (
            <span
              style={{
                fontSize: '0.85em',
                fontWeight: 'bold',
                color: '#dc2626',
                backgroundColor: '#fee2e2',
                padding: '0.25em 0.75em',
                borderRadius: '4px',
              }}
            >
              RECOMMENDED
            </span>
          )}
        </div>
        {isRecommended(props.timing.status) && (
          <p style={{ fontStyle: 'italic', color: '#991b1b', marginBottom: '1em', fontSize: '0.95em' }}>
            This action is recommended due to the elevated risk level and potential financial exposure.
          </p>
        )}
        <div style={{ marginBottom: '0.75em' }}>
          <span style={{ fontSize: '0.9em', color: '#6b7280' }}>Status: </span>
          <span
            style={{
              fontSize: '1em',
              fontWeight: isRecommended(props.timing.status) ? 'bold' : '600',
              color: isRecommended(props.timing.status) ? '#dc2626' : '#374151',
            }}
          >
            {props.timing.status}
          </span>
        </div>
        <div style={{ marginBottom: '0.75em' }}>
          <span style={{ fontSize: '0.9em', color: '#6b7280' }}>Recommendation: </span>
          <span
            style={{
              fontSize: isActionRecommended(props.timing.recommendation) ? '1.15em' : '1em',
              fontWeight: isActionRecommended(props.timing.recommendation) ? 'bold' : '600',
              color: isActionRecommended(props.timing.recommendation) ? '#dc2626' : '#374151',
            }}
          >
            {props.timing.recommendation}
          </span>
        </div>
        <p style={{ fontSize: '0.95em', color: '#4b5563', marginBottom: '0.75em', lineHeight: '1.5' }}>
          {props.timing.rationale}
        </p>
        {props.timing.optimalWindow && (
          <div style={{ marginBottom: '0.75em', fontSize: '0.9em', color: '#6b7280' }}>
            <span>Optimal Window: </span>
            <strong style={{ color: '#374151' }}>
              {props.timing.optimalWindow.start} to {props.timing.optimalWindow.end}
            </strong>
          </div>
        )}
        <div style={{ display: 'flex', gap: '1.5em', fontSize: '0.9em', color: '#6b7280' }}>
          {props.timing.riskReductionPoints !== null && (
            <span>
              Risk Reduction: <strong style={{ color: '#374151' }}>{props.timing.riskReductionPoints} points</strong>
            </span>
          )}
          {props.timing.costImpactUsd !== null && (
            <span>
              Cost Impact: <strong style={{ color: '#374151' }}>${props.timing.costImpactUsd.toLocaleString()}</strong>
            </span>
          )}
        </div>
      </div>

      <div
        style={{
          border: isRecommended(props.routing.status) ? '3px solid #dc2626' : '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '1.5em',
          marginBottom: '1.5em',
          backgroundColor: isRecommended(props.routing.status) ? '#fef2f2' : '#f9fafb',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1em' }}>
          <h3 style={{ fontSize: '1.25em', fontWeight: '600', color: '#111827' }}>Routing</h3>
          {isRecommended(props.routing.status) && (
            <span
              style={{
                fontSize: '0.85em',
                fontWeight: 'bold',
                color: '#dc2626',
                backgroundColor: '#fee2e2',
                padding: '0.25em 0.75em',
                borderRadius: '4px',
              }}
            >
              RECOMMENDED
            </span>
          )}
        </div>
        {isRecommended(props.routing.status) && (
          <p style={{ fontStyle: 'italic', color: '#991b1b', marginBottom: '1em', fontSize: '0.95em' }}>
            This action is recommended due to the elevated risk level and potential financial exposure.
          </p>
        )}
        <div style={{ marginBottom: '0.75em' }}>
          <span style={{ fontSize: '0.9em', color: '#6b7280' }}>Status: </span>
          <span
            style={{
              fontSize: '1em',
              fontWeight: isRecommended(props.routing.status) ? 'bold' : '600',
              color: isRecommended(props.routing.status) ? '#dc2626' : '#374151',
            }}
          >
            {props.routing.status}
          </span>
        </div>
        <div style={{ marginBottom: '0.75em' }}>
          <span style={{ fontSize: '0.9em', color: '#6b7280' }}>Recommendation: </span>
          <span
            style={{
              fontSize: isActionRecommended(props.routing.recommendation) ? '1.15em' : '1em',
              fontWeight: isActionRecommended(props.routing.recommendation) ? 'bold' : '600',
              color: isActionRecommended(props.routing.recommendation) ? '#dc2626' : '#374151',
            }}
          >
            {props.routing.recommendation}
          </span>
        </div>
        <p style={{ fontSize: '0.95em', color: '#4b5563', marginBottom: '0.75em', lineHeight: '1.5' }}>
          {props.routing.rationale}
        </p>
        {props.routing.bestAlternative && (
          <div style={{ marginBottom: '0.5em', fontSize: '0.9em', color: '#6b7280' }}>
            <span>Best Alternative: </span>
            <strong style={{ color: '#374151' }}>{props.routing.bestAlternative}</strong>
          </div>
        )}
        {props.routing.tradeoff && (
          <div style={{ marginBottom: '0.75em', fontSize: '0.9em', color: '#6b7280', fontStyle: 'italic' }}>
            Tradeoff: {props.routing.tradeoff}
          </div>
        )}
        <div style={{ display: 'flex', gap: '1.5em', fontSize: '0.9em', color: '#6b7280' }}>
          {props.routing.riskReductionPoints !== null && (
            <span>
              Risk Reduction: <strong style={{ color: '#374151' }}>{props.routing.riskReductionPoints} points</strong>
            </span>
          )}
          {props.routing.costImpactUsd !== null && (
            <span>
              Cost Impact: <strong style={{ color: '#374151' }}>${props.routing.costImpactUsd.toLocaleString()}</strong>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

