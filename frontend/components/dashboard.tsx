'use client';

import { motion } from 'framer-motion';
import { Activity, Braces, GitBranch, Network, Search, ShieldCheck } from 'lucide-react';

import { ArchitecturePreview } from '@/components/architecture-preview';
import { HealthBadge } from '@/components/health-badge';
import { Button } from '@/components/ui/button';

const metrics = [
  { label: 'Files Indexed', value: '0', detail: 'ready for repository import' },
  { label: 'Graph Nodes', value: '0', detail: 'awaiting parser pipeline' },
  { label: 'Health Score', value: '--', detail: 'computed after indexing' },
];

const workflow = [
  { icon: GitBranch, label: 'Import repository' },
  { icon: Braces, label: 'Parse source files' },
  { icon: Network, label: 'Build graph' },
  { icon: Search, label: 'Ask grounded questions' },
];

export function Dashboard() {
  return (
    <main className="min-h-screen px-5 py-6 text-foreground sm:px-8 lg:px-10">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <header className="flex flex-col gap-4 border-b border-border pb-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-medium text-accent">Forge AI</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-normal sm:text-4xl">
              Software system map
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <HealthBadge />
            <Button>
              <GitBranch className="h-4 w-4" />
              Import repository
            </Button>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-3">
          {metrics.map((metric) => (
            <motion.div
              key={metric.label}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-lg border border-border bg-card p-5"
            >
              <p className="text-sm text-muted-foreground">{metric.label}</p>
              <p className="mt-3 text-3xl font-semibold">{metric.value}</p>
              <p className="mt-2 text-sm text-muted-foreground">{metric.detail}</p>
            </motion.div>
          ))}
        </section>

        <section className="grid gap-6 lg:grid-cols-[1fr_420px]">
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">Architecture Graph</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  The graph surface is ready for indexed repository data.
                </p>
              </div>
              <ShieldCheck className="h-5 w-5 text-accent" />
            </div>
            <ArchitecturePreview />
          </div>

          <aside className="rounded-lg border border-border bg-card p-5">
            <div className="flex items-center gap-3">
              <Activity className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold">Indexing Workflow</h2>
            </div>
            <div className="mt-5 space-y-3">
              {workflow.map((item) => (
                <div key={item.label} className="flex items-center gap-3 rounded-md bg-muted p-3">
                  <item.icon className="h-4 w-4 text-accent" />
                  <span className="text-sm">{item.label}</span>
                </div>
              ))}
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
