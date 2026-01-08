export interface ShipmentData {
  shipmentId: string;
  trade: {
    pol: string;
    polName: string;
    polCity: string;
    polCountry: string;
    pod: string;
    podName: string;
    podCity: string;
    podCountry: string;
    mode: 'AIR' | 'SEA' | 'ROAD' | 'RAIL' | 'MULTIMODAL';
    service_route: string;
    carrier: string;
    container_type: string;
    etd: string;
    eta: string;
    transit_time_days: number;
    incoterm: string;
    incoterm_location: string;
    priority: string;
  };
  cargo: {
    cargo_type: string;
    cargo_category: string;
    hs_code: string;
    hs_chapter: string;
    packing_type: string;
    packages: number;
    gross_weight_kg: number;
    net_weight_kg: number;
    volume_cbm: number;
    stackability: boolean;
    temp_control_required: boolean;
    is_dg: boolean;
  };
  seller: {
    name: string;
    company: string;
    email: string;
    phone: string;
    country: string;
    city: string;
    address: string;
    tax_id: string;
  };
  buyer: {
    name: string;
    company: string;
    email: string;
    phone: string;
    country: string;
    city: string;
    address: string;
    tax_id: string;
  };
  value: number;
}

export interface ModulesState {
  esg: boolean;
  weather: boolean;
  portCongestion: boolean;
  carrierPerformance: boolean;
  marketScanner: boolean;
  insurance: boolean;
}

export interface EditorState {
  field: string;
  value: unknown;
  type: string;
  position: { x: number; y: number };
}

export type SaveState = 'saved' | 'saving' | 'unsaved' | 'error';

