/**
 * Submissions List Page
 * List underwriting submissions with table view
 */
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { underwritingApi } from '../../api/client';
import { StatusBadge } from '../../components/common/StatusBadge';

export function SubmissionsList() {
  const { data: response, isLoading } = useQuery({
    queryKey: ['submissions'],
    queryFn: () => underwritingApi.listSubmissions().then(res => res.data)
  });

  const submissions = response?.items || response || [];

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white/60">Loading submissions...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-white">Underwriting Submissions</h1>

      {submissions.length === 0 ? (
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-8 text-center">
          <p className="text-white/60">No submissions found</p>
        </div>
      ) : (
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-3 px-4 text-white/80 font-semibold">ID</th>
                <th className="text-left py-3 px-4 text-white/80 font-semibold">Status</th>
                <th className="text-left py-3 px-4 text-white/80 font-semibold">Product</th>
                <th className="text-left py-3 px-4 text-white/80 font-semibold">Created</th>
                <th className="text-left py-3 px-4 text-white/80 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {submissions.map((sub: any) => (
                <tr key={sub.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                  <td className="py-3 px-4 font-mono text-sm text-white">
                    {sub.id.slice(0, 8)}...
                  </td>
                  <td className="py-3 px-4">
                    <StatusBadge status={sub.status} />
                  </td>
                  <td className="py-3 px-4 text-white/80">
                    {sub.product_type || 'N/A'}
                  </td>
                  <td className="py-3 px-4 text-white/80">
                    {new Date(sub.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4">
                    <Link 
                      to={`/app/underwriting/submissions/${sub.id}`}
                      className="text-blue-400 hover:text-blue-300 hover:underline transition-colors"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default SubmissionsList;
