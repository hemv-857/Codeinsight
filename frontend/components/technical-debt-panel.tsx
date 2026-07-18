'use client';

import { AlertTriangle, GitBranch, Loader2, ShieldCheck } from 'lucide-react';
import { FormEvent, useEffect, useState } from 'react';

import { useRepo } from '@/components/repo-context';
import {
  type DebtSeverity,
  type RepositoryScanResult,
  type TechnicalDebtFinding,
  type TechnicalDebtReport,
  analyzeImportedTechnicalDebt,
  analyzeTechnicalDebt,
} from '@/lib/api';

interface TechnicalDebtPanelProps {
  scan: RepositoryScanResult | null;
}

const severityClass: Record<DebtSeverity, string> = {
  critical: 'text-red-200',
  high: 'text-red-100',
  medium: 'text-yellow-100',
  low: 'text-muted-foreground',
};

export function TechnicalDebtPanel({ scan }: TechnicalDebtPanelProps) {
  const { pipelineResults } = useRepo();
  const [repositoryPath, setRepositoryPath] = useState('');
  const [importId, setImportId] = useState('');
  const [report, setReport] = useState<TechnicalDebtReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const data = pipelineResults.debt as TechnicalDebtReport | undefined;
    if (data && !report) setReport(data);
  }, [pipelineResults, report]);

  const activePath = repositoryPath.trim() || scan?.repository_path || '';

  async function analyze(source: 'path' | 'import') {
    setIsLoading(true);
    setError(null);
    try {
      const result =
        source === 'path'
          ? await analyzeTechnicalDebt(activePath)
          : await analyzeImportedTechnicalDebt(importId.trim());
      setReport(result);
      setRepositoryPath(result.repository_path);
    } catch (analysisError) {
      setReport(null);
      setError(
        analysisError instanceof Error ? analysisError.message : 'Technical debt analysis failed',
      );
    } finally {
      setIsLoading(false);
    }
  }

  function submitPath(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (activePath) {
      void analyze('path');
    }
  }

  function submitImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (importId.trim()) {
      void analyze('import');
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row">
        <form className="flex min-w-0 flex-1 gap-2" onSubmit={submitPath}>
          <label className="sr-only" htmlFor="debt-repository-path">
            Repository path
          </label>
          <input
            id="debt-repository-path"
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
              <ShieldCheck className="h-4 w-4" />
            )}
            Analyze
          </button>
        </form>

        <form className="flex min-w-0 flex-1 gap-2" onSubmit={submitImport}>
          <label className="sr-only" htmlFor="debt-import-id">
            Import ID
          </label>
          <input
            id="debt-import-id"
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
            <div>
              <p className="text-sm text-muted-foreground">Architecture Health</p>
              <p className="mt-2 text-4xl font-semibold">{report.stats.score}</p>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <Stat label="Findings" value={report.stats.finding_count} />
              <Stat label="Parsed" value={report.stats.parsed_file_count} />
              <Stat label="Avg Cx" value={report.stats.average_complexity} />
              <Stat label="Max Cx" value={report.stats.max_complexity} />
              <Stat label="Complex" value={report.stats.complex_symbol_count} />
              <Stat label="High" value={report.stats.high_count} />
            </div>
          </aside>
          <div className="max-h-[520px] overflow-auto rounded-lg border border-border bg-card">
            {report.findings.length ? (
              report.findings.map((finding, index) => (
                <FindingCard
                  key={`${finding.path}-${finding.category}-${index}`}
                  finding={finding}
                />
              ))
            ) : (
              <div className="p-6 text-center text-sm text-muted-foreground">
                No technical debt findings from current analyzer rules.
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-card p-6 text-center text-sm text-muted-foreground">
          Analyze a repository to surface maintainability risks from parsed code and dependencies.
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

function FindingCard({ finding }: { finding: TechnicalDebtFinding }) {
  return (
    <article className="space-y-2 border-b border-border p-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-primary" />
            <p className="text-sm font-medium">{finding.title}</p>
          </div>
          <p className="mt-1 break-words text-sm text-muted-foreground">
            {finding.path}
            {finding.line ? `:${finding.line}` : ''}
            {finding.symbol_name ? ` / ${finding.symbol_name}` : ''}
          </p>
        </div>
        <p className={`text-xs uppercase ${severityClass[finding.severity]}`}>{finding.severity}</p>
      </div>
      <p className="text-sm text-muted-foreground">{finding.description}</p>
      {finding.evidence.length ? (
        <p className="break-words text-xs text-muted-foreground">
          Evidence: {finding.evidence.join(' -> ')}
        </p>
      ) : null}
    </article>
  );
}
