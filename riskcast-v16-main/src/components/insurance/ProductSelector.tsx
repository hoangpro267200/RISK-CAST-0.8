/**
 * RISKCAST Insurance Product Selector
 * ====================================
 * Component for selecting insurance products.
 */

import React, { useState } from 'react';
import { InsuranceProduct } from '../../types/insurance';

interface ProductSelectorProps {
  products: InsuranceProduct[];
  selectedProductId?: string;
  onSelectProduct: (product: InsuranceProduct) => void;
  riskAssessment?: any;
}

export const ProductSelector: React.FC<ProductSelectorProps> = ({
  products,
  selectedProductId,
  onSelectProduct,
  riskAssessment
}) => {
  const [selectedId, setSelectedId] = useState<string | undefined>(selectedProductId);

  const handleSelect = (product: InsuranceProduct) => {
    setSelectedId(product.product_id);
    onSelectProduct(product);
  };

  const getProductIcon = (category: string) => {
    switch (category) {
      case 'classical':
        return '🛡️';
      case 'parametric':
        return '⚡';
      case 'specialty':
        return '⭐';
      default:
        return '📦';
    }
  };

  const getProductStatusBadge = (status: string) => {
    const badges: Record<string, { text: string; color: string }> = {
      concept: { text: 'Concept', color: '#6b7280' },
      api_parametric: { text: 'Available', color: '#10b981' },
      transactional: { text: 'Live', color: '#3b82f6' },
      financialized: { text: 'Advanced', color: '#8b5cf6' }
    };
    
    const badge = badges[status] || badges.concept;
    return (
      <span
        style={{
          padding: '0.25rem 0.5rem',
          borderRadius: '4px',
          fontSize: '0.75rem',
          fontWeight: 600,
          backgroundColor: `${badge.color}20`,
          color: badge.color
        }}
      >
        {badge.text}
      </span>
    );
  };

  return (
    <div className="product-selector">
      <h2>Select Insurance Product</h2>
      
      <div className="products-grid">
        {products.map((product) => {
          const isSelected = selectedId === product.product_id;
          
          return (
            <div
              key={product.product_id}
              className={`product-card ${isSelected ? 'selected' : ''}`}
              onClick={() => handleSelect(product)}
            >
              <div className="product-header">
                <span className="product-icon">{getProductIcon(product.category)}</span>
                <div className="product-title">
                  <h3>{product.name}</h3>
                  {getProductStatusBadge(product.status)}
                </div>
              </div>
              
              <p className="product-description">{product.description}</p>
              
              <div className="product-details">
                <div className="detail-item">
                  <span>Type:</span>
                  <strong>{product.category}</strong>
                </div>
                {product.carrier && (
                  <div className="detail-item">
                    <span>Carrier:</span>
                    <strong>{product.carrier}</strong>
                  </div>
                )}
                {product.base_rate && (
                  <div className="detail-item">
                    <span>Base Rate:</span>
                    <strong>{(product.base_rate * 100).toFixed(2)}%</strong>
                  </div>
                )}
              </div>
              
              <button
                className={`select-product-btn ${isSelected ? 'selected' : ''}`}
                onClick={(e) => {
                  e.stopPropagation();
                  handleSelect(product);
                }}
              >
                {isSelected ? '✓ Selected' : 'Select Product'}
              </button>
            </div>
          );
        })}
      </div>
      
      <style jsx>{`
        .product-selector {
          padding: 2rem;
        }
        
        .product-selector h2 {
          margin-bottom: 1.5rem;
          font-size: 1.5rem;
          font-weight: 600;
        }
        
        .products-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 1.5rem;
        }
        
        .product-card {
          border: 2px solid #e5e7eb;
          border-radius: 12px;
          padding: 1.5rem;
          cursor: pointer;
          transition: all 0.2s;
          background: white;
        }
        
        .product-card:hover {
          border-color: #3b82f6;
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
        }
        
        .product-card.selected {
          border-color: #3b82f6;
          background: #eff6ff;
        }
        
        .product-header {
          display: flex;
          align-items: flex-start;
          gap: 1rem;
          margin-bottom: 1rem;
        }
        
        .product-icon {
          font-size: 2rem;
        }
        
        .product-title {
          flex: 1;
        }
        
        .product-title h3 {
          margin: 0 0 0.5rem 0;
          font-size: 1.25rem;
          font-weight: 600;
        }
        
        .product-description {
          color: #6b7280;
          font-size: 0.875rem;
          margin: 1rem 0;
          line-height: 1.5;
        }
        
        .product-details {
          margin: 1rem 0;
          padding: 1rem;
          background: #f9fafb;
          border-radius: 8px;
        }
        
        .detail-item {
          display: flex;
          justify-content: space-between;
          margin: 0.5rem 0;
          font-size: 0.875rem;
        }
        
        .select-product-btn {
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
        
        .select-product-btn:hover {
          background: #3b82f6;
          color: white;
        }
        
        .select-product-btn.selected {
          background: #3b82f6;
          color: white;
        }
      `}</style>
    </div>
  );
};

export default ProductSelector;
