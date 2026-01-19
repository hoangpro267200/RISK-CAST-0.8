import { adaptResultV2 } from '../riskcast-v16-main/src/adapters/adaptResultV2.ts';

const input = {
  overall_risk: 65.5,
  risk_level: 'Medium',
  confidence: 0.7,
  shipment: {
    id: 'SH-TEST',
    route: 'TEST → TEST',
  },
};

console.log('Testing adaptResultV2 function...');

try {
  console.log('Calling adaptResultV2...');
  const res = adaptResultV2(input);
  console.log('Function returned successfully');
  console.log('Result type:', typeof res);
  console.log('Result is null/undefined:', res == null);
  console.log('meta.warnings:', res?.meta?.warnings ?? null);
  console.log('top-level keys present:', res && typeof res === 'object' ? Object.keys(res).filter(k=>['shipment','riskScore','profile','layers','drivers','timeline','scenarios','loss','decisions','meta'].includes(k)) : 'N/A');
  console.log('overview present:', !!(res?.overview));
  console.log('overview.shipment:', res?.overview?.shipment?.id);
  if (res && typeof res === 'object') {
    console.log('All result keys:', Object.keys(res));
  }
} catch (error) {
  console.error('Error caught:', error);
  console.error('Stack:', error.stack);
}


