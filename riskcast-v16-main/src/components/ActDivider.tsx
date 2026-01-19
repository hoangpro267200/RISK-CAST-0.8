import React from 'react';

export const ActDivider: React.FC = () => {
  return (
    <div className="my-12 flex items-center gap-4">
      <div className="flex-1 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      <div className="w-2 h-2 rounded-full bg-white/30" />
      <div className="flex-1 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
    </div>
  );
};




