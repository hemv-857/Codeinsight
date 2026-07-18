'use client';

import { GitPullRequest, Globe, Loader2, Sparkles } from 'lucide-react';
import { FormEvent, useState } from 'react';

import {
  type OpenSourceContributionResult,
  type RepositoryScanResult,
  analyzeOpenSourceContribution,
  analyzeImportedOpenSourceContribution,
} from '@/lib/api';

interface OpenSourceContributorPanelProps {
  scan: RepositoryScanResult | null;
}

const CATEGORY_LABELS: Record<string, string> = {
  bug: 'Bug',
  security: 'Security',
  code_smell: 'Code Smell',
  missing_test: 'Missing Test',
  missing_docs: 'Missing Docs',
  performance: 'Performance',
  accessibility: 'Accessibility',
  api_design: 'API Design',
};

const CATEGORY_COLORS: Record<string, string> = {
  bug: 'bg-red-500/10 text-red-400 border-red-500/20',
  security: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  code_smell: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  missing_test: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  missing_docs: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  performance: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  accessibility: 'bg-green-500/10 text-green-400 border-green-500/20',
  api_design: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-500/20 text-red-300',
  high: 'bg-orange-500/20 text-orange-300',
  medium: 'bg-yellow-500/20 text-yellow-300',
  low: 'bg-blue-500/20 text-blue-300',
};

export function OpenSourceContributorPanel({ scan }: OpenSourceContributorPanelProps) {
  const [repositoryPath, setRepositoryPath] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  const [importId, setImportId] = useState('');
  const [result, setResult] = useState<OpenSourceContributionResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activePath = repositoryPath.trim() || scan?.repository_path || '';

  async function runAnalysis(source: 'path' | 'import' | 'github') {
    setIsLoading(true);
    setError(null);
    try {
      let data: OpenSourceContributionResult;
      if (source === 'github') {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8002'}/api/repositories/open-source-contribution`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ github_url: githubUrl.trim(), focus: null }),
          },
        );
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.detail || 'GitHub analysis failed');
        }
        data = (await response.json()) as OpenSourceContributionResult;
      } else if (source === 'path') {
        data = await analyzeOpenSourceContribution(activePath);
      } else {
        data = await analyzeImportedOpenSourceContribution(importId.trim());
      }
      setResult(data);
      if (data.repository_path) setRepositoryPath(data.repository_path);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsLoading(false);
    }
  }

  function submitPath(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (activePath) void runAnalysis('path');
  }

  function submitGithub(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (githubUrl.trim()) void runAnalysis('github');
  }

  function submitImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (importId.trim()) void runAnalysis('import');
  }

  return (
    <section className="space-y-4">
      <div className="space-y-3">
        <form onSubmit={submitGithub} className="flex gap-2">
          <input
            type="url"
            value={githubUrl}
            onChange={(e) => setGithubUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
            className="flex-1 rounded-md border border-border bg-muted px-3 py-2 text-sm placeholder:text-muted-foreground"
          />
          <button
            type="submit"
            disabled={isLoading || !githubUrl.trim()}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Globe className="h-4 w-4" />
            )}
            Analyze GitHub Repo
          </button>
        </form>

        <div className="flex gap-2">
          <form onSubmit={submitPath} className="flex flex-1 gap-2">
            <input
              type="text"
              value={repositoryPath}
              onChange={(e) => setRepositoryPath(e.target.value)}
              placeholder="/path/to/repository"
              className="flex-1 rounded-md border border-border bg-muted px-3 py-2 text-sm placeholder:text-muted-foreground"
            />
            <button
              type="submit"
              disabled={isLoading || !activePath}
              className="inline-flex items-center gap-2 rounded-md border border-border bg-card px-4 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Local
            </button>
          </form>
          <form onSubmit={submitImport} className="flex gap-2">
            <input
              type="text"
              value={importId}
              onChange={(e) => setImportId(e.target.value)}
              placeholder="Import ID"
              className="w-32 rounded-md border border-border bg-muted px-3 py-2 text-sm placeholder:text-muted-foreground"
            />
            <button
              type="submit"
              disabled={isLoading || !importId.trim()}
              className="inline-flex items-center gap-2 rounded-md border border-border bg-card px-4 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <GitPullRequest className="h-4 w-4" />
              )}
              Import
            </button>
          </form>
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="grid gap-3 md:grid-cols-4">
            <StatCard
              label="Contribution Score"
              value={`${result.stats.contribution_score}/100`}
              accent
            />
            <StatCard label="Total Findings" value={String(result.stats.finding_count)} />
            <StatCard
              label="Files Scanned"
              value={`${result.stats.scanned_file_count}/${result.stats.file_count}`}
            />
            <StatCard label="Confidence" value={`${Math.round(result.stats.confidence * 100)}%`} />
          </div>

          <div className="grid gap-3 md:grid-cols-4">
            <MiniStat label="Bugs" count={result.stats.bug_count} color="text-red-400" />
            <MiniStat
              label="Security"
              count={result.stats.security_count}
              color="text-orange-400"
            />
            <MiniStat
              label="Code Smells"
              count={result.stats.code_smell_count}
              color="text-yellow-400"
            />
            <MiniStat
              label="Performance"
              count={result.stats.performance_count}
              color="text-cyan-400"
            />
          </div>

          <div className="space-y-2">
            <h3 className="text-sm font-medium text-muted-foreground">Recommendations</h3>
            {result.recommendations.map((rec, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                <span>{rec}</span>
              </div>
            ))}
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-medium text-muted-foreground">
              Findings ({result.findings.length})
            </h3>
            {result.findings.map((finding, i) => (
              <FindingCard key={i} finding={finding} />
            ))}
            {result.findings.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No findings — great contribution readiness!
              </p>
            )}
          </div>
        </div>
      )}

      {!result && !error && !isLoading && (
        <div className="rounded-lg border border-dashed border-border p-8 text-center">
          <Sparkles className="mx-auto h-8 w-8 text-muted-foreground" />
          <p className="mt-3 text-sm text-muted-foreground">
            Analyze a repository to find contribution opportunities — bugs, security issues, code
            smells, and more.
          </p>
        </div>
      )}
    </section>
  );
}

function StatCard({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className={`rounded-lg border border-border p-4 ${accent ? 'bg-accent/10' : 'bg-card'}`}>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${accent ? 'text-accent' : ''}`}>{value}</p>
    </div>
  );
}

function MiniStat({ label, count, color }: { label: string; count: number; color: string }) {
  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`mt-1 text-lg font-semibold ${color}`}>{count}</p>
    </div>
  );
}

function FindingCard({ finding }: { finding: OpenSourceContributionResult['findings'][number] }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-2">
      <div className="flex items-center gap-2 flex-wrap">
        <span
          className={`rounded-md border px-2 py-0.5 text-xs font-medium ${CATEGORY_COLORS[finding.category] || 'bg-muted text-muted-foreground'}`}
        >
          {CATEGORY_LABELS[finding.category] || finding.category}
        </span>
        <span
          className={`rounded-md px-2 py-0.5 text-xs font-medium ${SEVERITY_COLORS[finding.severity] || 'bg-muted text-muted-foreground'}`}
        >
          {finding.severity}
        </span>
        <span className="text-xs text-muted-foreground">
          {finding.path}:{finding.line}
        </span>
      </div>
      <p className="text-sm font-medium">{finding.title}</p>
      <p className="text-sm text-muted-foreground">{finding.description}</p>
      {finding.evidence.length > 0 && finding.evidence[0] && (
        <pre className="overflow-x-auto rounded-md bg-muted p-2 text-xs text-muted-foreground">
          {finding.evidence[0]}
        </pre>
      )}
      <div className="rounded-md bg-accent/5 border border-accent/10 p-2">
        <p className="text-xs font-medium text-accent">Suggested Fix</p>
        <p className="mt-1 text-sm">{finding.suggested_fix}</p>
      </div>
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span>Impact: {finding.impact}</span>
        <span>Effort: {finding.effort}</span>
      </div>
    </div>
  );
}
