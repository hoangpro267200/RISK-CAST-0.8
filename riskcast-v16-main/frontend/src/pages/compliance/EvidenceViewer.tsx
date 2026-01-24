/**
 * Evidence Viewer Page
 * View evidence bundle
 */
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { evidenceApi } from '../../api/client';

export default function EvidenceViewer() {
  const { bundleId } = useParams<{ bundleId: string }>();
  
  const { data: bundle, isLoading } = useQuery({
    queryKey: ['evidence-bundle', bundleId!],
    queryFn: () => evidenceApi.getBundle(bundleId!).then(res => res.data),
    enabled: !!bundleId
  });

  if (isLoading) {
    return <div className="text-white">Loading...</div>;
  }

  if (!bundle) {
    return <div className="text-white">Bundle not found</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-white mb-6">Evidence Bundle</h1>
      <div className="bg-white/10 rounded-lg p-6">
        <p className="text-white">Bundle ID: {bundle.bundle_id}</p>
        <p className="text-white">Hash: {bundle.bundle_hash}</p>
        <pre className="text-white/80 mt-4 overflow-auto">
          {JSON.stringify(bundle.manifest, null, 2)}
        </pre>
      </div>
    </div>
  );
}
