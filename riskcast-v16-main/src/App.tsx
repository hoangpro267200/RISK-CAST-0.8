import { useEffect, useState, Suspense } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { initWebVitals } from './utils/webVitals';
import { lazyWithRetry } from './utils/lazyWithRetry';

// Initialize Web Vitals monitoring (Phase 5 - Performance)
if (typeof window !== 'undefined') {
  initWebVitals();
}

// Lazy load pages for code splitting (Phase 5 - Performance)
// Use lazyWithRetry to handle network errors gracefully
const ResultsPage = lazyWithRetry(() => import('./pages/ResultsPage'));
const SummaryPage = lazyWithRetry(() => import('./pages/SummaryPage'));
const InputPage = lazyWithRetry(() => import('./pages/InputPage'));
const LoginPage = lazyWithRetry(() => import('./pages/LoginPage'));
const SignupPage = lazyWithRetry(() => import('./pages/SignupPage'));
const HomePage = lazyWithRetry(() => import('./pages/HomePage'));
const OverviewPage = lazyWithRetry(() => import('./pages/Overview'));

// Loading component for lazy-loaded pages
const PageLoader = () => (
  <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
    <div className="text-center">
      <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p className="text-white/60">Đang tải trang...</p>
    </div>
  </div>
);

type PageType = 'results' | 'summary' | 'input' | 'login' | 'signup' | 'home' | 'overview';

export default function App() {
  const [page, setPage] = useState<PageType>('results');

  useEffect(() => {
    // Determine which page to render based on URL
    const path = window.location.pathname;
    if (path === '/login') {
      setPage('login');
    } else if (path === '/signup') {
      setPage('signup');
    } else if (path === '/overview') {
      setPage('overview');
    } else if (path === '/' || path === '/home') {
      setPage('home');
    } else if (path === '/input' || path === '/input_react' || path.startsWith('/input_react')) {
      setPage('input');
    } else if (path.includes('/summary') || path.includes('/shipments/summary')) {
      setPage('summary');
    } else {
      setPage('results');
    }

    // Listen for popstate (browser back/forward)
    const handlePopState = () => {
      const newPath = window.location.pathname;
      if (newPath === '/login') {
        setPage('login');
      } else if (newPath === '/signup') {
        setPage('signup');
      } else if (newPath === '/overview') {
        setPage('overview');
      } else if (newPath === '/' || newPath === '/home') {
        setPage('home');
      } else if (newPath === '/input' || newPath === '/input_react' || newPath.startsWith('/input_react')) {
        setPage('input');
      } else if (newPath.includes('/summary') || newPath.includes('/shipments/summary')) {
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
        {page === 'login' ? (
          <LoginPage />
        ) : page === 'signup' ? (
          <SignupPage />
        ) : page === 'overview' ? (
          <OverviewPage />
        ) : page === 'home' ? (
          <HomePage />
        ) : page === 'input' ? (
          <InputPage />
        ) : page === 'summary' ? (
          <SummaryPage />
        ) : (
          <ResultsPage />
        )}
      </Suspense>
    </ErrorBoundary>
  );
}
