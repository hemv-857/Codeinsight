'use client';

import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';

import type { RepositoryScanResult } from '@/lib/api';

interface RepoContextValue {
  repositoryPath: string;
  importId: string;
  scan: RepositoryScanResult | null;
  pipelineResults: Record<string, unknown>;
  setRepositoryPath: (path: string) => void;
  setImportId: (id: string) => void;
  setScan: (scan: RepositoryScanResult | null) => void;
  setPipelineResult: (stepId: string, data: unknown) => void;
  isLoaded: boolean;
}

const RepoContext = createContext<RepoContextValue | null>(null);

export function RepoProvider({ children }: { children: ReactNode }) {
  const [repositoryPath, setRepositoryPath] = useState('');
  const [importId, setImportId] = useState('');
  const [scan, setScan] = useState<RepositoryScanResult | null>(null);
  const [pipelineResults, setPipelineResults] = useState<Record<string, unknown>>({});

  const setPipelineResult = useCallback((stepId: string, data: unknown) => {
    setPipelineResults((prev) => ({ ...prev, [stepId]: data }));
  }, []);

  return (
    <RepoContext.Provider
      value={{
        repositoryPath,
        importId,
        scan,
        pipelineResults,
        setRepositoryPath,
        setImportId,
        setScan,
        setPipelineResult,
        isLoaded: Boolean(scan),
      }}
    >
      {children}
    </RepoContext.Provider>
  );
}

export function useRepo(): RepoContextValue {
  const ctx = useContext(RepoContext);
  if (!ctx) throw new Error('useRepo must be used within RepoProvider');
  return ctx;
}
