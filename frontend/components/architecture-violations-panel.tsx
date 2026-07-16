'use client';

import { AlertTriangle, GitBranch, Loader2, ShieldAlert } from 'lucide-react';
import { FormEvent, useState } from 'react';

import {
  type ArchitectureViolation,
  type ArchitectureViolationReport,
  type ArchitectureViolationSeverity,
  type RepositoryScanResult,
  detectArchitectureViolations,
  detectImportedArchitectureViolations,
} from '@/lib/api';

interface ArchitectureViolationsPanelProps {
  scan: RepositoryScanResult | null;
}

const severityClass: Record<ArchitectureViolationSeverity, string> = {
  critical: 'text-red-200',
  high: 'text-red-100',
  medium: 'text-yellow-100',
  low: 'text-muted-foreground',
};

export function ArchitectureViolationsPanel({ scan }: ArchitectureViolationsPanelProps) {
  const [repositoryPath, setRepositoryPath] = useState('');
  const [importId, setImportId] = useState('');
  const [report, setReport] = useState<ArchitectureViolationReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activePath = repositoryPath.trim() || scan?.repository_path || '';

  async function detect(source: 'path' | 'import') {
    setIsLoading(true);
    setError(null);
    try {
      const result =
        source === 'path'
          ? await detectArchitectureViolations(activePath)
          : await detectImportedArchitectureViolations(importId.trim());
      setReport(result);
      setRepositoryPath(result.repository_path);
    } catch (detectError) {
      setReport(null);
      setError(
        detectError instanceof Error
          ? detectError.message
          : 'Architecture violation detection failed',
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
          <label className="sr-only" htmlFor="architecture-violations-repository-path">
            Repository path
          </label>
          <input
            id="architecture-violations-repository-path"
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
              <ShieldAlert className="h-4 w-4" />
            )}
            Detect
          </button>
        </form>

        <form className="flex min-w-0 flex-1 gap-2" onSubmit={submitImport}>
          <label className="sr-only" htmlFor="architecture-violations-import-id">
            Import ID
          </label>
          <input
            id="architecture-violations-import-id"
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
              <AlertTriangle className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">Violations</h3>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <Stat label="Total" value={report.stats.violation_count} />
              <Stat label="Deps" value={report.stats.dependency_count} />
              <Stat label="Critical" value={report.stats.critical_count} />
              <Stat label="High" value={report.stats.high_count} />
            </div>
          </aside>
          <div className="max-h-[420px] overflow-auto rounded-lg border border-border bg-card">
            {report.violations.length ? (
              report.violations.map((violation, index) => (
                <ViolationCard
                  key={`${violation.rule_id}-${violation.source}-${index}`}
                  violation={violation}
                />
              ))
            ) : (
              <div className="p-6 text-center text-sm text-muted-foreground">
                No architecture violations detected.
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-card p-6 text-center text-sm text-muted-foreground">
          Detect layer boundary violations from repository import edges.
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

function ViolationCard({ violation }: { violation: ArchitectureViolation }) {
  return (
    <article className="space-y-2 border-b border-border p-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <p className="text-sm font-medium">{violation.title}</p>
          <p className="mt-1 break-words text-sm text-muted-foreground">
            {violation.source} imports {violation.target}
          </p>
        </div>
        <p className={`text-xs uppercase ${severityClass[violation.severity]}`}>
          {violation.severity}
        </p>
      </div>
      <p className="text-sm text-muted-foreground">{violation.description}</p>
      <p className="break-words text-xs text-muted-foreground">
        {violation.rule_id} via {violation.import_name} - {Math.round(violation.confidence * 100)}%
      </p>
      {violation.evidence.length ? (
        <p className="break-words text-xs text-muted-foreground">
          Evidence: {violation.evidence.join(' -> ')}
        </p>
      ) : null}
    </article>
  );
}
