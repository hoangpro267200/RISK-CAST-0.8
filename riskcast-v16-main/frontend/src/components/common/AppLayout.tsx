/**
 * App Layout Component
 * Main layout wrapper for RISKCAST V3 app
 */
import { Outlet } from 'react-router-dom';
import { Suspense } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useTenant } from '../../hooks/useTenant';

// Loading component
const PageLoader = () => (
  <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
    <div className="text-center">
      <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p className="text-white/60">Đang tải trang...</p>
    </div>
  </div>
);

export default function AppLayout() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { tenant, isLoading: tenantLoading } = useTenant();

  // Show loader while checking auth/tenant
  if (authLoading || tenantLoading) {
    return <PageLoader />;
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    window.location.href = '/login';
    return null;
  }

  // Redirect to tenant selection if no tenant
  if (!tenant) {
    window.location.href = '/select-tenant';
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <Suspense fallback={<PageLoader />}>
        <Outlet />
      </Suspense>
    </div>
  );
}
