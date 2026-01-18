/**
 * Port Lookup Utility - Centralized Port Database
 * 
 * Provides consistent port code → name/city/country mapping across all pages.
 * Replaces hardcoded port mappings scattered throughout the codebase.
 */

export interface PortInfo {
  code: string;
  name: string;
  city: string;
  country: string;
  countryCode: string;
  type: 'airport' | 'seaport';
}

/**
 * Comprehensive ports database
 * Source: Consolidated from SmartInlineEditor.tsx, overview.py, and logistics data
 */
const PORTS_DATABASE: PortInfo[] = [
  // Vietnam Airports
  { code: 'SGN', name: 'Tan Son Nhat International Airport', city: 'Ho Chi Minh City', country: 'Vietnam', countryCode: 'VN', type: 'airport' },
  { code: 'HAN', name: 'Noi Bai International Airport', city: 'Hanoi', country: 'Vietnam', countryCode: 'VN', type: 'airport' },
  { code: 'DAD', name: 'Da Nang International Airport', city: 'Da Nang', country: 'Vietnam', countryCode: 'VN', type: 'airport' },
  { code: 'CXR', name: 'Cam Ranh International Airport', city: 'Nha Trang', country: 'Vietnam', countryCode: 'VN', type: 'airport' },
  { code: 'PQC', name: 'Phu Quoc International Airport', city: 'Phu Quoc', country: 'Vietnam', countryCode: 'VN', type: 'airport' },
  
  // Vietnam Seaports
  { code: 'VNSGN', name: 'Saigon Port (Cat Lai)', city: 'Ho Chi Minh City', country: 'Vietnam', countryCode: 'VN', type: 'seaport' },
  { code: 'VNHPH', name: 'Hai Phong Port', city: 'Hai Phong', country: 'Vietnam', countryCode: 'VN', type: 'seaport' },
  { code: 'VNCMP', name: 'Cai Mep International Terminal', city: 'Vung Tau', country: 'Vietnam', countryCode: 'VN', type: 'seaport' },
  { code: 'VNDAD', name: 'Da Nang Port (Tien Sa)', city: 'Da Nang', country: 'Vietnam', countryCode: 'VN', type: 'seaport' },
  
  // China Airports
  { code: 'PVG', name: 'Shanghai Pudong International Airport', city: 'Shanghai', country: 'China', countryCode: 'CN', type: 'airport' },
  { code: 'SHA', name: 'Shanghai Hongqiao Airport', city: 'Shanghai', country: 'China', countryCode: 'CN', type: 'airport' },
  { code: 'PEK', name: 'Beijing Capital International Airport', city: 'Beijing', country: 'China', countryCode: 'CN', type: 'airport' },
  { code: 'CAN', name: 'Guangzhou Baiyun Airport', city: 'Guangzhou', country: 'China', countryCode: 'CN', type: 'airport' },
  { code: 'SZX', name: 'Shenzhen Bao\'an Airport', city: 'Shenzhen', country: 'China', countryCode: 'CN', type: 'airport' },
  
  // China Seaports
  { code: 'CNSHA', name: 'Port of Shanghai', city: 'Shanghai', country: 'China', countryCode: 'CN', type: 'seaport' },
  { code: 'CNNGB', name: 'Ningbo-Zhoushan Port', city: 'Ningbo', country: 'China', countryCode: 'CN', type: 'seaport' },
  { code: 'CNSZX', name: 'Shenzhen Port (Yantian)', city: 'Shenzhen', country: 'China', countryCode: 'CN', type: 'seaport' },
  { code: 'CNQIN', name: 'Port of Qingdao', city: 'Qingdao', country: 'China', countryCode: 'CN', type: 'seaport' },
  { code: 'CNDLC', name: 'Port of Dalian', city: 'Dalian', country: 'China', countryCode: 'CN', type: 'seaport' },
  { code: 'CNXMN', name: 'Port of Xiamen', city: 'Xiamen', country: 'China', countryCode: 'CN', type: 'seaport' },
  
  // USA Airports
  { code: 'LAX', name: 'Los Angeles International Airport', city: 'Los Angeles', country: 'USA', countryCode: 'US', type: 'airport' },
  { code: 'JFK', name: 'John F. Kennedy International Airport', city: 'New York', country: 'USA', countryCode: 'US', type: 'airport' },
  { code: 'ORD', name: "O'Hare International Airport", city: 'Chicago', country: 'USA', countryCode: 'US', type: 'airport' },
  { code: 'SFO', name: 'San Francisco International Airport', city: 'San Francisco', country: 'USA', countryCode: 'US', type: 'airport' },
  { code: 'MIA', name: 'Miami International Airport', city: 'Miami', country: 'USA', countryCode: 'US', type: 'airport' },
  { code: 'SEA', name: 'Seattle-Tacoma International Airport', city: 'Seattle', country: 'USA', countryCode: 'US', type: 'airport' },
  { code: 'DFW', name: 'Dallas/Fort Worth International Airport', city: 'Dallas', country: 'USA', countryCode: 'US', type: 'airport' },
  
  // USA Seaports
  { code: 'USLAX', name: 'Port of Los Angeles', city: 'Los Angeles', country: 'USA', countryCode: 'US', type: 'seaport' },
  { code: 'USLGB', name: 'Port of Long Beach', city: 'Long Beach', country: 'USA', countryCode: 'US', type: 'seaport' },
  { code: 'USNYC', name: 'Port of New York/New Jersey', city: 'New York', country: 'USA', countryCode: 'US', type: 'seaport' },
  { code: 'USOAK', name: 'Port of Oakland', city: 'Oakland', country: 'USA', countryCode: 'US', type: 'seaport' },
  { code: 'USSEA', name: 'Port of Seattle/Tacoma', city: 'Seattle', country: 'USA', countryCode: 'US', type: 'seaport' },
  { code: 'USSAV', name: 'Port of Savannah', city: 'Savannah', country: 'USA', countryCode: 'US', type: 'seaport' },
  { code: 'USHOU', name: 'Port of Houston', city: 'Houston', country: 'USA', countryCode: 'US', type: 'seaport' },
  
  // Hong Kong
  { code: 'HKG', name: 'Hong Kong International Airport', city: 'Hong Kong', country: 'Hong Kong', countryCode: 'HK', type: 'airport' },
  { code: 'HKHKG', name: 'Port of Hong Kong', city: 'Hong Kong', country: 'Hong Kong', countryCode: 'HK', type: 'seaport' },
  
  // Singapore
  { code: 'SIN', name: 'Singapore Changi Airport', city: 'Singapore', country: 'Singapore', countryCode: 'SG', type: 'airport' },
  { code: 'SGSIN', name: 'Port of Singapore', city: 'Singapore', country: 'Singapore', countryCode: 'SG', type: 'seaport' },
  
  // Japan
  { code: 'NRT', name: 'Narita International Airport', city: 'Tokyo', country: 'Japan', countryCode: 'JP', type: 'airport' },
  { code: 'HND', name: 'Tokyo Haneda Airport', city: 'Tokyo', country: 'Japan', countryCode: 'JP', type: 'airport' },
  { code: 'KIX', name: 'Kansai International Airport', city: 'Osaka', country: 'Japan', countryCode: 'JP', type: 'airport' },
  { code: 'JPTYO', name: 'Port of Tokyo', city: 'Tokyo', country: 'Japan', countryCode: 'JP', type: 'seaport' },
  { code: 'JPYOK', name: 'Port of Yokohama', city: 'Yokohama', country: 'Japan', countryCode: 'JP', type: 'seaport' },
  
  // South Korea
  { code: 'ICN', name: 'Incheon International Airport', city: 'Seoul', country: 'South Korea', countryCode: 'KR', type: 'airport' },
  { code: 'KRPUS', name: 'Port of Busan', city: 'Busan', country: 'South Korea', countryCode: 'KR', type: 'seaport' },
  { code: 'KRICN', name: 'Port of Incheon', city: 'Incheon', country: 'South Korea', countryCode: 'KR', type: 'seaport' },
  
  // Thailand
  { code: 'BKK', name: 'Suvarnabhumi Airport', city: 'Bangkok', country: 'Thailand', countryCode: 'TH', type: 'airport' },
  { code: 'DMK', name: 'Don Mueang Airport', city: 'Bangkok', country: 'Thailand', countryCode: 'TH', type: 'airport' },
  { code: 'THLCH', name: 'Laem Chabang Port', city: 'Chonburi', country: 'Thailand', countryCode: 'TH', type: 'seaport' },
  { code: 'THBKK', name: 'Bangkok Port', city: 'Bangkok', country: 'Thailand', countryCode: 'TH', type: 'seaport' },
  
  // Europe
  { code: 'LHR', name: 'London Heathrow Airport', city: 'London', country: 'UK', countryCode: 'GB', type: 'airport' },
  { code: 'FRA', name: 'Frankfurt Airport', city: 'Frankfurt', country: 'Germany', countryCode: 'DE', type: 'airport' },
  { code: 'AMS', name: 'Amsterdam Schiphol Airport', city: 'Amsterdam', country: 'Netherlands', countryCode: 'NL', type: 'airport' },
  { code: 'CDG', name: 'Paris Charles de Gaulle Airport', city: 'Paris', country: 'France', countryCode: 'FR', type: 'airport' },
  { code: 'NLRTM', name: 'Port of Rotterdam', city: 'Rotterdam', country: 'Netherlands', countryCode: 'NL', type: 'seaport' },
  { code: 'DEHAM', name: 'Port of Hamburg', city: 'Hamburg', country: 'Germany', countryCode: 'DE', type: 'seaport' },
  { code: 'BEANR', name: 'Port of Antwerp', city: 'Antwerp', country: 'Belgium', countryCode: 'BE', type: 'seaport' },
  { code: 'GBFXT', name: 'Port of Felixstowe', city: 'Felixstowe', country: 'UK', countryCode: 'GB', type: 'seaport' },
  
  // UAE
  { code: 'DXB', name: 'Dubai International Airport', city: 'Dubai', country: 'UAE', countryCode: 'AE', type: 'airport' },
  { code: 'AEJEA', name: 'Jebel Ali Port', city: 'Dubai', country: 'UAE', countryCode: 'AE', type: 'seaport' },
  
  // Malaysia
  { code: 'KUL', name: 'Kuala Lumpur International Airport', city: 'Kuala Lumpur', country: 'Malaysia', countryCode: 'MY', type: 'airport' },
  { code: 'MYPKG', name: 'Port Klang', city: 'Klang', country: 'Malaysia', countryCode: 'MY', type: 'seaport' },
  
  // Taiwan
  { code: 'TPE', name: 'Taiwan Taoyuan International Airport', city: 'Taipei', country: 'Taiwan', countryCode: 'TW', type: 'airport' },
  { code: 'TWKHH', name: 'Port of Kaohsiung', city: 'Kaohsiung', country: 'Taiwan', countryCode: 'TW', type: 'seaport' },
];

// Create lookup map for O(1) access
const PORT_MAP = new Map<string, PortInfo>();
PORTS_DATABASE.forEach(port => {
  PORT_MAP.set(port.code.toUpperCase(), port);
});

/**
 * Get port information by code
 * @param portCode - Port code (e.g., 'SGN', 'LAX', 'VNSGN')
 * @returns PortInfo or null if not found
 */
export function getPortInfo(portCode: string | null | undefined): PortInfo | null {
  if (!portCode) return null;
  const code = portCode.toUpperCase();
  return PORT_MAP.get(code) || null;
}

/**
 * Get port information with fallback defaults
 * @param portCode - Port code
 * @returns PortInfo with fallback values if not found
 */
export function getPortInfoWithFallback(portCode: string | null | undefined): PortInfo {
  const info = getPortInfo(portCode);
  if (info) return info;
  
  // Fallback to defaults
  const code = (portCode || 'SGN').toUpperCase();
  return {
    code,
    name: code,
    city: code,
    country: 'Unknown',
    countryCode: 'XX',
    type: 'airport', // Default to airport
  };
}

/**
 * Search ports by code or name (case-insensitive)
 * @param query - Search query
 * @param limit - Maximum results (default 10)
 * @returns Array of matching PortInfo
 */
export function searchPorts(query: string, limit = 10): PortInfo[] {
  if (!query || query.trim().length === 0) {
    return PORTS_DATABASE.slice(0, limit);
  }
  
  const normalizedQuery = query.toUpperCase().trim();
  const matches: PortInfo[] = [];
  
  for (const port of PORTS_DATABASE) {
    if (matches.length >= limit) break;
    
    if (
      port.code.toUpperCase().includes(normalizedQuery) ||
      port.name.toUpperCase().includes(normalizedQuery) ||
      port.city.toUpperCase().includes(normalizedQuery) ||
      port.country.toUpperCase().includes(normalizedQuery)
    ) {
      matches.push(port);
    }
  }
  
  return matches;
}
