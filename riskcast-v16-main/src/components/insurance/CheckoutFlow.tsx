/**
 * RISKCAST Insurance Checkout Flow
 * =================================
 * Multi-step checkout process for insurance purchase.
 */

import React, { useState } from 'react';
import { InsuranceQuote, TransactionState } from '../../types/insurance';

interface CheckoutFlowProps {
  quote: InsuranceQuote;
  onComplete: (transactionId: string) => void;
  onCancel: () => void;
}

type CheckoutStep = 'config' | 'kyc' | 'payment' | 'review' | 'processing' | 'complete';

export const CheckoutFlow: React.FC<CheckoutFlowProps> = ({
  quote,
  onComplete,
  onCancel
}) => {
  const [currentStep, setCurrentStep] = useState<CheckoutStep>('config');
  const [coverageConfig, setCoverageConfig] = useState({
    sum_insured: quote.coverage?.sum_insured || 0,
    deductible: quote.coverage?.deductible || 0,
    trigger_threshold: quote.trigger?.threshold,
    payout_per_day: quote.payout_structure?.payout_per_unit
  });
  const [kycData, setKycData] = useState<any>(null);
  const [paymentData, setPaymentData] = useState<any>(null);
  const [transactionId, setTransactionId] = useState<string | null>(null);

  const handleNext = () => {
    const steps: CheckoutStep[] = ['config', 'kyc', 'payment', 'review', 'processing', 'complete'];
    const currentIndex = steps.indexOf(currentStep);
    if (currentIndex < steps.length - 1) {
      setCurrentStep(steps[currentIndex + 1]);
    }
  };

  const handleBack = () => {
    const steps: CheckoutStep[] = ['config', 'kyc', 'payment', 'review', 'processing', 'complete'];
    const currentIndex = steps.indexOf(currentStep);
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1]);
    }
  };

  const handleSubmit = async () => {
    setCurrentStep('processing');
    
    try {
      // Create transaction
      const response = await fetch('/api/v2/insurance/transactions/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quote_id: quote.quote_id,
          coverage_config: coverageConfig,
          insured_party: kycData
        })
      });
      
      const result = await response.json();
      const txId = result.data.transaction_id;
      setTransactionId(txId);
      
      // Process payment
      if (paymentData) {
        await fetch(`/api/v2/insurance/transactions/${txId}/payment`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(paymentData)
        });
      }
      
      setCurrentStep('complete');
      onComplete(txId);
      
    } catch (error) {
      console.error('Checkout error:', error);
      // Handle error
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <div className="checkout-flow">
      <div className="checkout-header">
        <h2>Complete Your Insurance Purchase</h2>
        <div className="progress-bar">
          {['config', 'kyc', 'payment', 'review'].map((step, index) => (
            <div
              key={step}
              className={`progress-step ${
                ['config', 'kyc', 'payment', 'review'].indexOf(currentStep) >= index
                  ? 'completed'
                  : ''
              }`}
            >
              {index + 1}
            </div>
          ))}
        </div>
      </div>

      {currentStep === 'config' && (
        <div className="checkout-step">
          <h3>Configure Coverage</h3>
          <div className="config-form">
            <label>
              Sum Insured:
              <input
                type="number"
                value={coverageConfig.sum_insured}
                onChange={(e) =>
                  setCoverageConfig({
                    ...coverageConfig,
                    sum_insured: parseFloat(e.target.value)
                  })
                }
              />
            </label>
            <label>
              Deductible:
              <input
                type="number"
                value={coverageConfig.deductible}
                onChange={(e) =>
                  setCoverageConfig({
                    ...coverageConfig,
                    deductible: parseFloat(e.target.value)
                  })
                }
              />
            </label>
            {quote.trigger && (
              <label>
                Trigger Threshold:
                <input
                  type="number"
                  value={coverageConfig.trigger_threshold || quote.trigger.threshold}
                  onChange={(e) =>
                    setCoverageConfig({
                      ...coverageConfig,
                      trigger_threshold: parseFloat(e.target.value)
                    })
                  }
                />
              </label>
            )}
          </div>
          <div className="step-actions">
            <button onClick={onCancel}>Cancel</button>
            <button onClick={handleNext}>Continue</button>
          </div>
        </div>
      )}

      {currentStep === 'kyc' && (
        <div className="checkout-step">
          <h3>Identity Verification</h3>
          <div className="kyc-form">
            <label>
              Legal Name:
              <input
                type="text"
                onChange={(e) =>
                  setKycData({ ...kycData, legal_name: e.target.value })
                }
              />
            </label>
            <label>
              Registration Number:
              <input
                type="text"
                onChange={(e) =>
                  setKycData({ ...kycData, registration_number: e.target.value })
                }
              />
            </label>
            <label>
              Country:
              <select
                onChange={(e) =>
                  setKycData({ ...kycData, country: e.target.value })
                }
              >
                <option value="">Select Country</option>
                <option value="US">United States</option>
                <option value="SG">Singapore</option>
                <option value="CN">China</option>
              </select>
            </label>
          </div>
          <div className="step-actions">
            <button onClick={handleBack}>Back</button>
            <button onClick={handleNext}>Continue</button>
          </div>
        </div>
      )}

      {currentStep === 'payment' && (
        <div className="checkout-step">
          <h3>Payment</h3>
          <div className="payment-form">
            <div className="order-summary">
              <h4>Order Summary</h4>
              <div>Premium: {formatCurrency(quote.premium.total_premium)}</div>
              <div>Total: {formatCurrency(quote.premium.total_premium)}</div>
            </div>
            <label>
              Payment Method:
              <select
                onChange={(e) =>
                  setPaymentData({ ...paymentData, payment_method: e.target.value })
                }
              >
                <option value="credit_card">Credit/Debit Card</option>
                <option value="wire_transfer">Wire Transfer</option>
              </select>
            </label>
          </div>
          <div className="step-actions">
            <button onClick={handleBack}>Back</button>
            <button onClick={handleNext}>Continue</button>
          </div>
        </div>
      )}

      {currentStep === 'review' && (
        <div className="checkout-step">
          <h3>Review & Confirm</h3>
          <div className="review-summary">
            <div>Quote: {quote.quote_id}</div>
            <div>Premium: {formatCurrency(quote.premium.total_premium)}</div>
            <div>Coverage: {formatCurrency(coverageConfig.sum_insured)}</div>
          </div>
          <div className="step-actions">
            <button onClick={handleBack}>Back</button>
            <button onClick={handleSubmit}>Complete Purchase</button>
          </div>
        </div>
      )}

      {currentStep === 'processing' && (
        <div className="checkout-step">
          <div className="processing">
            <div className="spinner"></div>
            <p>Processing your insurance...</p>
          </div>
        </div>
      )}

      {currentStep === 'complete' && (
        <div className="checkout-step">
          <div className="success">
            <h3>✅ Insurance Purchase Complete!</h3>
            <p>Transaction ID: {transactionId}</p>
            <p>Your policy is being processed and will be active shortly.</p>
          </div>
        </div>
      )}

      <style jsx>{`
        .checkout-flow {
          max-width: 800px;
          margin: 0 auto;
          padding: 2rem;
        }
        
        .checkout-header h2 {
          margin-bottom: 1rem;
        }
        
        .progress-bar {
          display: flex;
          gap: 1rem;
          margin-bottom: 2rem;
        }
        
        .progress-step {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          border: 2px solid #e5e7eb;
          display: flex;
          align-items: center;
          justify-content: center;
          background: white;
        }
        
        .progress-step.completed {
          background: #3b82f6;
          color: white;
          border-color: #3b82f6;
        }
        
        .checkout-step {
          background: white;
          border-radius: 12px;
          padding: 2rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .step-actions {
          display: flex;
          gap: 1rem;
          margin-top: 2rem;
          justify-content: flex-end;
        }
        
        .step-actions button {
          padding: 0.75rem 1.5rem;
          border-radius: 8px;
          border: none;
          font-weight: 600;
          cursor: pointer;
        }
        
        .step-actions button:first-child {
          background: #f3f4f6;
          color: #374151;
        }
        
        .step-actions button:last-child {
          background: #3b82f6;
          color: white;
        }
        
        .processing {
          text-align: center;
          padding: 3rem;
        }
        
        .spinner {
          border: 4px solid #f3f4f6;
          border-top: 4px solid #3b82f6;
          border-radius: 50%;
          width: 50px;
          height: 50px;
          animation: spin 1s linear infinite;
          margin: 0 auto 1rem;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        .success {
          text-align: center;
          padding: 3rem;
        }
        
        .success h3 {
          color: #10b981;
          margin-bottom: 1rem;
        }
      `}</style>
    </div>
  );
};

export default CheckoutFlow;
