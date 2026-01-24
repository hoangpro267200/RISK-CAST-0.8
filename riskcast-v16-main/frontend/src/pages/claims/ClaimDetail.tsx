/**
 * Claim Detail Page
 * View claim details and timeline
 */
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { claimsApi } from '../../api/client';

export default function ClaimDetail() {
  const { claimId } = useParams<{ claimId: string }>();
  
  const { data: claim, isLoading } = useQuery({
    queryKey: ['claim', claimId!],
    queryFn: () => claimsApi.getClaim(claimId!).then(res => res.data),
    enabled: !!claimId
  });


  if (isLoading) {
    return <div className="text-white">Loading...</div>;
  }

  if (!claim) {
    return <div className="text-white">Claim not found</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-white mb-6">Claim Details</h1>
      <div className="bg-white/10 rounded-lg p-6 mb-6">
        <p className="text-white">ID: {claim.id}</p>
        <p className="text-white">Status: {claim.status}</p>
        {/* More details will be added here */}
      </div>
      
    </div>
  );
}
