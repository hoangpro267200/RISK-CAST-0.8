/**
 * Model Version Detail Page
 * Version details, parameters, calibration, usage stats, set-active.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { modelVersionsApi } from '../../api/client';

export default function ModelVersionDetailPage() {
  const { versionId } = useParams<{ versionId: string }>();
  const queryClient = useQueryClient();
  const { data: version, isLoading } = useQuery({
    queryKey: ['model-version', versionId],
    queryFn: () => modelVersionsApi.getVersion(versionId!).then((r) => r.data),
    enabled: !!versionId,
  });
  const { data: active } = useQuery({
    queryKey: ['model-versions-active'],
    queryFn: () => modelVersionsApi.getActive().then((r) => r.data),
  });
  const setActive = useMutation({
    mutationFn: (id: string) => modelVersionsApi.setActive(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['model-versions-active'] });
      queryClient.invalidateQueries({ queryKey: ['model-version', versionId] });
    },
  });

  if (!versionId || isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-white/80">Loading…</p>
      </div>
    );
  }

  if (!version) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-white/80">Version not found.</p>
        <Link to="/app/models" className="text-emerald-400 hover:underline mt-2 inline-block">
          Back to list
        </Link>
      </div>
    );
  }

  const isActive = active?.id === version.id;
  const canSetActive = version.status === 'PUBLISHED' && !isActive;

  return (
    <div className="container mx-auto px-4 py-8">
      <Link to="/app/models" className="text-white/60 hover:text-white mb-4 inline-block">
        ← Back to model versions
      </Link>
      <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">
            {version.name} <span className="text-white/60">v{version.version}</span>
          </h1>
          <p className="text-white/60 mt-1">
            {version.status}
            {isActive && <span className="ml-2 text-emerald-400">(active)</span>}
          </p>
        </div>
        {canSetActive && (
          <button
            type="button"
            onClick={() => setActive.mutate(version.id)}
            disabled={setActive.isPending}
            className="px-4 py-2 rounded bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50"
          >
            Set active
          </button>
        )}
      </div>

      {version.description && (
        <p className="text-white/80 mb-6">{version.description}</p>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <section className="p-4 bg-white/10 rounded-lg">
          <h2 className="text-lg font-semibold text-white mb-2">Info</h2>
          <dl className="space-y-1 text-sm">
            <dt className="text-white/60">ID</dt>
            <dd className="text-white font-mono">{version.id}</dd>
            <dt className="text-white/60 mt-2">Immutable hash</dt>
            <dd className="text-white font-mono break-all">{version.immutable_hash || '—'}</dd>
            <dt className="text-white/60 mt-2">Published</dt>
            <dd className="text-white">{version.published_at ? new Date(version.published_at).toISOString() : '—'}</dd>
          </dl>
        </section>
        <section className="p-4 bg-white/10 rounded-lg">
          <h2 className="text-lg font-semibold text-white mb-2">API</h2>
          <ul className="space-y-2 text-sm">
            <li>
              <a
                href={`/api/v3/models/versions/${versionId}/parameters`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-emerald-400 hover:underline"
              >
                Parameters
              </a>
            </li>
            <li>
              <a
                href={`/api/v3/models/versions/${versionId}/calibration`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-emerald-400 hover:underline"
              >
                Calibration
              </a>
            </li>
            <li>
              <a
                href={`/api/v3/models/versions/${versionId}/usage-stats?days=30`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-emerald-400 hover:underline"
              >
                Usage stats (30d)
              </a>
            </li>
          </ul>
        </section>
      </div>
    </div>
  );
}
