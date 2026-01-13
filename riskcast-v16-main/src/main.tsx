import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './style.css';
import './styles/perf-a11y.css';
import { initLongTaskObserver, initWebVitals } from './utils/monitoring';

createRoot(document.getElementById('root')!).render(<App />);

void initWebVitals({ app: 'riskcast', surface: 'root' });
initLongTaskObserver({ app: 'riskcast', surface: 'root' });

