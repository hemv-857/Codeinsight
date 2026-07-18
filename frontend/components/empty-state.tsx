'use client';

import { motion } from 'framer-motion';
import {
  Code2,
  FileSearch,
  GitBranch,
  GitPullRequest,
  MessageSquare,
  Network,
  Search,
  Shield,
  Sparkles,
  TreePine,
} from 'lucide-react';

const illustrations: Record<string, React.ReactNode> = {
  repo: (
    <svg width="120" height="100" viewBox="0 0 120 100" fill="none" className="mx-auto">
      <rect
        x="20"
        y="15"
        width="80"
        height="70"
        rx="8"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="1.5"
        strokeDasharray="4 4"
        opacity="0.4"
      />
      <rect x="30" y="25" width="25" height="6" rx="2" fill="hsl(var(--accent))" opacity="0.3" />
      <rect
        x="30"
        y="37"
        width="40"
        height="4"
        rx="2"
        fill="hsl(var(--muted-foreground))"
        opacity="0.2"
      />
      <rect
        x="30"
        y="47"
        width="35"
        height="4"
        rx="2"
        fill="hsl(var(--muted-foreground))"
        opacity="0.15"
      />
      <rect
        x="30"
        y="57"
        width="45"
        height="4"
        rx="2"
        fill="hsl(var(--muted-foreground))"
        opacity="0.1"
      />
      <circle cx="85" cy="20" r="12" fill="hsl(var(--accent))" opacity="0.15" />
      <path
        d="M82 20L84 22L89 17"
        stroke="hsl(var(--accent))"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.6"
      />
    </svg>
  ),
  graph: (
    <svg width="120" height="100" viewBox="0 0 120 100" fill="none" className="mx-auto">
      <circle cx="60" cy="50" r="8" stroke="hsl(var(--accent))" strokeWidth="1.5" opacity="0.5" />
      <circle cx="30" cy="30" r="5" fill="hsl(var(--accent))" opacity="0.2" />
      <circle cx="90" cy="30" r="5" fill="hsl(var(--primary))" opacity="0.2" />
      <circle cx="30" cy="70" r="5" fill="hsl(var(--primary))" opacity="0.2" />
      <circle cx="90" cy="70" r="5" fill="hsl(var(--accent))" opacity="0.2" />
      <line
        x1="35"
        y1="33"
        x2="52"
        y2="46"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="1"
        opacity="0.3"
      />
      <line
        x1="85"
        y1="33"
        x2="68"
        y2="46"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="1"
        opacity="0.3"
      />
      <line
        x1="35"
        y1="67"
        x2="52"
        y2="54"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="1"
        opacity="0.3"
      />
      <line
        x1="85"
        y1="67"
        x2="68"
        y2="54"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="1"
        opacity="0.3"
      />
    </svg>
  ),
  search: (
    <svg width="120" height="100" viewBox="0 0 120 100" fill="none" className="mx-auto">
      <circle
        cx="50"
        cy="45"
        r="20"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="1.5"
        opacity="0.3"
      />
      <line
        x1="65"
        y1="60"
        x2="80"
        y2="75"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.3"
      />
      <path
        d="M42 40L48 46L58 36"
        stroke="hsl(var(--accent))"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.5"
      />
    </svg>
  ),
  code: (
    <svg width="120" height="100" viewBox="0 0 120 100" fill="none" className="mx-auto">
      <rect
        x="15"
        y="20"
        width="90"
        height="60"
        rx="6"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="1.5"
        opacity="0.3"
      />
      <path
        d="M35 42L25 50L35 58"
        stroke="hsl(var(--accent))"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.5"
      />
      <path
        d="M75 42L85 50L75 58"
        stroke="hsl(var(--accent))"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.5"
      />
      <line
        x1="55"
        y1="38"
        x2="55"
        y2="62"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="1.5"
        opacity="0.3"
      />
    </svg>
  ),
  chat: (
    <svg width="120" height="100" viewBox="0 0 120 100" fill="none" className="mx-auto">
      <rect
        x="20"
        y="20"
        width="60"
        height="40"
        rx="8"
        stroke="hsl(var(--accent))"
        strokeWidth="1.5"
        opacity="0.4"
      />
      <rect
        x="40"
        y="45"
        width="60"
        height="35"
        rx="8"
        stroke="hsl(var(--primary))"
        strokeWidth="1.5"
        opacity="0.3"
      />
      <rect
        x="30"
        y="30"
        width="30"
        height="3"
        rx="1.5"
        fill="hsl(var(--muted-foreground))"
        opacity="0.2"
      />
      <rect
        x="30"
        y="38"
        width="20"
        height="3"
        rx="1.5"
        fill="hsl(var(--muted-foreground))"
        opacity="0.15"
      />
      <rect
        x="50"
        y="55"
        width="30"
        height="3"
        rx="1.5"
        fill="hsl(var(--muted-foreground))"
        opacity="0.2"
      />
      <rect
        x="50"
        y="63"
        width="25"
        height="3"
        rx="1.5"
        fill="hsl(var(--muted-foreground))"
        opacity="0.15"
      />
    </svg>
  ),
  shield: (
    <svg width="120" height="100" viewBox="0 0 120 100" fill="none" className="mx-auto">
      <path
        d="M60 15L25 30V55C25 75 42 90 60 95C78 90 95 75 95 55V30L60 15Z"
        stroke="hsl(var(--accent))"
        strokeWidth="1.5"
        opacity="0.4"
      />
      <path
        d="M50 52L57 59L72 44"
        stroke="hsl(var(--accent))"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.5"
      />
    </svg>
  ),
  tree: (
    <svg width="120" height="100" viewBox="0 0 120 100" fill="none" className="mx-auto">
      <circle cx="60" cy="25" r="10" stroke="hsl(var(--accent))" strokeWidth="1.5" opacity="0.4" />
      <circle cx="35" cy="55" r="8" stroke="hsl(var(--primary))" strokeWidth="1.5" opacity="0.3" />
      <circle cx="85" cy="55" r="8" stroke="hsl(var(--primary))" strokeWidth="1.5" opacity="0.3" />
      <circle cx="25" cy="80" r="6" fill="hsl(var(--accent))" opacity="0.15" />
      <circle cx="45" cy="80" r="6" fill="hsl(var(--accent))" opacity="0.15" />
      <circle cx="75" cy="80" r="6" fill="hsl(var(--primary))" opacity="0.15" />
      <circle cx="95" cy="80" r="6" fill="hsl(var(--primary))" opacity="0.15" />
      <line
        x1="55"
        y1="35"
        x2="40"
        y2="47"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="1"
        opacity="0.3"
      />
      <line
        x1="65"
        y1="35"
        x2="80"
        y2="47"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="1"
        opacity="0.3"
      />
      <line
        x1="30"
        y1="63"
        x2="28"
        y2="74"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="1"
        opacity="0.25"
      />
      <line
        x1="40"
        y1="63"
        x2="42"
        y2="74"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="1"
        opacity="0.25"
      />
      <line
        x1="80"
        y1="63"
        x2="78"
        y2="74"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="1"
        opacity="0.25"
      />
      <line
        x1="90"
        y1="63"
        x2="92"
        y2="74"
        stroke="hsl(var(--muted-foreground))"
        strokeWidth="1"
        opacity="0.25"
      />
    </svg>
  ),
};

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  repo: GitBranch,
  graph: Network,
  search: Search,
  code: Code2,
  chat: MessageSquare,
  shield: Shield,
  tree: TreePine,
  pr: GitPullRequest,
  file: FileSearch,
  sparkles: Sparkles,
};

interface EmptyStateProps {
  illustration?: string;
  icon?: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({ illustration, icon, title, description, action }: EmptyStateProps) {
  const Icon = icon ? iconMap[icon] : null;
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="flex flex-col items-center justify-center py-12 px-6 text-center"
    >
      {illustration && illustrations[illustration] ? (
        <div className="mb-4">{illustrations[illustration]}</div>
      ) : Icon ? (
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-border bg-muted">
          <Icon className="h-7 w-7 text-accent" />
        </div>
      ) : null}
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </motion.div>
  );
}
