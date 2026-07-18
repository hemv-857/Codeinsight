'use client';

import { motion } from 'framer-motion';
import { CheckCircle2, Circle, Loader2, Play, XCircle } from 'lucide-react';
import { useState } from 'react';

import { useRepo } from '@/components/repo-context';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8002';

interface PipelineStep {
  id: string;
  label: string;
  endpoint: string;
  importEndpoint: string | null;
  importMethod: 'GET' | 'POST';
}

const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: 'debt',
    label: 'Technical Debt Analysis',
    endpoint: '/api/repositories/technical-debt',
    importEndpoint: '/api/repositories/imports/{id}/technical-debt',
    importMethod: 'GET',
  },
  {
    id: 'circular',
    label: 'Circular Dependencies',
    endpoint: '/api/repositories/circular-dependencies',
    importEndpoint: null,
    importMethod: 'POST',
  },
  {
    id: 'dead-code',
    label: 'Dead Code Detection',
    endpoint: '/api/repositories/dead-code',
    importEndpoint: '/api/repositories/imports/{id}/dead-code',
    importMethod: 'GET',
  },
  {
    id: 'violations',
    label: 'Architecture Violations',
    endpoint: '/api/repositories/architecture-violations',
    importEndpoint: null,
    importMethod: 'POST',
  },
  {
    id: 'knowledge',
    label: 'Knowledge Graph',
    endpoint: '/api/repositories/knowledge-graph',
    importEndpoint: '/api/repositories/imports/{id}/knowledge-graph',
    importMethod: 'GET',
  },
  {
    id: 'summary',
    label: 'Repository Summary',
    endpoint: '/api/repositories/summary',
    importEndpoint: '/api/repositories/imports/{id}/summary',
    importMethod: 'GET',
  },
];

type StepStatus = 'pending' | 'running' | 'completed' | 'failed';

interface StepResult {
  status: StepStatus;
  error?: string;
  data?: Record<string, unknown>;
}

function getResultSummary(stepId: string, data: Record<string, unknown>): string[] {
  const lines: string[] = [];
  if (stepId === 'debt') {
    const stats = data.stats as Record<string, unknown> | undefined;
    if (stats) {
      lines.push(`${stats.finding_count ?? 0} findings (score: ${stats.score ?? '?'})`);
      if (Number(stats.high_count) > 0)
        lines.push(`${stats.high_count} high / ${stats.critical_count ?? 0} critical`);
    }
  } else if (stepId === 'circular') {
    const stats = data.stats as Record<string, unknown> | undefined;
    if (stats)
      lines.push(
        `${stats.cycle_count ?? 0} cycles detected across ${stats.affected_file_count ?? 0} files`,
      );
  } else if (stepId === 'dead-code') {
    const stats = data.stats as Record<string, unknown> | undefined;
    if (stats)
      lines.push(
        `${stats.finding_count ?? 0} dead code items (${stats.unused_file_count ?? 0} files, ${stats.unused_callable_count ?? 0} callables)`,
      );
  } else if (stepId === 'violations') {
    const stats = data.stats as Record<string, unknown> | undefined;
    if (stats)
      lines.push(
        `${stats.violation_count ?? 0} violations (${stats.high_count ?? 0} high, ${stats.medium_count ?? 0} medium)`,
      );
  } else if (stepId === 'knowledge') {
    const stats = data.stats as Record<string, unknown> | undefined;
    if (stats) lines.push(`${stats.node_count ?? 0} nodes, ${stats.edge_count ?? 0} edges`);
  } else if (stepId === 'summary') {
    const stats = data.stats as Record<string, unknown> | undefined;
    if (stats)
      lines.push(
        `${stats.file_count ?? 0} files, ${stats.symbol_count ?? 0} symbols, ${stats.language_count ?? 0} languages`,
      );
    if (data.overview) lines.push(String(data.overview).slice(0, 120) + '...');
  }
  return lines;
}

export function FullAnalysisPipeline() {
  const { scan, importId, repositoryPath, setPipelineResult } = useRepo();
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<Record<string, StepResult>>({});

  const repo = repositoryPath || scan?.repository_path;
  const canRun = Boolean(repo || importId);

  async function runPipeline() {
    if (!canRun || isRunning) return;
    setIsRunning(true);
    setResults({});

    for (const step of PIPELINE_STEPS) {
      setResults((prev) => ({ ...prev, [step.id]: { status: 'running' } }));

      try {
        const useImport = Boolean(importId) && step.importEndpoint;
        const url = useImport
          ? `${API_BASE_URL}${step.importEndpoint?.replace('{id}', importId) ?? step.endpoint}`
          : `${API_BASE_URL}${step.endpoint}`;

        const method = useImport ? step.importMethod : 'POST';

        const fetchOptions: RequestInit = {
          method,
          headers: { 'Content-Type': 'application/json' },
        };

        if (method === 'POST') {
          fetchOptions.body = JSON.stringify({ repository_path: repo });
        }

        const response = await fetch(url, fetchOptions);
        if (!response.ok) throw new Error(`${response.status}`);
        const data = await response.json();

        setResults((prev) => ({ ...prev, [step.id]: { status: 'completed', data } }));
        setPipelineResult(step.id, data);
      } catch (error) {
        setResults((prev) => ({
          ...prev,
          [step.id]: { status: 'failed', error: error instanceof Error ? error.message : 'Failed' },
        }));
      }
    }

    setIsRunning(false);
  }

  const completedCount = Object.values(results).filter((r) => r.status === 'completed').length;
  const failedCount = Object.values(results).filter((r) => r.status === 'failed').length;

  return (
    <div className="rounded-lg border border-border bg-card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold">Full Analysis Pipeline</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Run all analyses in sequence with one click.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void runPipeline()}
          disabled={!canRun || isRunning}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-accent px-5 text-sm font-medium text-accent-foreground transition-colors hover:bg-accent/90 disabled:pointer-events-none disabled:opacity-50"
        >
          {isRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          {isRunning ? 'Running...' : 'Run Full Analysis'}
        </button>
      </div>

      {Object.keys(results).length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span>
              {completedCount}/{PIPELINE_STEPS.length} completed
            </span>
            {failedCount > 0 && <span className="text-red-400">{failedCount} failed</span>}
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-muted">
            <motion.div
              className="h-full rounded-full bg-accent"
              initial={{ width: 0 }}
              animate={{ width: `${(completedCount / PIPELINE_STEPS.length) * 100}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            {PIPELINE_STEPS.map((step) => {
              const result = results[step.id];
              const status = result?.status ?? 'pending';
              const summaryLines = result?.data ? getResultSummary(step.id, result.data) : [];
              return (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, x: -4 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`rounded-md border p-3 text-sm ${
                    status === 'completed'
                      ? 'border-green-500/30 bg-green-950/20'
                      : status === 'failed'
                        ? 'border-red-500/30 bg-red-950/20'
                        : status === 'running'
                          ? 'border-accent/30 bg-accent/5'
                          : 'border-border bg-muted/30'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {status === 'completed' && (
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-green-400" />
                    )}
                    {status === 'running' && (
                      <Loader2 className="h-4 w-4 shrink-0 animate-spin text-accent" />
                    )}
                    {status === 'failed' && <XCircle className="h-4 w-4 shrink-0 text-red-400" />}
                    {status === 'pending' && (
                      <Circle className="h-4 w-4 shrink-0 text-muted-foreground" />
                    )}
                    <span className="font-medium">{step.label}</span>
                  </div>
                  {status === 'failed' && result?.error && (
                    <p className="mt-1 text-xs text-red-300">{result.error}</p>
                  )}
                  {status === 'completed' && summaryLines.length > 0 && (
                    <div className="mt-1.5 space-y-0.5">
                      {summaryLines.map((line, i) => (
                        <p key={i} className="text-xs text-muted-foreground">
                          {line}
                        </p>
                      ))}
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {!canRun && (
        <p className="text-xs text-muted-foreground">Load a repository above to enable.</p>
      )}
    </div>
  );
}
