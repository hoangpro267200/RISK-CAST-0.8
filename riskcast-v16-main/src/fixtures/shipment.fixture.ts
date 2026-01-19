import type { ShipmentData } from '../types';

let shipmentSeq = 1;

export function createMockShipment(overrides: Partial<ShipmentData> = {}): ShipmentData {
  const id = overrides.shipmentId ?? `SHP-${String(shipmentSeq++).padStart(4, '0')}`;

  return {
    shipmentId: id,
    route: overrides.route ?? { pol: 'SGSIN', pod: 'USLAX' },
    carrier: overrides.carrier ?? 'MAERSK',
    etd: overrides.etd ?? '2025-01-01',
    eta: overrides.eta ?? '2025-01-20',
    incoterm: overrides.incoterm,
    cargoValue: overrides.cargoValue,
    dataConfidence: overrides.dataConfidence ?? 0.65,
    lastUpdated: overrides.lastUpdated ?? '2025-01-01T00:00:00Z',
    trace: overrides.trace,
  };
}

