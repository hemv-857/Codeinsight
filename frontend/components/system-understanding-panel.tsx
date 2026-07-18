'use client';

import { Brain, Copy, GitBranch, Loader2, Network } from 'lucide-react';
import { FormEvent, useState } from 'react';

import { MermaidDiagram } from '@/components/mermaid-diagram';
import {
  type RepositoryScanResult,
  type SystemUnderstandingReport,
  generateImportedSystemUnderstanding,
  generateSystemUnderstanding,
} from '@/lib/api';

interface SystemUnderstandingPanelProps {
  scan: RepositoryScanResult | null;
}

export function SystemUnderstandingPanel({ scan }: SystemUnderstandingPanelProps) {
  const [repositoryPath, setRepositoryPath] = useState('');
  const [importId, setImportId] = useState('');
  const [report, setReport] = useState<SystemUnderstandingReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const activePath = repositoryPath.trim() || scan?.repository_path || '';

  async function generate(source: 'path' | 'import') {
    setIsLoading(true);
    setError(null);
    try {
      const result =
        source === 'path'
          ? await generateSystemUnderstanding(activePath)
          : await generateImportedSystemUnderstanding(importId.trim());
      setReport(result);
      setRepositoryPath(result.repository_path);
    } catch (generateError) {
      setReport(null);
      setError(
        generateError instanceof Error
          ? generateError.message
          : 'System understanding generation failed',
      );
    } finally {
      setIsLoading(false);
    }
  }

  function submitPath(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (activePath) {
      void generate('path');
    }
  }

  function submitImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (importId.trim()) {
      void generate('import');
    }
  }

  function copyMarkdown() {
    if (report) {
      void navigator.clipboard.writeText(report.markdown).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
    }
  }

  return (
    <section className="space-y-4">
      <div className="grid gap-3 lg:grid-cols-2">
        <form className="space-y-3" onSubmit={submitPath}>
          <label className="sr-only" htmlFor="system-understanding-repository-path">
            Repository path
          </label>
          <div className="flex gap-2">
            <input
              id="system-understanding-repository-path"
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
                <Brain className="h-4 w-4" />
              )}
              Generate System Understanding
            </button>
          </div>
        </form>
        <form className="flex gap-2" onSubmit={submitImport}>
          <label className="sr-only" htmlFor="system-understanding-import-id">
            Import ID
          </label>
          <input
            id="system-understanding-import-id"
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
        <div className="space-y-4">
          <div className="grid gap-3 md:grid-cols-4">
            <Stat label="Files" value={report.stats.file_count} />
            <Stat label="Symbols" value={report.stats.symbol_count} />
            <Stat label="Deps" value={report.stats.dependency_count} />
            <Stat label="Conf" value={Math.round(report.stats.confidence * 100)} />
          </div>

          <div className="grid gap-4 xl:grid-cols-[1fr_340px]">
            <article className="space-y-4 rounded-lg border border-border bg-card p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-xl font-semibold">{report.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {report.application_overview}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={copyMarkdown}
                  className="inline-flex h-9 shrink-0 items-center justify-center gap-2 rounded-md border border-border bg-muted px-3 text-sm font-medium text-foreground transition-colors hover:bg-muted/80"
                >
                  <Copy className="h-4 w-4" />
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>

              <Section title="Architecture Summary" items={[report.architecture_summary]} />
              <Section title="Critical Execution Flows" items={report.critical_execution_flows} />
              <Section title="Database Interactions" items={report.database_interactions} />
              <Section title="Suggested Learning Path" items={report.suggested_learning_path} />

              <div>
                <h4 className="text-sm font-semibold">Main Components</h4>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  {report.main_components.map((component, index) => (
                    <div
                      key={component.path}
                      className="group relative rounded-md border border-border bg-gradient-to-br from-card to-muted/30 p-4 transition-colors hover:border-accent/50"
                    >
                      <div className="flex items-start gap-3">
                        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-accent/30 bg-accent/10 text-xs font-bold text-accent">
                          {index + 1}
                        </span>
                        <div className="min-w-0">
                          <p className="break-words text-sm font-medium">{component.path}</p>
                          <p className="mt-1.5 text-sm leading-6 text-muted-foreground">
                            {component.role}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </article>

            <aside className="space-y-5 rounded-lg border border-border bg-card p-5">
              <div className="flex items-center gap-2">
                <Network className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold">Evidence</h3>
              </div>
              <FileList title="Important Files" files={report.important_files} accent />
              <FileList title="High-Risk Modules" files={report.high_risk_modules} danger />
              <div>
                <p className="text-sm font-medium">Related Symbols</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {report.related_symbols.map((symbol) => (
                    <span
                      key={`${symbol.path}:${symbol.line}:${symbol.name}`}
                      className="inline-flex items-center gap-1.5 rounded-md border border-border bg-muted px-2.5 py-1 text-xs"
                    >
                      <span className="font-medium text-foreground">{symbol.name}</span>
                      <span className="text-muted-foreground">{symbol.path}</span>
                    </span>
                  ))}
                </div>
              </div>
            </aside>
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            <MermaidDiagram title="Architecture Diagram" code={report.architecture_diagram} />
            <MermaidDiagram
              title="Dependency Visualization"
              code={report.dependency_visualization}
            />
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-card p-6 text-center text-sm text-muted-foreground">
          Generate a repository-grounded system report with architecture, flows, evidence, risk, and
          learning path in one click.
        </div>
      )}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-gradient-to-br from-card to-muted/20 p-4 text-center">
      <p className="text-xs uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-bold tabular-nums">{value}</p>
    </div>
  );
}

function Section({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h4 className="text-sm font-semibold">{title}</h4>
      <ul className="mt-2 space-y-1.5">
        {items.map((item) => (
          <li key={item} className="flex items-start gap-2 text-sm leading-6 text-muted-foreground">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function FileList({
  title,
  files,
  accent,
  danger,
}: {
  title: string;
  files: { path: string; reason: string }[];
  accent?: boolean;
  danger?: boolean;
}) {
  return (
    <div>
      <p className="text-sm font-medium">{title}</p>
      <ul className="mt-2 space-y-2">
        {files.map((file) => (
          <li
            key={file.path}
            className={`rounded-md border p-2.5 text-sm ${
              danger
                ? 'border-red-400/20 bg-red-950/20'
                : accent
                  ? 'border-accent/20 bg-accent/5'
                  : 'border-border'
            }`}
          >
            <p className="break-words font-medium">{file.path}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">{file.reason}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
