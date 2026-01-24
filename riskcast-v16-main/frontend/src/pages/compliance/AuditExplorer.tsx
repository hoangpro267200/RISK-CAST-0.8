/**
 * Audit Explorer Page
 * Explore audit logs
 */
import { useQuery } from '@tanstack/react-query';
import { auditApi } from '../../api/client';

export default function AuditExplorer() {
  const { data: events, isLoading } = useQuery({
    queryKey: ['audit-events'],
    queryFn: () => auditApi.listEvents().then(res => res.data)
  });

  if (isLoading) {
    return <div className="text-white">Loading...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-white mb-6">Audit Explorer</h1>
      <div className="space-y-4">
        {events?.items?.map((event: any) => (
          <div key={event.id} className="bg-white/10 rounded-lg p-4">
            <p className="text-white">{event.action}</p>
            <p className="text-white/60">{event.occurred_at}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
