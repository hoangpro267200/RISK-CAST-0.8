import { useEffect, useState, lazy, Suspense } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { initWebVitals } from './utils/webVitals';

// Initialize Web Vitals monitoring (Phase 5 - Performance)
if (typeof window !== 'undefined') {
  initWebVitals();
}

// Lazy load pages for code splitting (Phase 5 - Performance)
const ResultsPage = lazy(() => import('./pages/ResultsPage'));
const SummaryPage = lazy(() => import('./pages/SummaryPage'));

// Loading component for lazy-loaded pages
const PageLoader = () => (
  <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
    <div className="text-center">
      <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p className="text-white/60">Đang tải trang...</p>
    </div>
  </div>
);

export default function App() {
  const [page, setPage] = useState<'results' | 'summary'>('results');

  useEffect(() => {
    // Determine which page to render based on URL
    const path = window.location.pathname;
    if (path.includes('/summary') || path.includes('/shipments/summary')) {
      setPage('summary');
    } else {
      setPage('results');
    }

    // Listen for popstate (browser back/forward)
    const handlePopState = () => {
      const newPath = window.location.pathname;
      if (newPath.includes('/summary') || newPath.includes('/shipments/summary')) {
        setPage('summary');
      } else {
        setPage('results');
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  return (
    <ErrorBoundary
      title="Đã xảy ra lỗi"
      description="Ứng dụng gặp sự cố. Vui lòng tải lại trang hoặc báo cáo lỗi."
    >
      <Suspense fallback={<PageLoader />}>
        {page === 'summary' ? <SummaryPage /> : <ResultsPage />}
      </Suspense>
    </ErrorBoundary>
  );
}
