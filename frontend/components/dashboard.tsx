'use client';

import { motion } from 'framer-motion';
import { Activity, Braces, GitBranch, Network, Search } from 'lucide-react';
import { useState } from 'react';

import { ArchitectureViolationsPanel } from '@/components/architecture-violations-panel';
import { BugImpactPanel } from '@/components/bug-impact-panel';
import { CircularDependenciesPanel } from '@/components/circular-dependencies-panel';
import { DeadCodePanel } from '@/components/dead-code-panel';
import { DependencyGraphPanel } from '@/components/dependency-graph-panel';
import { HealthBadge } from '@/components/health-badge';
import { KnowledgeGraphPanel } from '@/components/knowledge-graph-panel';
import { RepositoryExplorer } from '@/components/repository-explorer';
import { RepositorySearchPanel } from '@/components/repository-search-panel';
import { StackTracePanel } from '@/components/stack-trace-panel';
import { TechnicalDebtPanel } from '@/components/technical-debt-panel';
import { Button } from '@/components/ui/button';
import type { RepositoryScanResult } from '@/lib/api';

const workflow = [
  { icon: GitBranch, label: 'Import repository' },
  { icon: Braces, label: 'Parse source files' },
  { icon: Network, label: 'Build graph' },
  { icon: Search, label: 'Ask grounded questions' },
];

export function Dashboard() {
  const [scan, setScan] = useState<RepositoryScanResult | null>(null);
  const metrics = [
    {
      label: 'Files Indexed',
      value: String(scan?.files.length ?? 0),
      detail: scan
        ? `${scan.directories.length} directories scanned`
        : 'ready for repository import',
    },
    {
      label: 'Languages',
      value: String(scan?.languages.length ?? 0),
      detail: scan?.languages.join(', ') || 'detected after scan',
    },
    {
      label: 'Source Files',
      value: String(scan?.files.filter((file) => file.language !== null).length ?? 0),
      detail: scan ? 'Tree-sitter supported candidates' : 'awaiting parser pipeline',
    },
  ];

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

        <section className="space-y-4">
          <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
            <div>
              <h2 className="text-xl font-semibold">Repository Explorer</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Scan a local path or load an imported repository to inspect files, folders, and
                languages.
              </p>
            </div>
            {scan ? (
              <p className="max-w-full truncate text-sm text-muted-foreground">
                {scan.repository_path}
              </p>
            ) : null}
          </div>
          <RepositoryExplorer onScanLoaded={setScan} />
        </section>

        <section className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">Repository Search</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Search indexed code chunks with vector, keyword, and graph ranking.
              </p>
            </div>
            <Search className="h-5 w-5 text-accent" />
          </div>
          <RepositorySearchPanel scan={scan} />
        </section>

        <section className="grid gap-6 xl:grid-cols-[1fr_320px]">
          <div className="space-y-6">
            <section className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold">Technical Debt</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Analyze maintainability risks from parsed code and dependency structure.
                  </p>
                </div>
                <Activity className="h-5 w-5 text-accent" />
              </div>
              <TechnicalDebtPanel scan={scan} />
            </section>

            <section className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold">Circular Dependencies</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Detect import cycles and inspect the files participating in each loop.
                  </p>
                </div>
                <GitBranch className="h-5 w-5 text-accent" />
              </div>
              <CircularDependenciesPanel scan={scan} />
            </section>

            <section className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold">Dead Code</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Find unreferenced files and uncalled functions from repository graphs.
                  </p>
                </div>
                <Search className="h-5 w-5 text-accent" />
              </div>
              <DeadCodePanel scan={scan} />
            </section>

            <section className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold">Architecture Violations</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Flag layer-boundary imports that cut across the system architecture.
                  </p>
                </div>
                <Activity className="h-5 w-5 text-accent" />
              </div>
              <ArchitectureViolationsPanel scan={scan} />
            </section>

            <section className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold">Stack Trace Parser</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Extract files, functions, lines, and error metadata from runtime traces.
                  </p>
                </div>
                <Activity className="h-5 w-5 text-accent" />
              </div>
              <StackTracePanel />
            </section>

            <section className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold">Bug Impact</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Predict likely root cause and affected files from stack traces and imports.
                  </p>
                </div>
                <Activity className="h-5 w-5 text-accent" />
              </div>
              <BugImpactPanel scan={scan} />
            </section>

            <section className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold">Dependency Graph</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Build the file-level dependency graph from parsed repository imports.
                  </p>
                </div>
                <Network className="h-5 w-5 text-accent" />
              </div>
              <DependencyGraphPanel scan={scan} />
            </section>

            <section className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold">Knowledge Graph</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Persist the repository architecture graph for AI and graph traversal.
                  </p>
                </div>
                <Network className="h-5 w-5 text-accent" />
              </div>
              <KnowledgeGraphPanel scan={scan} />
            </section>
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
