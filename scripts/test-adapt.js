// Simple test for adaptResultV2
console.log('Testing adaptResultV2...');

try {
  // Import the function
  const { adaptResultV2 } = await import('../riskcast-v16-main/src/adapters/adaptResultV2.ts');

  // Test with simple input
  const input = {
    overall_risk: 65.5,
    risk_level: 'Medium',
    confidence: 0.7,
    shipment: {
      id: 'SH-TEST',
      route: 'TEST → TEST',
    },
  };

  console.log('Input:', input);

  const result = adaptResultV2(input);

  console.log('Result type:', typeof result);
  console.log('Result is null/undefined:', result == null);
  console.log('Result has overview:', result && typeof result === 'object' && 'overview' in result);
  console.log('Result keys:', result ? Object.keys(result) : 'N/A');

  if (result && result.overview) {
    console.log('SUCCESS: Function returned valid ResultsViewModel');
    console.log('Overview riskScore:', result.overview.riskScore);
  } else {
    console.log('FAILURE: Function did not return valid ResultsViewModel');
    console.log('Result:', result);
  }

} catch (error) {
  console.error('ERROR:', error);
  console.error('Stack:', error.stack);
}





