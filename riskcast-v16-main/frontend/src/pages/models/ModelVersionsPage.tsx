/**
 * Model Versions Page
 * List model versions, active version, and links to detail / compare / set-active.
 * UI support for model version management API.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { modelVersionsApi } from '../../api/client';

export default function ModelVersionsPage() {
  const queryClient = useQueryClient();
  const { data: versions, isLoading: versionsLoading } = useQuery({
    queryKey: ['model-versions'],
    queryFn: () => modelVersionsApi.listVersions({ include_deprecated: true, limit: 100 }).then((r) => r.data),
  });
  const { data: active, isLoading: activeLoading } = useQuery({
    queryKey: ['model-versions-active'],
    queryFn: () => modelVersionsApi.getActive().then((r) => r.data),
  });
  const setActive = useMutation({
    mutationFn: (id: string) => modelVersionsApi.setActive(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['model-versions'] });
      queryClient.invalidateQueries({ queryKey: ['model-versions-active'] });
    },
  });

  if (versionsLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-white/80">Loading model versions…</p>
      </div>
    );
  }

  const list = Array.isArray(versions) ? versions : (versions as any)?.items ?? [];
  const activeId = active?.id ?? null;

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-white mb-2">Model Versions</h1>
      <p className="text-white/60 mb-6">
        Manage risk model versions. Set active version for new assessments.
      </p>

      {!activeLoading && active && (
        <section className="mb-8 p-4 bg-emerald-500/20 rounded-lg border border-emerald-500/40">
          <h2 className="text-lg font-semibold text-white mb-2">Active version</h2>
          <p className="text-white/90">
            {active.name} <span className="text-white/60">v{active.version}</span>
          </p>
          <p className="text-white/60 text-sm mt-1">ID: {active.id}</p>
        </section>
      )}

      <section>
        <h2 className="text-xl font-semibold text-white mb-4">All versions</h2>
        <div className="space-y-3">
          {list.map((v: any) => (
            <div
              key={v.id}
              className="flex flex-wrap items-center gap-3 p-4 bg-white/10 rounded-lg hover:bg-white/15"
            >
              <div className="flex-1 min-w-0">
                <p className="text-white font-medium truncate">
                  {v.name} <span className="text-white/60">v{v.version}</span>
                  {activeId === v.id && (
                    <span className="ml-2 text-emerald-400 text-sm">(active)</span>
                  )}
                </p>
                <p className="text-white/60 text-sm">
                  {v.status} · {v.immutable_hash ? 'Hash: ' + String(v.immutable_hash).slice(0, 12) + '…' : '—'}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Link
                  to={`/app/models/versions/${v.id}`}
                  className="px-3 py-1.5 rounded bg-white/20 text-white text-sm hover:bg-white/30"
                >
                  Details
                </Link>
                {v.status === 'PUBLISHED' && activeId !== v.id && (
                  <button
                    type="button"
                    onClick={() => setActive.mutate(v.id)}
                    disabled={setActive.isPending}
                    className="px-3 py-1.5 rounded bg-emerald-600 text-white text-sm hover:bg-emerald-500 disabled:opacity-50"
                  >
                    Set active
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
        {list.length === 0 && (
          <p className="text-white/60">No model versions found.</p>
        )}
      </section>
    </div>
  );
}
