/**
 * React Router Configuration
 * Main routing setup for RISKCAST V3
 */
import { createBrowserRouter } from 'react-router-dom';
import { lazy } from 'react';

// Lazy load pages for code splitting
const NewAssessment = lazy(() => import('../../frontend/src/pages/risk/NewAssessment'));
const RunDetail = lazy(() => import('../../frontend/src/pages/risk/RunDetail'));
const SubmissionsList = lazy(() => import('../../frontend/src/pages/underwriting/SubmissionsList'));
const SubmissionDetail = lazy(() => import('../../frontend/src/pages/underwriting/SubmissionDetail'));
const ClaimsList = lazy(() => import('../../frontend/src/pages/claims/ClaimsList'));
const ClaimDetail = lazy(() => import('../../frontend/src/pages/claims/ClaimDetail'));
const AuditExplorer = lazy(() => import('../../frontend/src/pages/compliance/AuditExplorer'));
const EvidenceViewer = lazy(() => import('../../frontend/src/pages/compliance/EvidenceViewer'));

// App Layout component (to be created)
const AppLayout = lazy(() => import('../../frontend/src/components/common/AppLayout'));

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
      }
    ]
  }
]);
