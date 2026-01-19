'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  
  useEffect(() => {
    router.push('/dashboard');
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center bg-bg-deep">
      <p className="text-text-medium">Redirecting to dashboard...</p>
    </div>
  );
}
