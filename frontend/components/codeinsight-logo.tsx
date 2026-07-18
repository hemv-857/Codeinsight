'use client';

interface CodeInsightLogoProps {
  className?: string;
  size?: number;
}

export function CodeInsightLogo({ className = '', size = 32 }: CodeInsightLogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="CodeInsight logo"
    >
      <defs>
        <linearGradient id="ci-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="hsl(var(--accent))" />
          <stop offset="100%" stopColor="hsl(var(--primary))" />
        </linearGradient>
        <linearGradient id="ci-glow" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity="0.3" />
          <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0" />
        </linearGradient>
      </defs>
      <circle cx="32" cy="32" r="30" fill="url(#ci-glow)" />
      <circle cx="32" cy="32" r="28" stroke="url(#ci-gradient)" strokeWidth="2" fill="none" />
      <path
        d="M20 24L28 32L20 40"
        stroke="url(#ci-gradient)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <line
        x1="32"
        y1="40"
        x2="44"
        y2="40"
        stroke="url(#ci-gradient)"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <circle cx="48" cy="20" r="3" fill="hsl(var(--accent))" opacity="0.8" />
      <circle cx="48" cy="20" r="6" stroke="hsl(var(--accent))" strokeWidth="1" opacity="0.3" />
    </svg>
  );
}
