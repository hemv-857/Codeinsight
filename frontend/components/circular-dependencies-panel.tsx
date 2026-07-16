'use client';

import { GitBranch, Loader2, RefreshCcw, Repeat2 } from 'lucide-react';
import { FormEvent, useState } from 'react';

import {
  type CircularDependencyCycle,
  type CircularDependencyReport,
  type RepositoryScanResult,
  detectCircularDependencies,
  detectImportedCircularDependencies,
} from '@/lib/api';

interface CircularDependenciesPanelProps {
  scan: RepositoryScanResult | null;
}

export function CircularDependenciesPanel({ scan }: CircularDependenciesPanelProps) {
  const [repositoryPath, setRepositoryPath] = useState('');
  const [importId, setImportId] = useState('');
  const [report, setReport] = useState<CircularDependencyReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activePath = repositoryPath.trim() || scan?.repository_path || '';

  async function detect(source: 'path' | 'import') {
    setIsLoading(true);
    setError(null);
    try {
      const result =
        source === 'path'
          ? await detectCircularDependencies(activePath)
          : await detectImportedCircularDependencies(importId.trim());
      setReport(result);
      setRepositoryPath(result.repository_path);
    } catch (detectError) {
      setReport(null);
      setError(
        detectError instanceof Error ? detectError.message : 'Circular dependency detection failed',
      );
    } finally {
      setIsLoading(false);
    }
  }

  function submitPath(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (activePath) {
      void detect('path');
    }
  }

  function submitImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (importId.trim()) {
      void detect('import');
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row">
        <form className="flex min-w-0 flex-1 gap-2" onSubmit={submitPath}>
          <label className="sr-only" htmlFor="cycle-repository-path">
            Repository path
          </label>
          <input
            id="cycle-repository-path"
            value={repositoryPath}
            onChange={(event) => setRepositoryPath(event.target.value)}
            placeholder={scan?.repository_path ?? '/path/to/repository'}
            className="h-10 min-w-0 flex-1 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent"
          />
          <button
            type="submit"
            disabled={isLoading || !activePath}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCcw className="h-4 w-4" />
            )}
            Detect
          </button>
        </form>

        <form className="flex min-w-0 flex-1 gap-2" onSubmit={submitImport}>
          <label className="sr-only" htmlFor="cycle-import-id">
            Import ID
          </label>
          <input
            id="cycle-import-id"
            value={importId}
            onChange={(event) => setImportId(event.target.value)}
            placeholder="import id"
            className="h-10 min-w-0 flex-1 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent"
          />
          <button
            type="submit"
            disabled={isLoading || !importId.trim()}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-border bg-muted px-4 text-sm font-medium text-foreground transition-colors hover:bg-muted/80 disabled:pointer-events-none disabled:opacity-50"
          >
            <GitBranch className="h-4 w-4" />
            Load
          </button>
        </form>
      </div>

      {error ? (
        <div className="rounded-md border border-red-400/30 bg-red-950/30 px-3 py-2 text-sm text-red-100">
          {error}
        </div>
      ) : null}

      {report ? (
        <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
          <aside className="space-y-3 rounded-lg border border-border bg-card p-4">
            <div className="flex items-center gap-2">
              <Repeat2 className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">Cycle Impact</h3>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <Stat label="Cycles" value={report.stats.cycle_count} />
              <Stat label="Files" value={report.stats.affected_file_count} />
              <Stat label="Max Len" value={report.stats.max_cycle_length} />
              <Stat label="Edges" value={report.stats.internal_dependency_count} />
            </div>
          </aside>
          <div className="max-h-[420px] overflow-auto rounded-lg border border-border bg-card">
            {report.cycles.length ? (
              report.cycles.map((cycle, index) => (
                <CycleCard key={`${cycle.files.join('>')}-${index}`} cycle={cycle} />
              ))
            ) : (
              <div className="p-6 text-center text-sm text-muted-foreground">
                No circular dependencies detected.
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-card p-6 text-center text-sm text-muted-foreground">
          Detect circular file dependencies from parsed imports.
        </div>
      )}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md bg-muted p-3">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 text-xl font-semibold">{value}</p>
    </div>
  );
}

function CycleCard({ cycle }: { cycle: CircularDependencyCycle }) {
  return (
    <article className="space-y-3 border-b border-border p-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-medium">Cycle of {cycle.length} files</p>
          <p className="mt-1 break-words text-sm text-muted-foreground">
            {cycle.files.join(' -> ')}
            {' -> '}
            {cycle.files[0]}
          </p>
        </div>
      </div>
      <div className="space-y-1 rounded-md bg-muted p-3 text-xs text-muted-foreground">
        {cycle.edges.map((edge) => (
          <p key={`${edge.source}-${edge.target}-${edge.import_name}`} className="break-words">
            {edge.source} imports {edge.target} via {edge.import_name}
          </p>
        ))}
      </div>
    </article>
  );
}
