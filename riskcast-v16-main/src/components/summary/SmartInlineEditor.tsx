import { useState, useEffect, useRef, useCallback } from 'react';
import { X, Check, AlertCircle, Search, MapPin, Clock, Plane, Ship, Truck, Train } from 'lucide-react';

// ============================================
// COMPREHENSIVE PORTS DATABASE (from airports_ports.json + logistics_data)
// ============================================
const PORTS_DATABASE = [
  // Vietnam Airports
  { code: 'SGN', name: 'Tan Son Nhat International Airport', city: 'Ho Chi Minh City', country: 'VN', countryName: 'Vietnam', type: 'airport' },
  { code: 'HAN', name: 'Noi Bai International Airport', city: 'Hanoi', country: 'VN', countryName: 'Vietnam', type: 'airport' },
  { code: 'DAD', name: 'Da Nang International Airport', city: 'Da Nang', country: 'VN', countryName: 'Vietnam', type: 'airport' },
  { code: 'CXR', name: 'Cam Ranh International Airport', city: 'Nha Trang', country: 'VN', countryName: 'Vietnam', type: 'airport' },
  { code: 'PQC', name: 'Phu Quoc International Airport', city: 'Phu Quoc', country: 'VN', countryName: 'Vietnam', type: 'airport' },
  
  // Vietnam Seaports
  { code: 'VNSGN', name: 'Saigon Port (Cat Lai)', city: 'Ho Chi Minh City', country: 'VN', countryName: 'Vietnam', type: 'seaport' },
  { code: 'VNHPH', name: 'Hai Phong Port', city: 'Hai Phong', country: 'VN', countryName: 'Vietnam', type: 'seaport' },
  { code: 'VNCMP', name: 'Cai Mep International Terminal', city: 'Vung Tau', country: 'VN', countryName: 'Vietnam', type: 'seaport' },
  { code: 'VNDAD', name: 'Da Nang Port (Tien Sa)', city: 'Da Nang', country: 'VN', countryName: 'Vietnam', type: 'seaport' },
  
  // China Airports
  { code: 'PVG', name: 'Shanghai Pudong International Airport', city: 'Shanghai', country: 'CN', countryName: 'China', type: 'airport' },
  { code: 'SHA', name: 'Shanghai Hongqiao Airport', city: 'Shanghai', country: 'CN', countryName: 'China', type: 'airport' },
  { code: 'PEK', name: 'Beijing Capital International Airport', city: 'Beijing', country: 'CN', countryName: 'China', type: 'airport' },
  { code: 'CAN', name: 'Guangzhou Baiyun Airport', city: 'Guangzhou', country: 'CN', countryName: 'China', type: 'airport' },
  { code: 'SZX', name: 'Shenzhen Bao\'an Airport', city: 'Shenzhen', country: 'CN', countryName: 'China', type: 'airport' },
  
  // China Seaports
  { code: 'CNSHA', name: 'Port of Shanghai', city: 'Shanghai', country: 'CN', countryName: 'China', type: 'seaport' },
  { code: 'CNNGB', name: 'Ningbo-Zhoushan Port', city: 'Ningbo', country: 'CN', countryName: 'China', type: 'seaport' },
  { code: 'CNSZX', name: 'Shenzhen Port (Yantian)', city: 'Shenzhen', country: 'CN', countryName: 'China', type: 'seaport' },
  { code: 'CNQIN', name: 'Port of Qingdao', city: 'Qingdao', country: 'CN', countryName: 'China', type: 'seaport' },
  { code: 'CNDLC', name: 'Port of Dalian', city: 'Dalian', country: 'CN', countryName: 'China', type: 'seaport' },
  { code: 'CNXMN', name: 'Port of Xiamen', city: 'Xiamen', country: 'CN', countryName: 'China', type: 'seaport' },
  
  // USA Airports
  { code: 'LAX', name: 'Los Angeles International Airport', city: 'Los Angeles', country: 'US', countryName: 'USA', type: 'airport' },
  { code: 'JFK', name: 'John F. Kennedy International Airport', city: 'New York', country: 'US', countryName: 'USA', type: 'airport' },
  { code: 'ORD', name: "O'Hare International Airport", city: 'Chicago', country: 'US', countryName: 'USA', type: 'airport' },
  { code: 'SFO', name: 'San Francisco International Airport', city: 'San Francisco', country: 'US', countryName: 'USA', type: 'airport' },
  { code: 'MIA', name: 'Miami International Airport', city: 'Miami', country: 'US', countryName: 'USA', type: 'airport' },
  { code: 'SEA', name: 'Seattle-Tacoma International Airport', city: 'Seattle', country: 'US', countryName: 'USA', type: 'airport' },
  { code: 'DFW', name: 'Dallas/Fort Worth International Airport', city: 'Dallas', country: 'US', countryName: 'USA', type: 'airport' },
  
  // USA Seaports
  { code: 'USLAX', name: 'Port of Los Angeles', city: 'Los Angeles', country: 'US', countryName: 'USA', type: 'seaport' },
  { code: 'USLGB', name: 'Port of Long Beach', city: 'Long Beach', country: 'US', countryName: 'USA', type: 'seaport' },
  { code: 'USNYC', name: 'Port of New York/New Jersey', city: 'New York', country: 'US', countryName: 'USA', type: 'seaport' },
  { code: 'USOAK', name: 'Port of Oakland', city: 'Oakland', country: 'US', countryName: 'USA', type: 'seaport' },
  { code: 'USSEA', name: 'Port of Seattle/Tacoma', city: 'Seattle', country: 'US', countryName: 'USA', type: 'seaport' },
  { code: 'USSAV', name: 'Port of Savannah', city: 'Savannah', country: 'US', countryName: 'USA', type: 'seaport' },
  { code: 'USHOU', name: 'Port of Houston', city: 'Houston', country: 'US', countryName: 'USA', type: 'seaport' },
  
  // Hong Kong
  { code: 'HKG', name: 'Hong Kong International Airport', city: 'Hong Kong', country: 'HK', countryName: 'Hong Kong', type: 'airport' },
  { code: 'HKHKG', name: 'Port of Hong Kong', city: 'Hong Kong', country: 'HK', countryName: 'Hong Kong', type: 'seaport' },
  
  // Singapore
  { code: 'SIN', name: 'Singapore Changi Airport', city: 'Singapore', country: 'SG', countryName: 'Singapore', type: 'airport' },
  { code: 'SGSIN', name: 'Port of Singapore', city: 'Singapore', country: 'SG', countryName: 'Singapore', type: 'seaport' },
  
  // Japan
  { code: 'NRT', name: 'Narita International Airport', city: 'Tokyo', country: 'JP', countryName: 'Japan', type: 'airport' },
  { code: 'HND', name: 'Tokyo Haneda Airport', city: 'Tokyo', country: 'JP', countryName: 'Japan', type: 'airport' },
  { code: 'KIX', name: 'Kansai International Airport', city: 'Osaka', country: 'JP', countryName: 'Japan', type: 'airport' },
  { code: 'JPTYO', name: 'Port of Tokyo', city: 'Tokyo', country: 'JP', countryName: 'Japan', type: 'seaport' },
  { code: 'JPYOK', name: 'Port of Yokohama', city: 'Yokohama', country: 'JP', countryName: 'Japan', type: 'seaport' },
  
  // South Korea
  { code: 'ICN', name: 'Incheon International Airport', city: 'Seoul', country: 'KR', countryName: 'South Korea', type: 'airport' },
  { code: 'KRPUS', name: 'Port of Busan', city: 'Busan', country: 'KR', countryName: 'South Korea', type: 'seaport' },
  { code: 'KRICN', name: 'Port of Incheon', city: 'Incheon', country: 'KR', countryName: 'South Korea', type: 'seaport' },
  
  // Thailand
  { code: 'BKK', name: 'Suvarnabhumi Airport', city: 'Bangkok', country: 'TH', countryName: 'Thailand', type: 'airport' },
  { code: 'DMK', name: 'Don Mueang Airport', city: 'Bangkok', country: 'TH', countryName: 'Thailand', type: 'airport' },
  { code: 'THLCH', name: 'Laem Chabang Port', city: 'Chonburi', country: 'TH', countryName: 'Thailand', type: 'seaport' },
  { code: 'THBKK', name: 'Bangkok Port', city: 'Bangkok', country: 'TH', countryName: 'Thailand', type: 'seaport' },
  
  // Europe
  { code: 'LHR', name: 'London Heathrow Airport', city: 'London', country: 'GB', countryName: 'UK', type: 'airport' },
  { code: 'FRA', name: 'Frankfurt Airport', city: 'Frankfurt', country: 'DE', countryName: 'Germany', type: 'airport' },
  { code: 'AMS', name: 'Amsterdam Schiphol Airport', city: 'Amsterdam', country: 'NL', countryName: 'Netherlands', type: 'airport' },
  { code: 'CDG', name: 'Paris Charles de Gaulle Airport', city: 'Paris', country: 'FR', countryName: 'France', type: 'airport' },
  { code: 'NLRTM', name: 'Port of Rotterdam', city: 'Rotterdam', country: 'NL', countryName: 'Netherlands', type: 'seaport' },
  { code: 'DEHAM', name: 'Port of Hamburg', city: 'Hamburg', country: 'DE', countryName: 'Germany', type: 'seaport' },
  { code: 'BEANR', name: 'Port of Antwerp', city: 'Antwerp', country: 'BE', countryName: 'Belgium', type: 'seaport' },
  { code: 'GBFXT', name: 'Port of Felixstowe', city: 'Felixstowe', country: 'GB', countryName: 'UK', type: 'seaport' },
  
  // UAE
  { code: 'DXB', name: 'Dubai International Airport', city: 'Dubai', country: 'AE', countryName: 'UAE', type: 'airport' },
  { code: 'AEJEA', name: 'Jebel Ali Port', city: 'Dubai', country: 'AE', countryName: 'UAE', type: 'seaport' },
  
  // Malaysia
  { code: 'KUL', name: 'Kuala Lumpur International Airport', city: 'Kuala Lumpur', country: 'MY', countryName: 'Malaysia', type: 'airport' },
  { code: 'MYPKG', name: 'Port Klang', city: 'Klang', country: 'MY', countryName: 'Malaysia', type: 'seaport' },
  
  // Taiwan
  { code: 'TPE', name: 'Taiwan Taoyuan International Airport', city: 'Taipei', country: 'TW', countryName: 'Taiwan', type: 'airport' },
  { code: 'TWKHH', name: 'Port of Kaohsiung', city: 'Kaohsiung', country: 'TW', countryName: 'Taiwan', type: 'seaport' },
];

// ============================================
// CARRIERS DATABASE (from carriers.json)
// ============================================
const CARRIERS_DATABASE = [
  // Sea Carriers
  { code: 'MAERSK', name: 'Maersk Line', mode: 'SEA', reliability: 85, icon: '🚢' },
  { code: 'MSC', name: 'Mediterranean Shipping Company', mode: 'SEA', reliability: 82, icon: '🚢' },
  { code: 'ONE', name: 'Ocean Network Express', mode: 'SEA', reliability: 78, icon: '🚢' },
  { code: 'COSCO', name: 'COSCO Shipping', mode: 'SEA', reliability: 80, icon: '🚢' },
  { code: 'HPL', name: 'Hapag-Lloyd', mode: 'SEA', reliability: 76, icon: '🚢' },
  { code: 'EVERGREEN', name: 'Evergreen Line', mode: 'SEA', reliability: 79, icon: '🚢' },
  { code: 'YANGMING', name: 'Yang Ming Marine', mode: 'SEA', reliability: 74, icon: '🚢' },
  { code: 'HMM', name: 'HMM (Hyundai)', mode: 'SEA', reliability: 77, icon: '🚢' },
  { code: 'CMA', name: 'CMA CGM', mode: 'SEA', reliability: 81, icon: '🚢' },
  { code: 'ZIM', name: 'ZIM Integrated Shipping', mode: 'SEA', reliability: 72, icon: '🚢' },
  
  // Air Carriers
  { code: 'VNA', name: 'Vietnam Airlines Cargo', mode: 'AIR', reliability: 89, icon: '✈️' },
  { code: 'KE', name: 'Korean Air Cargo', mode: 'AIR', reliability: 93, icon: '✈️' },
  { code: 'ANA', name: 'All Nippon Airways Cargo', mode: 'AIR', reliability: 95, icon: '✈️' },
  { code: 'LH', name: 'Lufthansa Cargo', mode: 'AIR', reliability: 90, icon: '✈️' },
  { code: 'CX', name: 'Cathay Pacific Cargo', mode: 'AIR', reliability: 88, icon: '✈️' },
  { code: 'SQ', name: 'Singapore Airlines Cargo', mode: 'AIR', reliability: 91, icon: '✈️' },
  { code: 'EK', name: 'Emirates SkyCargo', mode: 'AIR', reliability: 87, icon: '✈️' },
  { code: 'TK', name: 'Turkish Airlines Cargo', mode: 'AIR', reliability: 84, icon: '✈️' },
  { code: 'FX', name: 'FedEx Express', mode: 'AIR', reliability: 94, icon: '✈️' },
  { code: 'UPS', name: 'UPS Airlines', mode: 'AIR', reliability: 92, icon: '✈️' },
  { code: 'DHL', name: 'DHL Express', mode: 'AIR', reliability: 93, icon: '✈️' },
];

// ============================================
// CONTAINER TYPES
// ============================================
const CONTAINER_TYPES = {
  SEA: [
    { value: '20GP', label: "20' General Purpose", desc: 'Standard 20ft dry container' },
    { value: '40GP', label: "40' General Purpose", desc: 'Standard 40ft dry container' },
    { value: '40HC', label: "40' High Cube", desc: 'Extra height (9\'6")' },
    { value: '20RF', label: "20' Reefer", desc: 'Temperature controlled' },
    { value: '40RF', label: "40' Reefer", desc: 'Temperature controlled' },
    { value: '20OT', label: "20' Open Top", desc: 'For oversized cargo' },
    { value: '40OT', label: "40' Open Top", desc: 'For oversized cargo' },
    { value: '20FR', label: "20' Flat Rack", desc: 'For heavy/odd shapes' },
    { value: '40FR', label: "40' Flat Rack", desc: 'For heavy/odd shapes' },
    { value: 'LCL', label: 'LCL (Less than Container)', desc: 'Shared container space' },
    { value: 'FCL', label: 'FCL (Full Container)', desc: 'Full container load' },
  ],
  AIR: [
    { value: 'ULD-AKE', label: 'ULD-AKE (LD3)', desc: 'Standard narrow-body' },
    { value: 'ULD-AKH', label: 'ULD-AKH (LD3-45)', desc: 'Contour container' },
    { value: 'ULD-AQY', label: 'ULD-AQY (LD7)', desc: 'Wide-body main deck' },
    { value: 'ULD-PMC', label: 'ULD-PMC (P6P)', desc: '96x125 pallet' },
    { value: 'ULD-PGF', label: 'ULD-PGF (P1P)', desc: '88x125 pallet' },
    { value: 'LOOSE', label: 'Loose Cargo', desc: 'Non-containerized' },
  ],
  ROAD: [
    { value: 'FTL', label: 'FTL (Full Truck Load)', desc: 'Dedicated truck' },
    { value: 'LTL', label: 'LTL (Less Than Truck)', desc: 'Shared truck space' },
    { value: 'FLATBED', label: 'Flatbed Trailer', desc: 'For oversized cargo' },
    { value: 'REEFER', label: 'Reefer Truck', desc: 'Temperature controlled' },
  ],
  RAIL: [
    { value: 'FCL', label: 'FCL Rail Container', desc: 'Full container by rail' },
    { value: 'LCL', label: 'LCL Rail Container', desc: 'Shared container by rail' },
    { value: 'BOXCAR', label: 'Boxcar', desc: 'Rail boxcar' },
  ],
};

// ============================================
// CARGO TYPES
// ============================================
const CARGO_TYPES = [
  { value: 'electronics', label: 'Electronics & Technology', icon: '💻', desc: 'Phones, computers, components' },
  { value: 'textiles', label: 'Textiles & Apparel', icon: '👕', desc: 'Clothing, fabrics, footwear' },
  { value: 'machinery', label: 'Machinery & Equipment', icon: '⚙️', desc: 'Industrial machines, parts' },
  { value: 'food', label: 'Food & Beverages', icon: '🍎', desc: 'Perishable goods, drinks' },
  { value: 'chemicals', label: 'Chemicals', icon: '🧪', desc: 'Industrial chemicals, paints' },
  { value: 'automotive', label: 'Automotive Parts', icon: '🚗', desc: 'Car parts, accessories' },
  { value: 'furniture', label: 'Furniture & Home', icon: '🪑', desc: 'Home goods, decor' },
  { value: 'pharmaceuticals', label: 'Pharmaceuticals', icon: '💊', desc: 'Medicine, medical supplies' },
  { value: 'raw_materials', label: 'Raw Materials', icon: '🪨', desc: 'Metals, minerals, wood' },
  { value: 'consumer_goods', label: 'Consumer Goods', icon: '📦', desc: 'General retail products' },
  { value: 'perishables', label: 'Perishables', icon: '❄️', desc: 'Requires cold chain' },
  { value: 'hazmat', label: 'Hazardous Materials', icon: '☣️', desc: 'DG class goods' },
];

// ============================================
// INCOTERMS 2020
// ============================================
const INCOTERMS = [
  { value: 'EXW', label: 'EXW - Ex Works', desc: 'Seller makes goods available at their premises', risk: 'Seller: Minimal | Buyer: Maximum' },
  { value: 'FCA', label: 'FCA - Free Carrier', desc: 'Seller delivers to carrier nominated by buyer', risk: 'Seller: Low | Buyer: High' },
  { value: 'FAS', label: 'FAS - Free Alongside Ship', desc: 'Seller delivers alongside vessel at port', risk: 'Seller: Medium-Low | Buyer: Medium-High' },
  { value: 'FOB', label: 'FOB - Free On Board', desc: 'Seller loads goods on vessel nominated by buyer', risk: 'Seller: Medium | Buyer: Medium' },
  { value: 'CFR', label: 'CFR - Cost and Freight', desc: 'Seller pays freight to destination port', risk: 'Seller: Medium-High | Buyer: Medium-Low' },
  { value: 'CIF', label: 'CIF - Cost, Insurance, Freight', desc: 'Seller pays freight and insurance', risk: 'Seller: High | Buyer: Low' },
  { value: 'CPT', label: 'CPT - Carriage Paid To', desc: 'Seller pays carriage to named place', risk: 'Seller: High | Buyer: Low' },
  { value: 'CIP', label: 'CIP - Carriage and Insurance Paid', desc: 'Seller pays carriage and insurance', risk: 'Seller: High | Buyer: Low' },
  { value: 'DAP', label: 'DAP - Delivered at Place', desc: 'Seller delivers goods ready for unloading', risk: 'Seller: Very High | Buyer: Very Low' },
  { value: 'DPU', label: 'DPU - Delivered at Place Unloaded', desc: 'Seller delivers and unloads goods', risk: 'Seller: Very High | Buyer: Very Low' },
  { value: 'DDP', label: 'DDP - Delivered Duty Paid', desc: 'Seller delivers goods cleared for import', risk: 'Seller: Maximum | Buyer: Minimal' },
];

// ============================================
// TRANSPORT MODES
// ============================================
const TRANSPORT_MODES = [
  { value: 'AIR', label: 'Air Freight', icon: <Plane className="w-5 h-5" />, desc: 'Fast delivery, higher cost', color: 'from-sky-400 to-blue-500' },
  { value: 'SEA', label: 'Sea Freight', icon: <Ship className="w-5 h-5" />, desc: 'Cost-effective for large volumes', color: 'from-cyan-400 to-teal-500' },
  { value: 'ROAD', label: 'Road Transport', icon: <Truck className="w-5 h-5" />, desc: 'Flexible door-to-door delivery', color: 'from-amber-400 to-orange-500' },
  { value: 'RAIL', label: 'Rail Freight', icon: <Train className="w-5 h-5" />, desc: 'Efficient for long distances', color: 'from-purple-400 to-indigo-500' },
  { value: 'MULTIMODAL', label: 'Multimodal', icon: <span className="text-lg">🔄</span>, desc: 'Combined transport modes', color: 'from-pink-400 to-rose-500' },
];

interface SmartInlineEditorProps {
  isOpen: boolean;
  field: string;
  label: string;
  value: unknown;
  type: 'text' | 'number' | 'date' | 'select' | 'checkbox' | 'textarea' | 'port' | 'cargo_type' | 'incoterm' | 'mode' | 'carrier' | 'container';
  options?: Array<{ value: string; label: string }>;
  position: { x: number; y: number };
  transportMode?: string; // For container type selection
  onSave: (value: unknown) => void;
  onClose: () => void;
}

export function SmartInlineEditor({ 
  isOpen, 
  field, 
  label, 
  value, 
  type, 
  options, 
  position,
  transportMode = 'SEA',
  onSave, 
  onClose 
}: SmartInlineEditorProps) {
  const [localValue, setLocalValue] = useState<string>(String(value ?? ''));
  const [error, setError] = useState<string | null>(null);
  const [isValid, setIsValid] = useState<boolean>(false);
  const [suggestions, setSuggestions] = useState<typeof PORTS_DATABASE>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [recentPorts, setRecentPorts] = useState<typeof PORTS_DATABASE>([]);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Load recent ports from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem('recent_ports');
      if (saved) {
        const codes = JSON.parse(saved) as string[];
        const recent = codes
          .map(code => PORTS_DATABASE.find(p => p.code === code))
          .filter(Boolean) as typeof PORTS_DATABASE;
        setRecentPorts(recent.slice(0, 5));
      }
    } catch (e) {
      console.warn('Failed to load recent ports:', e);
    }
  }, []);

  // Save to recent ports
  const saveToRecent = useCallback((code: string) => {
    try {
      const saved = localStorage.getItem('recent_ports');
      const codes = saved ? JSON.parse(saved) as string[] : [];
      const updated = [code, ...codes.filter(c => c !== code)].slice(0, 10);
      localStorage.setItem('recent_ports', JSON.stringify(updated));
    } catch (e) {
      console.warn('Failed to save recent port:', e);
    }
  }, []);

  useEffect(() => {
    setLocalValue(String(value ?? ''));
    setError(null);
    validateValue(String(value ?? ''));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, field]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
      
      // Auto-show suggestions for port type when opening
      if (type === 'port') {
        const currentValue = String(value ?? '');
        if (currentValue) {
          // Search with current value to show matching ports - inline logic
          const q = currentValue.toLowerCase();
          const results = PORTS_DATABASE.filter(p =>
            p.code.toLowerCase().includes(q) ||
            p.name.toLowerCase().includes(q) ||
            p.city.toLowerCase().includes(q) ||
            p.country.toLowerCase().includes(q) ||
            p.countryName.toLowerCase().includes(q)
          ).slice(0, 10);
          setSuggestions(results);
          setShowSuggestions(results.length > 0);
        } else {
          // Show recent ports if no value
          setShowSuggestions(false);
        }
      }
    }
  }, [isOpen, type, value]);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  // Validate value
  const validateValue = useCallback((val: string) => {
    if (type === 'port') {
      const found = PORTS_DATABASE.find(p => 
        p.code.toLowerCase() === val.toLowerCase() ||
        p.name.toLowerCase().includes(val.toLowerCase()) ||
        val.toLowerCase().includes(p.code.toLowerCase())
      );
      setIsValid(!!found || val.length >= 2);
      return !!found || val.length >= 2;
    }
    if (type === 'number') {
      const num = Number(val);
      setIsValid(!isNaN(num) && num >= 0);
      return !isNaN(num) && num >= 0;
    }
    if (type === 'date') {
      const date = new Date(val);
      setIsValid(!isNaN(date.getTime()));
      return !isNaN(date.getTime());
    }
    setIsValid(val.length > 0);
    return val.length > 0;
  }, [type]);

  // Search ports
  const searchPorts = useCallback((query: string) => {
    if (!query.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const q = query.toLowerCase();
    const results = PORTS_DATABASE.filter(p =>
      p.code.toLowerCase().includes(q) ||
      p.name.toLowerCase().includes(q) ||
      p.city.toLowerCase().includes(q) ||
      p.country.toLowerCase().includes(q) ||
      p.countryName.toLowerCase().includes(q)
    ).slice(0, 10);

    setSuggestions(results);
    setShowSuggestions(results.length > 0);
    setSelectedIndex(-1);
  }, []);

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setLocalValue(val);
    validateValue(val);

    if (type === 'port') {
      searchPorts(val);
    }
  };

  // Handle suggestion select
  const handleSelectSuggestion = (port: typeof PORTS_DATABASE[0]) => {
    const displayValue = `${port.code} - ${port.name}`;
    setLocalValue(displayValue);
    setIsValid(true);
    setShowSuggestions(false);
    saveToRecent(port.code);
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (type === 'port' && showSuggestions) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(prev => Math.min(prev + 1, suggestions.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(prev => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter' && selectedIndex >= 0 && suggestions[selectedIndex]) {
        e.preventDefault();
        handleSelectSuggestion(suggestions[selectedIndex]);
        return;
      }
    }

    if (e.key === 'Enter' && type !== 'textarea') {
      e.preventDefault();
      handleSave();
    }
  };

  const handleSave = () => {
    if (!validateValue(localValue)) {
      setError('Please enter a valid value');
      return;
    }

    // Extract code from port selection
    let saveValue: unknown = localValue;
    if (type === 'port') {
      const match = localValue.match(/^([A-Z0-9]+)/i);
      if (match && match[1]) {
        saveValue = match[1].toUpperCase();
      }
    } else if (type === 'number') {
      saveValue = Number(localValue);
    }

    onSave(saveValue);
    onClose();
  };

  if (!isOpen) return null;

  // Adjust position to stay within viewport
  const adjustedPosition = {
    x: Math.min(Math.max(position.x, 20), window.innerWidth - 440),
    y: Math.min(Math.max(position.y, 20), window.innerHeight - 500),
  };

  // Popular ports to show by default
  const POPULAR_PORTS = PORTS_DATABASE.filter(p => 
    ['SGN', 'HAN', 'VNSGN', 'VNCMP', 'LAX', 'JFK', 'USLAX', 'CNSHA', 'HKG', 'SIN', 'SGSIN', 'NRT', 'ICN', 'BKK', 'THLCH'].includes(p.code)
  );

  // ============================================
  // RENDER: PORT EDITOR
  // ============================================
  const renderPortEditor = () => {
    // Get ports to display
    const displayPorts = showSuggestions && suggestions.length > 0 
      ? suggestions 
      : (recentPorts.length > 0 ? [] : POPULAR_PORTS.slice(0, 8));

    return (
      <div className="space-y-4">
        {/* Search Input */}
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-cyan-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            ref={inputRef}
            type="text"
            value={localValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Search port code, city or country..."
            className="w-full bg-[#0a1628] border border-cyan-500/30 rounded-xl pl-10 pr-4 py-3.5 text-white placeholder-white/40 focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 transition-all font-medium"
          />
          {isValid && localValue && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1.5 text-emerald-400">
              <Check className="w-4 h-4" />
              <span className="text-sm font-medium">Valid</span>
            </div>
          )}
        </div>

        {/* Recent Ports - Always show if available */}
        {recentPorts.length > 0 && (
          <div>
            <div className="flex items-center gap-2 text-amber-400/70 text-xs font-medium mb-2 px-1">
              <Clock className="w-3.5 h-3.5" />
              <span>Recent Ports:</span>
            </div>
            <div className="space-y-1.5 max-h-40 overflow-y-auto custom-scrollbar">
              {recentPorts.map((port) => (
                <div
                  key={`recent-${port.code}`}
                  onClick={() => handleSelectSuggestion(port)}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-amber-500/5 hover:bg-gradient-to-r hover:from-amber-500/10 hover:to-orange-500/10 border border-amber-500/20 hover:border-amber-400/40 cursor-pointer transition-all group"
                >
                  <span className="px-2 py-0.5 bg-amber-500/20 text-amber-300 text-xs font-bold rounded uppercase tracking-wide">
                    {port.country}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-semibold">{port.code}</span>
                      <span className="text-white/30">-</span>
                      <span className="text-white/70 truncate">{port.city}</span>
                    </div>
                  </div>
                  <span className="text-white/40 text-xs">
                    {port.type === 'airport' ? '✈️' : '🚢'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Search Suggestions or Popular Ports */}
        {(showSuggestions ? suggestions.length > 0 : displayPorts.length > 0) && (
          <div>
            <div className="flex items-center gap-2 text-cyan-400/70 text-xs font-medium mb-2 px-1">
              <MapPin className="w-3.5 h-3.5" />
              <span>{showSuggestions ? 'Search Results:' : 'Popular Ports:'}</span>
            </div>
            <div className="space-y-1.5 max-h-48 overflow-y-auto custom-scrollbar">
              {(showSuggestions ? suggestions : displayPorts).map((port, index) => (
                <div
                  key={`port-${port.code}`}
                  onClick={() => handleSelectSuggestion(port)}
                  className={`
                    flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer transition-all
                    ${index === selectedIndex && showSuggestions
                      ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/50 shadow-lg shadow-cyan-500/10' 
                      : 'bg-white/5 hover:bg-white/10 border border-transparent hover:border-cyan-500/30'
                    }
                  `}
                >
                  <span className={`
                    px-2 py-0.5 text-xs font-bold rounded uppercase tracking-wide
                    ${index === selectedIndex && showSuggestions
                      ? 'bg-cyan-400 text-slate-900' 
                      : 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300'
                    }
                  `}>
                    {port.country}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-semibold">{port.code}</span>
                      <span className="text-white/30">-</span>
                      <span className="text-white/70 truncate">{port.city}</span>
                    </div>
                    <div className="text-white/40 text-xs truncate">{port.name}</div>
                  </div>
                  <span className="text-white/40 text-sm">
                    {port.type === 'airport' ? '✈️' : '🚢'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* All Ports Link */}
        {!showSuggestions && (
          <div className="pt-2 border-t border-white/10">
            <button
              type="button"
              onClick={() => {
                // Show all ports
                setSuggestions(PORTS_DATABASE.slice(0, 20));
                setShowSuggestions(true);
              }}
              className="w-full text-center text-cyan-400/70 hover:text-cyan-300 text-sm py-2 rounded-lg hover:bg-white/5 transition-colors"
            >
              Browse all {PORTS_DATABASE.length} ports →
            </button>
          </div>
        )}
      </div>
    );
  };

  // ============================================
  // RENDER: CARRIER EDITOR
  // ============================================
  const renderCarrierEditor = () => {
    const currentMode = transportMode?.toUpperCase() || 'SEA';
    const filteredCarriers = CARRIERS_DATABASE.filter(c => 
      c.mode === currentMode || currentMode === 'MULTIMODAL'
    );

    return (
      <div className="space-y-4">
        <input
          ref={inputRef}
          type="text"
          value={localValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Search carrier..."
          className="w-full bg-[#0a1628] border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500"
        />
        <div className="space-y-1.5 max-h-64 overflow-y-auto custom-scrollbar">
          {filteredCarriers.map((carrier) => (
            <div
              key={carrier.code}
              onClick={() => {
                setLocalValue(carrier.name);
                setIsValid(true);
              }}
              className={`
                flex items-center gap-3 px-3 py-3 rounded-xl cursor-pointer transition-all
                ${localValue === carrier.name 
                  ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/50' 
                  : 'bg-white/5 hover:bg-white/10 border border-transparent'
                }
              `}
            >
              <span className="text-2xl">{carrier.icon}</span>
              <div className="flex-1">
                <div className="text-white font-medium">{carrier.name}</div>
                <div className="text-white/50 text-xs">Reliability: {carrier.reliability}%</div>
              </div>
              {localValue === carrier.name && (
                <Check className="w-5 h-5 text-cyan-400" />
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // ============================================
  // RENDER: CONTAINER TYPE EDITOR
  // ============================================
  const renderContainerEditor = () => {
    const currentMode = (transportMode?.toUpperCase() || 'SEA') as keyof typeof CONTAINER_TYPES;
    const containers = CONTAINER_TYPES[currentMode] || CONTAINER_TYPES.SEA;

    return (
      <div className="space-y-1.5 max-h-72 overflow-y-auto custom-scrollbar">
        {containers.map((container) => (
          <div
            key={container.value}
            onClick={() => {
              setLocalValue(container.value);
              setIsValid(true);
            }}
            className={`
              px-3 py-3 rounded-xl cursor-pointer transition-all
              ${localValue === container.value 
                ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/50' 
                : 'bg-white/5 hover:bg-white/10 border border-transparent'
              }
            `}
          >
            <div className="flex items-center justify-between">
              <span className="text-white font-medium">{container.label}</span>
              {localValue === container.value && (
                <Check className="w-5 h-5 text-cyan-400" />
              )}
            </div>
            <p className="text-white/50 text-xs mt-1">{container.desc}</p>
          </div>
        ))}
      </div>
    );
  };

  // ============================================
  // RENDER: CARGO TYPE EDITOR
  // ============================================
  const renderCargoTypeEditor = () => (
    <div className="space-y-1.5 max-h-72 overflow-y-auto custom-scrollbar">
      {CARGO_TYPES.map((cargo) => (
        <div
          key={cargo.value}
          onClick={() => {
            setLocalValue(cargo.value);
            setIsValid(true);
          }}
          className={`
            flex items-center gap-3 px-3 py-3 rounded-xl cursor-pointer transition-all
            ${localValue === cargo.value 
              ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/50' 
              : 'bg-white/5 hover:bg-white/10 border border-transparent'
            }
          `}
        >
          <span className="text-2xl w-10 text-center">{cargo.icon}</span>
          <div className="flex-1">
            <div className="text-white font-medium">{cargo.label}</div>
            <div className="text-white/50 text-xs">{cargo.desc}</div>
          </div>
          {localValue === cargo.value && (
            <Check className="w-5 h-5 text-cyan-400" />
          )}
        </div>
      ))}
    </div>
  );

  // ============================================
  // RENDER: INCOTERM EDITOR
  // ============================================
  const renderIncotermEditor = () => (
    <div className="space-y-1.5 max-h-72 overflow-y-auto custom-scrollbar">
      {INCOTERMS.map((term) => (
        <div
          key={term.value}
          onClick={() => {
            setLocalValue(term.value);
            setIsValid(true);
          }}
          className={`
            px-3 py-3 rounded-xl cursor-pointer transition-all
            ${localValue === term.value 
              ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/50' 
              : 'bg-white/5 hover:bg-white/10 border border-transparent'
            }
          `}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-white font-medium">{term.label}</span>
            {localValue === term.value && (
              <Check className="w-5 h-5 text-cyan-400" />
            )}
          </div>
          <p className="text-white/50 text-xs">{term.desc}</p>
          <p className="text-amber-400/60 text-xs mt-1">{term.risk}</p>
        </div>
      ))}
    </div>
  );

  // ============================================
  // RENDER: TRANSPORT MODE EDITOR
  // ============================================
  const renderModeEditor = () => (
    <div className="space-y-2">
      {TRANSPORT_MODES.map((mode) => (
        <div
          key={mode.value}
          onClick={() => {
            setLocalValue(mode.value);
            setIsValid(true);
          }}
          className={`
            flex items-center gap-4 px-4 py-4 rounded-xl cursor-pointer transition-all
            ${localValue === mode.value 
              ? `bg-gradient-to-r ${mode.color} bg-opacity-20 border border-white/20 shadow-lg` 
              : 'bg-white/5 hover:bg-white/10 border border-transparent'
            }
          `}
        >
          <div className={`
            w-12 h-12 rounded-xl flex items-center justify-center text-white
            ${localValue === mode.value 
              ? `bg-gradient-to-r ${mode.color}` 
              : 'bg-white/10'
            }
          `}>
            {mode.icon}
          </div>
          <div className="flex-1">
            <div className="text-white font-semibold">{mode.label}</div>
            <div className="text-white/50 text-sm">{mode.desc}</div>
          </div>
          {localValue === mode.value && (
            <Check className="w-6 h-6 text-white" />
          )}
        </div>
      ))}
    </div>
  );

  // ============================================
  // RENDER: DEFAULT EDITOR
  // ============================================
  const renderDefaultEditor = () => {
    if (type === 'select' && options) {
      return (
        <div className="space-y-1.5 max-h-64 overflow-y-auto custom-scrollbar">
          {options.map((opt) => (
            <div
              key={opt.value}
              onClick={() => {
                setLocalValue(opt.value);
                setIsValid(true);
              }}
              className={`
                flex items-center justify-between px-3 py-3 rounded-xl cursor-pointer transition-all
                ${localValue === opt.value 
                  ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/50' 
                  : 'bg-white/5 hover:bg-white/10 border border-transparent'
                }
              `}
            >
              <span className="text-white font-medium">{opt.label}</span>
              {localValue === opt.value && (
                <Check className="w-5 h-5 text-cyan-400" />
              )}
            </div>
          ))}
        </div>
      );
    }

    if (type === 'checkbox') {
      const isChecked = localValue === 'true' || localValue === '1';
      return (
        <label className="flex items-center gap-4 cursor-pointer p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
          <input
            type="checkbox"
            checked={isChecked}
            onChange={(e) => setLocalValue(String(e.target.checked))}
            className="w-6 h-6 rounded border-white/20 bg-[#0a1628] text-cyan-500 focus:ring-cyan-500 focus:ring-offset-0"
          />
          <span className="text-white font-medium">{isChecked ? 'Yes - Enabled' : 'No - Disabled'}</span>
        </label>
      );
    }

    if (type === 'textarea') {
      return (
        <textarea
          value={localValue}
          onChange={(e) => {
            setLocalValue(e.target.value);
            validateValue(e.target.value);
          }}
          rows={4}
          className="w-full bg-[#0a1628] border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500 resize-none"
        />
      );
    }

    if (type === 'date') {
      return (
        <input
          ref={inputRef}
          type="date"
          value={localValue}
          onChange={(e) => {
            setLocalValue(e.target.value);
            validateValue(e.target.value);
          }}
          onKeyDown={handleKeyDown}
          className="w-full bg-[#0a1628] border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500"
        />
      );
    }

    return (
      <div className="relative">
        <input
          ref={inputRef}
          type={type === 'number' ? 'number' : 'text'}
          value={localValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          className="w-full bg-[#0a1628] border border-white/20 rounded-xl px-4 py-3.5 text-white focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
        />
        {isValid && localValue && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1.5 text-emerald-400">
            <Check className="w-4 h-4" />
            <span className="text-sm font-medium">Valid</span>
          </div>
        )}
      </div>
    );
  };

  // ============================================
  // MAIN RENDER
  // ============================================
  const renderEditor = () => {
    switch (type) {
      case 'port':
        return renderPortEditor();
      case 'cargo_type':
        return renderCargoTypeEditor();
      case 'incoterm':
        return renderIncotermEditor();
      case 'mode':
        return renderModeEditor();
      case 'carrier':
        return renderCarrierEditor();
      case 'container':
        return renderContainerEditor();
      default:
        return renderDefaultEditor();
    }
  };

  return (
    <div
      ref={containerRef}
      className="fixed z-[100] w-[420px] backdrop-blur-2xl bg-gradient-to-br from-[#0d1f35]/98 to-[#0a1628]/98 border border-white/20 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden"
      style={{
        left: adjustedPosition.x,
        top: adjustedPosition.y,
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10 bg-gradient-to-r from-white/5 to-transparent">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-pink-500 flex items-center justify-center shadow-lg shadow-orange-500/30">
            <span className="text-white text-lg">✏️</span>
          </div>
          <div>
            <div className="text-white font-semibold text-lg">Edit: {label}</div>
            <div className="text-white/40 text-xs font-mono">{field}</div>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2.5 hover:bg-white/10 rounded-xl transition-colors"
        >
          <X className="w-5 h-5 text-white/50 hover:text-white" />
        </button>
      </div>

      {/* Body */}
      <div className="p-5 max-h-[60vh] overflow-y-auto custom-scrollbar">
        {renderEditor()}

        {error && (
          <div className="mt-3 flex items-center gap-2 text-red-400 text-sm bg-red-500/10 px-3 py-2 rounded-lg">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-white/10 bg-white/5">
        <button
          onClick={onClose}
          className="px-6 py-2.5 text-white/70 hover:text-white hover:bg-white/10 rounded-xl font-medium transition-all"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={!isValid}
          className={`
            px-6 py-2.5 rounded-xl font-semibold flex items-center gap-2 transition-all
            ${isValid 
              ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/30 hover:shadow-cyan-500/50' 
              : 'bg-white/10 text-white/40 cursor-not-allowed'
            }
          `}
        >
          <Check className="w-4 h-4" />
          Save
        </button>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      `}</style>
    </div>
  );
}
