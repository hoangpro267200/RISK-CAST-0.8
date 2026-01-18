/**
 * RISKCAST Insurance Quote Comparison Component
 * =============================================
 * Displays and compares multiple insurance quotes.
 */

import React, { useState } from 'react';
import { InsuranceQuote } from '../../types/insurance';

interface QuoteComparisonProps {
  quotes: InsuranceQuote[];
  onSelectQuote?: (quote: InsuranceQuote) => void;
  recommendedQuoteId?: string;
}

export const QuoteComparison: React.FC<QuoteComparisonProps> = ({
  quotes,
  onSelectQuote,
  recommendedQuoteId
}) => {
  const [selectedQuoteId, setSelectedQuoteId] = useState<string | null>(
    recommendedQuoteId || null
  );

  const handleSelectQuote = (quote: InsuranceQuote) => {
    setSelectedQuoteId(quote.quote_id);
    onSelectQuote?.(quote);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const getProductType = (productId: string) => {
    if (productId.includes('parametric')) {
      return 'Parametric';
    }
    return 'Classical';
  };

  const getProductIcon = (productId: string) => {
    if (productId.includes('parametric')) {
      return '⚡';
    }
    return '🛡️';
  };

  if (quotes.length === 0) {
    return (
      <div className="insurance-quote-comparison empty">
        <p>No quotes available. Please generate quotes first.</p>
      </div>
    );
  }

  return (
    <div className="insurance-quote-comparison">
      <h2>Compare Insurance Options</h2>
      
      <div className="quotes-grid">
        {quotes.map((quote) => {
          const isSelected = selectedQuoteId === quote.quote_id;
          const isRecommended = quote.quote_id === recommendedQuoteId;
          
          return (
            <div
              key={quote.quote_id}
              className={`quote-card ${isSelected ? 'selected' : ''} ${isRecommended ? 'recommended' : ''}`}
              onClick={() => handleSelectQuote(quote)}
            >
              {isRecommended && (
                <div className="recommended-badge">🤖 Recommended</div>
              )}
              
              <div className="quote-header">
                <span className="product-icon">
                  {getProductIcon(quote.product_id)}
                </span>
                <h3>{getProductType(quote.product_id)}</h3>
              </div>
              
              <div className="quote-premium">
                <div className="premium-amount">
                  {formatCurrency(quote.premium.total_premium)}
                </div>
                <div className="premium-label">Premium</div>
              </div>
              
              {quote.coverage && (
                <div className="quote-coverage">
                  <div className="coverage-item">
                    <span>Coverage:</span>
                    <strong>{formatCurrency(quote.coverage.sum_insured)}</strong>
                  </div>
                  <div className="coverage-item">
                    <span>Deductible:</span>
                    <strong>{formatCurrency(quote.coverage.deductible)}</strong>
                  </div>
                </div>
              )}
              
              {quote.expected_payout && (
                <div className="quote-parametric">
                  <div className="parametric-item">
                    <span>Expected Payout:</span>
                    <strong>{formatCurrency(quote.expected_payout)}</strong>
                  </div>
                  {quote.trigger_probability && (
                    <div className="parametric-item">
                      <span>Trigger Probability:</span>
                      <strong>{(quote.trigger_probability * 100).toFixed(1)}%</strong>
                    </div>
                  )}
                </div>
              )}
              
              {quote.pricing_breakdown && (
                <div className="quote-breakdown">
                  <details>
                    <summary>Pricing Breakdown</summary>
                    <div className="breakdown-details">
                      <div>Expected Loss: {formatCurrency(quote.pricing_breakdown.expected_loss)}</div>
                      <div>Load Factor: {quote.pricing_breakdown.load_factor}x</div>
                      <div>Admin Costs: {formatCurrency(quote.pricing_breakdown.administrative_costs)}</div>
                    </div>
                  </details>
                </div>
              )}
              
              <button
                className={`select-quote-btn ${isSelected ? 'selected' : ''}`}
                onClick={(e) => {
                  e.stopPropagation();
                  handleSelectQuote(quote);
                }}
              >
                {isSelected ? '✓ Selected' : 'Select Quote'}
              </button>
            </div>
          );
        })}
      </div>
      
      <style jsx>{`
        .insurance-quote-comparison {
          padding: 2rem;
        }
        
        .insurance-quote-comparison h2 {
          margin-bottom: 1.5rem;
          font-size: 1.5rem;
          font-weight: 600;
        }
        
        .quotes-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 1.5rem;
        }
        
        .quote-card {
          border: 2px solid #e5e7eb;
          border-radius: 12px;
          padding: 1.5rem;
          cursor: pointer;
          transition: all 0.2s;
          background: white;
          position: relative;
        }
        
        .quote-card:hover {
          border-color: #3b82f6;
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
        }
        
        .quote-card.selected {
          border-color: #3b82f6;
          background: #eff6ff;
        }
        
        .quote-card.recommended {
          border-color: #10b981;
        }
        
        .recommended-badge {
          position: absolute;
          top: -10px;
          right: 1rem;
          background: #10b981;
          color: white;
          padding: 0.25rem 0.75rem;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 600;
        }
        
        .quote-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 1rem;
        }
        
        .product-icon {
          font-size: 1.5rem;
        }
        
        .quote-header h3 {
          margin: 0;
          font-size: 1.25rem;
          font-weight: 600;
        }
        
        .quote-premium {
          margin: 1.5rem 0;
          text-align: center;
        }
        
        .premium-amount {
          font-size: 2rem;
          font-weight: 700;
          color: #1f2937;
        }
        
        .premium-label {
          font-size: 0.875rem;
          color: #6b7280;
          margin-top: 0.25rem;
        }
        
        .quote-coverage,
        .quote-parametric {
          margin: 1rem 0;
          padding: 1rem;
          background: #f9fafb;
          border-radius: 8px;
        }
        
        .coverage-item,
        .parametric-item {
          display: flex;
          justify-content: space-between;
          margin: 0.5rem 0;
          font-size: 0.875rem;
        }
        
        .quote-breakdown {
          margin-top: 1rem;
        }
        
        .breakdown-details {
          padding: 0.75rem;
          background: #f3f4f6;
          border-radius: 6px;
          font-size: 0.875rem;
          margin-top: 0.5rem;
        }
        
        .select-quote-btn {
          width: 100%;
          margin-top: 1rem;
          padding: 0.75rem;
          border: 2px solid #3b82f6;
          border-radius: 8px;
          background: white;
          color: #3b82f6;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .select-quote-btn:hover {
          background: #3b82f6;
          color: white;
        }
        
        .select-quote-btn.selected {
          background: #3b82f6;
          color: white;
        }
        
        .empty {
          text-align: center;
          padding: 3rem;
          color: #6b7280;
        }
      `}</style>
    </div>
  );
};

export default QuoteComparison;
