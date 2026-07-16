'use client';

import { Bug, GitBranch, Loader2, ShieldAlert } from 'lucide-react';
import { FormEvent, useState } from 'react';

import {
  type BugImpactPrediction,
  type ImpactedFile,
  type RepositoryScanResult,
  predictBugImpact,
  predictImportedBugImpact,
} from '@/lib/api';

interface BugImpactPanelProps {
  scan: RepositoryScanResult | null;
}

const sampleTrace = `Traceback (most recent call last):
  File "app/services/payment.py", line 42, in charge
    gateway.charge(card)
PaymentError: card declined`;

export function BugImpactPanel({ scan }: BugImpactPanelProps) {
  const [repositoryPath, setRepositoryPath] = useState('');
  const [importId, setImportId] = useState('');
  const [stackTrace, setStackTrace] = useState(sampleTrace);
  const [changedFiles, setChangedFiles] = useState('');
  const [prediction, setPrediction] = useState<BugImpactPrediction | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activePath = repositoryPath.trim() || scan?.repository_path || '';

  async function predict(source: 'path' | 'import') {
    setIsLoading(true);
    setError(null);
    try {
      const files = changedFiles
        .split('\n')
        .map((item) => item.trim())
        .filter(Boolean);
      const result =
        source === 'path'
          ? await predictBugImpact(activePath, stackTrace, files)
          : await predictImportedBugImpact(importId.trim(), stackTrace, files);
      setPrediction(result);
      setRepositoryPath(result.repository_path);
    } catch (predictError) {
      setPrediction(null);
      setError(
        predictError instanceof Error ? predictError.message : 'Bug impact prediction failed',
      );
    } finally {
      setIsLoading(false);
    }
  }

  function submitPath(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (activePath && stackTrace.trim()) {
      void predict('path');
    }
  }

  function submitImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (importId.trim() && stackTrace.trim()) {
      void predict('import');
    }
  }

  return (
    <section className="space-y-4">
      <div className="grid gap-3 lg:grid-cols-2">
        <form className="space-y-3" onSubmit={submitPath}>
          <label className="sr-only" htmlFor="bug-impact-repository-path">
            Repository path
          </label>
          <div className="flex gap-2">
            <input
              id="bug-impact-repository-path"
              value={repositoryPath}
              onChange={(event) => setRepositoryPath(event.target.value)}
              placeholder={scan?.repository_path ?? '/path/to/repository'}
              className="h-10 min-w-0 flex-1 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent"
            />
            <button
              type="submit"
              disabled={isLoading || !activePath || !stackTrace.trim()}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Bug className="h-4 w-4" />
              )}
              Predict
            </button>
          </div>
        </form>
        <form className="flex gap-2" onSubmit={submitImport}>
          <label className="sr-only" htmlFor="bug-impact-import-id">
            Import ID
          </label>
          <input
            id="bug-impact-import-id"
            value={importId}
            onChange={(event) => setImportId(event.target.value)}
            placeholder="import id"
            className="h-10 min-w-0 flex-1 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent"
          />
          <button
            type="submit"
            disabled={isLoading || !importId.trim() || !stackTrace.trim()}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-border bg-muted px-4 text-sm font-medium text-foreground transition-colors hover:bg-muted/80 disabled:pointer-events-none disabled:opacity-50"
          >
            <GitBranch className="h-4 w-4" />
            Load
          </button>
        </form>
      </div>

      <div className="grid gap-3 lg:grid-cols-[1fr_280px]">
        <textarea
          value={stackTrace}
          onChange={(event) => setStackTrace(event.target.value)}
          rows={7}
          className="min-h-36 w-full resize-y rounded-md border border-border bg-card px-3 py-3 font-mono text-sm outline-none focus:border-accent"
        />
        <textarea
          value={changedFiles}
          onChange={(event) => setChangedFiles(event.target.value)}
          rows={7}
          placeholder="changed files"
          className="min-h-36 w-full resize-y rounded-md border border-border bg-card px-3 py-3 font-mono text-sm outline-none focus:border-accent"
        />
      </div>

      {error ? (
        <div className="rounded-md border border-red-400/30 bg-red-950/30 px-3 py-2 text-sm text-red-100">
          {error}
        </div>
      ) : null}

      {prediction ? (
        <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
          <aside className="space-y-3 rounded-lg border border-border bg-card p-4">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">Impact</h3>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <Stat label="Risk" value={prediction.stats.risk_score} />
              <Stat label="Files" value={prediction.stats.impacted_file_count} />
              <Stat label="Frames" value={prediction.stats.matched_frame_count} />
              <Stat label="Conf" value={Math.round(prediction.stats.confidence * 100)} />
            </div>
            {prediction.root_cause ? (
              <div className="rounded-md bg-muted p-3 text-sm">
                <p className="text-xs uppercase text-muted-foreground">Root Cause</p>
                <p className="mt-1 break-words font-medium">
                  {prediction.root_cause.path}
                  {prediction.root_cause.line ? `:${prediction.root_cause.line}` : ''}
                </p>
              </div>
            ) : null}
          </aside>
          <div className="max-h-[420px] overflow-auto rounded-lg border border-border bg-card">
            {prediction.impacted_files.map((file) => (
              <ImpactedFileCard key={`${file.path}-${file.reason}`} file={file} />
            ))}
            {prediction.recommendations.length ? (
              <div className="space-y-2 border-t border-border p-4">
                {prediction.recommendations.map((item) => (
                  <p key={item} className="text-sm text-muted-foreground">
                    {item}
                  </p>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-card p-6 text-center text-sm text-muted-foreground">
          Predict likely root cause and affected files from a stack trace and repository graph.
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

function ImpactedFileCard({ file }: { file: ImpactedFile }) {
  return (
    <article className="space-y-2 border-b border-border p-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <p className="break-words text-sm font-medium">{file.path}</p>
        <p className="text-xs uppercase text-accent">{Math.round(file.score * 100)}%</p>
      </div>
      <p className="text-sm text-muted-foreground">{file.reason}</p>
    </article>
  );
}
