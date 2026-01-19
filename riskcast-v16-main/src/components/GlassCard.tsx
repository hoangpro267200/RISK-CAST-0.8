import React from 'react';

export interface GlassCardProps {
  children: React.ReactNode;
  padding?: 'sm' | 'md' | 'lg' | string;
  variant?: 'default' | 'hero' | 'compact';
  glowColor?: string;
  interactive?: boolean;
  className?: string;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  padding = 'md',
  variant = 'default',
  glowColor,
  interactive = false,
  className = '',
}) => {
  const paddingClass =
    typeof padding === 'string' && !['sm', 'md', 'lg'].includes(padding)
      ? padding
      : padding === 'sm'
      ? 'p-4'
      : padding === 'lg'
      ? 'p-8'
      : 'p-6';

  const variantClass =
    variant === 'hero'
      ? 'backdrop-blur-3xl bg-white/8 border border-white/15 rounded-3xl shadow-2xl'
      : variant === 'compact'
      ? 'backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl shadow-xl'
      : 'backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl shadow-2xl';

  const interactiveClass = interactive
    ? 'cursor-pointer hover:bg-white/10 hover:border-white/20 transition-all'
    : '';

  const glowStyle = glowColor
    ? {
        boxShadow: `0 0 20px ${glowColor}, 0 0 40px ${glowColor}80, 0 0 60px ${glowColor}40`,
      }
    : undefined;

  return (
    <div
      className={`${variantClass} ${interactiveClass} ${paddingClass} relative overflow-hidden ${className}`}
      style={glowStyle}
    >
      {glowColor && (
        <div
          className="absolute inset-0 opacity-20 pointer-events-none"
          style={{
            boxShadow: `0 0 20px ${glowColor}, 0 0 40px ${glowColor}80, 0 0 60px ${glowColor}40`,
          }}
        />
      )}
      {children}
    </div>
  );
};




