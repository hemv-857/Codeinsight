'use client';

import { useQuery } from '@tanstack/react-query';
import { Server } from 'lucide-react';

import { getBackendHealth } from '@/lib/api';
import { cn } from '@/lib/utils';

export function HealthBadge() {
  const health = useQuery({
    queryKey: ['backend-health'],
    queryFn: getBackendHealth,
    retry: 1,
  });

  const isHealthy = health.data?.status === 'ok';
  const label = health.data?.status === 'ok' ? `${health.data.service} online` : 'Backend pending';

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        'flex h-10 items-center gap-2 rounded-md border px-3 text-sm',
        isHealthy
          ? 'border-accent/50 bg-accent/10 text-accent'
          : 'border-border bg-muted text-muted-foreground',
      )}
    >
      <Server className="h-4 w-4" />
      {label}
    </div>
  );
}
