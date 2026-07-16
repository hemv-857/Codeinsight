'use client';

import { FileCheck2, GitBranch, Loader2, ShieldAlert } from 'lucide-react';
import { FormEvent, useState } from 'react';

import {
  type PullRequestFinding,
  type PullRequestReview,
  type RepositoryScanResult,
  reviewImportedPullRequest,
  reviewPullRequest,
} from '@/lib/api';

interface PullRequestReviewPanelProps {
  scan: RepositoryScanResult | null;
}

export function PullRequestReviewPanel({ scan }: PullRequestReviewPanelProps) {
  const [repositoryPath, setRepositoryPath] = useState('');
  const [importId, setImportId] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [changedFiles, setChangedFiles] = useState('');
  const [diffText, setDiffText] = useState('');
  const [review, setReview] = useState<PullRequestReview | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activePath = repositoryPath.trim() || scan?.repository_path || '';

  async function runReview(source: 'path' | 'import') {
    setIsLoading(true);
    setError(null);
    try {
      const files = changedFiles
        .split('\n')
        .map((item) => item.trim())
        .filter(Boolean);
      const result =
        source === 'path'
          ? await reviewPullRequest(
              activePath,
              files,
              title.trim() || undefined,
              description.trim() || undefined,
              diffText.trim() || undefined,
            )
          : await reviewImportedPullRequest(
              importId.trim(),
              files,
              title.trim() || undefined,
              description.trim() || undefined,
              diffText.trim() || undefined,
            );
      setReview(result);
      setRepositoryPath(result.repository_path);
    } catch (reviewError) {
      setReview(null);
      setError(reviewError instanceof Error ? reviewError.message : 'Pull request review failed');
    } finally {
      setIsLoading(false);
    }
  }

  function submitPath(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (activePath && changedFiles.trim()) {
      void runReview('path');
    }
  }

  function submitImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (importId.trim() && changedFiles.trim()) {
      void runReview('import');
    }
  }

  return (
    <section className="space-y-4">
      <div className="grid gap-3 lg:grid-cols-2">
        <form className="space-y-3" onSubmit={submitPath}>
          <label className="sr-only" htmlFor="pr-review-repository-path">
            Repository path
          </label>
          <div className="flex gap-2">
            <input
              id="pr-review-repository-path"
              value={repositoryPath}
              onChange={(event) => setRepositoryPath(event.target.value)}
              placeholder={scan?.repository_path ?? '/path/to/repository'}
              className="h-10 min-w-0 flex-1 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent"
            />
            <button
              type="submit"
              disabled={isLoading || !activePath || !changedFiles.trim()}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileCheck2 className="h-4 w-4" />
              )}
              Review
            </button>
          </div>
        </form>
        <form className="flex gap-2" onSubmit={submitImport}>
          <label className="sr-only" htmlFor="pr-review-import-id">
            Import ID
          </label>
          <input
            id="pr-review-import-id"
            value={importId}
            onChange={(event) => setImportId(event.target.value)}
            placeholder="import id"
            className="h-10 min-w-0 flex-1 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent"
          />
          <button
            type="submit"
            disabled={isLoading || !importId.trim() || !changedFiles.trim()}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-border bg-muted px-4 text-sm font-medium text-foreground transition-colors hover:bg-muted/80 disabled:pointer-events-none disabled:opacity-50"
          >
            <GitBranch className="h-4 w-4" />
            Load
          </button>
        </form>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="PR title"
          className="h-10 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent"
        />
        <input
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="PR description"
          className="h-10 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent"
        />
      </div>
      <div className="grid gap-3 lg:grid-cols-[280px_1fr]">
        <textarea
          value={changedFiles}
          onChange={(event) => setChangedFiles(event.target.value)}
          rows={8}
          placeholder="changed files, one per line"
          className="min-h-40 resize-y rounded-md border border-border bg-card px-3 py-3 font-mono text-sm outline-none focus:border-accent"
        />
        <textarea
          value={diffText}
          onChange={(event) => setDiffText(event.target.value)}
          rows={8}
          placeholder="optional unified diff"
          className="min-h-40 resize-y rounded-md border border-border bg-card px-3 py-3 font-mono text-sm outline-none focus:border-accent"
        />
      </div>

      {error ? (
        <div className="rounded-md border border-red-400/30 bg-red-950/30 px-3 py-2 text-sm text-red-100">
          {error}
        </div>
      ) : null}

      {review ? (
        <div className="grid gap-4 xl:grid-cols-[280px_1fr]">
          <aside className="space-y-3 rounded-lg border border-border bg-card p-4">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">Review</h3>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <Stat label="Risk" value={review.stats.risk_score} />
              <Stat label="Files" value={review.stats.changed_file_count} />
              <Stat label="Impact" value={review.stats.impacted_file_count} />
              <Stat label="Findings" value={review.stats.finding_count} />
            </div>
            <div className="rounded-md bg-muted p-3 text-sm">
              <p className="text-xs uppercase text-muted-foreground">Level</p>
              <p className="mt-1 font-medium uppercase">{review.stats.risk_level}</p>
            </div>
            <p className="text-sm text-muted-foreground">{review.summary}</p>
          </aside>
          <div className="max-h-[520px] overflow-auto rounded-lg border border-border bg-card">
            <div className="space-y-2 p-4">
              {review.findings.map((finding) => (
                <FindingCard
                  key={`${finding.category}-${finding.path ?? finding.title}`}
                  finding={finding}
                />
              ))}
              {review.findings.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No findings for the supplied changes.
                </p>
              ) : null}
            </div>
            <div className="space-y-2 border-t border-border p-4">
              {review.recommendations.map((item) => (
                <p key={item} className="text-sm text-muted-foreground">
                  {item}
                </p>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-card p-6 text-center text-sm text-muted-foreground">
          Review a proposed pull request with repository graph, debt, and impact signals.
        </div>
      )}
    </section>
  );
}

function FindingCard({ finding }: { finding: PullRequestFinding }) {
  return (
    <article className="rounded-md bg-muted p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{finding.title}</p>
          <p className="mt-1 text-xs uppercase text-accent">{finding.severity}</p>
        </div>
        {finding.path ? (
          <p className="max-w-52 truncate text-xs text-muted-foreground">{finding.path}</p>
        ) : null}
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{finding.description}</p>
    </article>
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
