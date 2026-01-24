/**
 * Claims List Page
 * List insurance claims
 */
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { claimsApi } from '../../api/client';

export default function ClaimsList() {
  const { data: claims, isLoading } = useQuery({
    queryKey: ['claims'],
    queryFn: () => claimsApi.listClaims().then(res => res.data)
  });

  if (isLoading) {
    return <div className="text-white">Loading...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-white mb-6">Claims</h1>
      <div className="space-y-4">
        {claims?.items?.map((claim: any) => (
          <Link
            key={claim.id}
            to={`/app/claims/${claim.id}`}
            className="block bg-white/10 rounded-lg p-4 hover:bg-white/20"
          >
            <p className="text-white">Claim {claim.id}</p>
            <p className="text-white/60">Status: {claim.status}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
