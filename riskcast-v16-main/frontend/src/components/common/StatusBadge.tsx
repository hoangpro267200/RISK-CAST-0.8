/**
 * Status Badge Component
 * Displays status with color coding
 */
interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const getStatusColor = (status: string) => {
    const normalizedStatus = status.toUpperCase();
    
    if (normalizedStatus.includes('SUCCEEDED') || normalizedStatus.includes('ACTIVE') || normalizedStatus.includes('QUOTED')) {
      return 'bg-green-500/20 text-green-300 border-green-500/50';
    }
    if (normalizedStatus.includes('FAILED') || normalizedStatus.includes('DECLINED')) {
      return 'bg-red-500/20 text-red-300 border-red-500/50';
    }
    if (normalizedStatus.includes('RUNNING') || normalizedStatus.includes('REVIEW') || normalizedStatus.includes('SUBMITTED')) {
      return 'bg-blue-500/20 text-blue-300 border-blue-500/50';
    }
    if (normalizedStatus.includes('QUEUED') || normalizedStatus.includes('DRAFT')) {
      return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50';
    }
    
    return 'bg-gray-500/20 text-gray-300 border-gray-500/50';
  };

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(status)} ${className}`}>
      {status}
    </span>
  );
}
