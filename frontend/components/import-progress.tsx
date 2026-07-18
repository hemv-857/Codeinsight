'use client';

import { motion } from 'framer-motion';
import { CheckCircle2, Circle, Download, FileSearch, Loader2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import type { RepositoryScanResult } from '@/lib/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8002';

interface ImportProgressProps {
  source: string;
  sourceType: 'github' | 'local';
  onCompleted: (result: {
    import_id: string;
    repository_path: string;
    file_count: number;
    languages: string[];
  }) => void;
  onError: (message: string) => void;
}

const STAGES = [
  { key: 'validating', label: 'Validating', icon: Circle },
  { key: 'cloning', label: 'Downloading', icon: Download },
  { key: 'scanning', label: 'Scanning', icon: FileSearch },
  { key: 'completed', label: 'Complete', icon: CheckCircle2 },
] as const;

export function ImportProgressIndicator({
  source,
  sourceType,
  onCompleted,
  onError,
}: ImportProgressProps) {
  const [stage, setStage] = useState<'validating' | 'cloning' | 'scanning' | 'completed'>(
    'validating',
  );
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setElapsed(0);
    setStage('validating');

    timerRef.current = setInterval(() => {
      setElapsed((prev) => prev + 0.1);
    }, 100);

    abortRef.current = new AbortController();

    const runImport = async () => {
      try {
        setStage('cloning');
        const importResponse = await fetch(`${API_BASE_URL}/api/repositories/import`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source_type: sourceType, source }),
          signal: abortRef.current?.signal,
        });
        if (!importResponse.ok) {
          const body = await importResponse.json().catch(() => ({}));
          throw new Error(body.detail ?? `Import failed (${importResponse.status})`);
        }
        const importResult = await importResponse.json();

        setStage('scanning');
        const scanResponse = await fetch(
          `${API_BASE_URL}/api/repositories/imports/${importResult.import_id}/scan`,
          { signal: abortRef.current?.signal },
        );
        if (!scanResponse.ok) throw new Error(`Scan failed (${scanResponse.status})`);
        const scanResult: RepositoryScanResult = await scanResponse.json();

        setStage('completed');
        if (timerRef.current) clearInterval(timerRef.current);
        onCompleted({
          import_id: importResult.import_id,
          repository_path: scanResult.repository_path,
          file_count: scanResult.files.length,
          languages: scanResult.languages,
        });
      } catch (error) {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        if (timerRef.current) clearInterval(timerRef.current);
        onError(error instanceof Error ? error.message : 'Import failed');
      }
    };

    void runImport();

    return () => {
      abortRef.current?.abort();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [source, sourceType, onCompleted, onError]);

  const currentStageIndex = STAGES.findIndex((s) => s.key === stage);

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${Math.floor(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin text-accent" />
          <span className="text-sm font-medium">Importing Repository</span>
        </div>
        <span className="text-xs text-muted-foreground font-mono">{formatTime(elapsed)}</span>
      </div>

      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
        <motion.div
          className="h-full rounded-full bg-accent"
          initial={{ width: 0 }}
          animate={{
            width:
              stage === 'completed'
                ? '100%'
                : `${Math.min(((currentStageIndex + 1) / STAGES.length) * 100, 95)}%`,
          }}
          transition={{ duration: 0.5, ease: 'easeInOut' }}
        />
      </div>

      <div className="grid grid-cols-4 gap-2">
        {STAGES.map((s, idx) => {
          const isCompleted = idx < currentStageIndex || stage === 'completed';
          const isCurrent = idx === currentStageIndex && stage !== 'completed';
          const StageIcon = s.icon;

          return (
            <div key={s.key} className="flex flex-col items-center gap-1">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full border ${
                  isCompleted
                    ? 'border-green-500/30 bg-green-500/10'
                    : isCurrent
                      ? 'border-accent/30 bg-accent/10'
                      : 'border-border bg-muted'
                }`}
              >
                {isCompleted ? (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                ) : isCurrent ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                  >
                    <StageIcon className="h-4 w-4 text-accent" />
                  </motion.div>
                ) : (
                  <StageIcon className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
              <span
                className={`text-[10px] ${isCurrent ? 'text-accent font-medium' : 'text-muted-foreground'}`}
              >
                {s.label}
              </span>
            </div>
          );
        })}
      </div>

      <motion.p
        key={stage}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-xs text-muted-foreground text-center"
      >
        {stage === 'validating' && 'Verifying repository source...'}
        {stage === 'cloning' && 'Downloading repository (this may take a while for large repos)...'}
        {stage === 'scanning' && 'Scanning files and detecting languages...'}
        {stage === 'completed' && 'Repository ready!'}
      </motion.p>
    </div>
  );
}
