/**
 * React Router Configuration
 * Route definitions for RISKCAST V3 frontend
 */
import { createBrowserRouter } from 'react-router-dom';
import { lazy } from 'react';

// Lazy load pages for code splitting
const NewAssessment = lazy(() => import('../pages/risk/NewAssessment'));
const RunDetail = lazy(() => import('../pages/risk/RunDetail'));
const SubmissionsList = lazy(() => import('../pages/underwriting/SubmissionsList'));
const SubmissionDetail = lazy(() => import('../pages/underwriting/SubmissionDetail'));
const ClaimsList = lazy(() => import('../pages/claims/ClaimsList'));
const ClaimDetail = lazy(() => import('../pages/claims/ClaimDetail'));
const AuditExplorer = lazy(() => import('../pages/compliance/AuditExplorer'));
const EvidenceViewer = lazy(() => import('../pages/compliance/EvidenceViewer'));
const ModelVersionsPage = lazy(() => import('../pages/models/ModelVersionsPage'));

// App Layout component (to be created)
const AppLayout = lazy(() => import('../components/common/AppLayout'));

export const router = createBrowserRouter([
  {
    path: '/app',
    element: <AppLayout />,
    children: [
      {
        path: 'risk/assessments/new',
        element: <NewAssessment />
      },
      {
        path: 'risk/runs/:runId',
        element: <RunDetail />
      },
      {
        path: 'underwriting/submissions',
        element: <SubmissionsList />
      },
      {
        path: 'underwriting/submissions/:submissionId',
        element: <SubmissionDetail />
      },
      {
        path: 'claims',
        element: <ClaimsList />
      },
      {
        path: 'claims/:claimId',
        element: <ClaimDetail />
      },
      {
        path: 'compliance/audit',
        element: <AuditExplorer />
      },
      {
        path: 'compliance/evidence/:bundleId',
        element: <EvidenceViewer />
      },
      {
        path: 'models',
        element: <ModelVersionsPage />
      },
      {
        path: 'models/versions/:versionId',
        element: <ModelVersionDetailPage />
      }
    ]
  }
]);
