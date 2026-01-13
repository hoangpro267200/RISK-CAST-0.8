/**
 * Header Language Switcher Component (React)
 * 
 * Inline language toggle for the header bar
 * Supports: Vietnamese (vi), English (en)
 */

import { useState, useEffect, useRef } from 'react';
import { Globe, Check } from 'lucide-react';

interface Language {
  code: string;
  name: string;
  flag: string;
  shortName: string;
}

const LANGUAGES: Language[] = [
  { code: 'vi', name: 'Tiếng Việt', flag: '🇻🇳', shortName: 'VI' },
  { code: 'en', name: 'English', flag: '🇺🇸', shortName: 'EN' },
];

const STORAGE_KEY = 'riskcast_lang';

// Translations for the Results page
const TRANSLATIONS: Record<string, Record<string, string>> = {
  vi: {
    overview: 'Tổng quan',
    analytics: 'Phân tích',
    decisions: 'Quyết định',
    refresh: 'Làm mới',
    riskScore: 'Điểm rủi ro',
    confidence: 'Độ tin cậy',
    riskLevel: 'Mức rủi ro',
    dataConfidence: 'Độ tin cậy dữ liệu',
    lastUpdated: 'Cập nhật lần cuối',
    engineV2: 'Engine v2',
    shipment: 'Lô hàng',
    route: 'Tuyến đường',
    carrier: 'Hãng vận chuyển',
    etd: 'Ngày gửi dự kiến',
    eta: 'Ngày đến dự kiến',
    riskProfileRadar: 'Radar Hồ Sơ Rủi Ro',
    loading: 'Đang phân tích dữ liệu rủi ro...',
    noData: 'Không có dữ liệu. Vui lòng chạy phân tích trước.',
    error: 'Lỗi phân tích',
    retry: 'Thử lại',
  },
  en: {
    overview: 'Overview',
    analytics: 'Analytics',
    decisions: 'Decisions',
    refresh: 'Refresh',
    riskScore: 'Risk Score',
    confidence: 'Confidence',
    riskLevel: 'Risk Level',
    dataConfidence: 'Data Confidence',
    lastUpdated: 'Last updated',
    engineV2: 'Engine v2',
    shipment: 'Shipment',
    route: 'Route',
    carrier: 'Carrier',
    etd: 'ETD',
    eta: 'ETA',
    riskProfileRadar: 'Risk Profile Radar',
    loading: 'Analyzing Risk Data...',
    noData: 'No data available. Please run analysis first.',
    error: 'Analysis Error',
    retry: 'Retry',
  }
};

// Export translation function
export function useTranslation() {
  const [lang, setLang] = useState(() => localStorage.getItem(STORAGE_KEY) || 'vi');
  
  useEffect(() => {
    const handleLangChange = (e: CustomEvent<{ language: string }>) => {
      setLang(e.detail.language);
    };
    
    window.addEventListener('languageChanged', handleLangChange as EventListener);
    return () => window.removeEventListener('languageChanged', handleLangChange as EventListener);
  }, []);
  
  const t = (key: string) => {
    return TRANSLATIONS[lang]?.[key] || TRANSLATIONS['en'][key] || key;
  };
  
  return { t, lang, setLang };
}

export function HeaderLangSwitcher() {
  const [isOpen, setIsOpen] = useState(false);
  const [currentLang, setCurrentLang] = useState('vi');
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize from localStorage
  useEffect(() => {
    const savedLang = localStorage.getItem(STORAGE_KEY) || 'vi';
    setCurrentLang(savedLang);
    document.documentElement.lang = savedLang;
  }, []);

  // Close on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLanguageChange = (langCode: string) => {
    setCurrentLang(langCode);
    localStorage.setItem(STORAGE_KEY, langCode);
    document.documentElement.lang = langCode;
    
    // Dispatch event for other components
    window.dispatchEvent(new CustomEvent('languageChanged', { 
      detail: { language: langCode } 
    }));

    setIsOpen(false);
    
    // Force re-render by dispatching storage event
    window.dispatchEvent(new StorageEvent('storage', {
      key: STORAGE_KEY,
      newValue: langCode
    }));
  };

  const currentLangData = LANGUAGES.find(l => l.code === currentLang) || LANGUAGES[0];

  return (
    <div ref={containerRef} className="relative">
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all"
        title="Change Language"
      >
        <Globe className="w-4 h-4 text-cyan-400" />
        <span className="text-sm font-medium text-white">{currentLangData.flag} {currentLangData.shortName}</span>
        <svg className={`w-3 h-3 text-white/50 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div 
          className="absolute top-full right-0 mt-2 w-44 rounded-xl overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200"
          style={{
            background: 'linear-gradient(135deg, rgba(20, 25, 30, 0.98), rgba(10, 15, 20, 0.99))',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(20px)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)'
          }}
        >
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleLanguageChange(lang.code)}
              className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-all ${
                lang.code === currentLang
                  ? 'bg-cyan-500/10 text-cyan-400'
                  : 'text-white/70 hover:bg-white/5 hover:text-white'
              }`}
            >
              <span className="text-lg">{lang.flag}</span>
              <div className="flex-1">
                <span className="text-sm font-medium">{lang.shortName}</span>
                <span className="text-xs text-white/40 ml-2">{lang.name}</span>
              </div>
              {lang.code === currentLang && (
                <Check className="w-4 h-4 text-cyan-400" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default HeaderLangSwitcher;

