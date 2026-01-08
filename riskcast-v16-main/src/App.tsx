import { useEffect, useState } from 'react';
import ResultsPage from './pages/ResultsPage';
import SummaryPage from './pages/SummaryPage';

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

  if (page === 'summary') {
    return <SummaryPage />;
  }

  return <ResultsPage />;
}
