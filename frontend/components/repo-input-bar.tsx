'use client';

import { Download, GitBranch, Loader2 } from 'lucide-react';
import { FormEvent, useCallback, useState } from 'react';

import { ImportProgressIndicator } from '@/components/import-progress';
import { type RepositoryScanResult } from '@/lib/api';
import { isGithubUrl } from '@/lib/utils';

interface RepoInputBarProps {
  onScanLoaded: (scan: RepositoryScanResult | null) => void;
  onImportId?: (id: string) => void;
  onRepositoryPath?: (path: string) => void;
}

export function RepoInputBar({ onScanLoaded, onImportId, onRepositoryPath }: RepoInputBarProps) {
  const [value, setValue] = useState('');
  const [status, setStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [importingSource, setImportingSource] = useState('');
  const [importingSourceType, setImportingSourceType] = useState<'github' | 'local'>('local');

  async function handleLoad(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const source = value.trim();
    if (!source || isLoading) return;

    setIsLoading(true);
    setImportingSource(source);
    setImportingSourceType(isGithubUrl(source) ? 'github' : 'local');
    setStatus('Importing repository...');
  }

  const handleImportCompleted = useCallback(
    (result: {
      import_id: string;
      repository_path: string;
      file_count: number;
      languages: string[];
    }) => {
      setStatus(`${result.file_count} files indexed from ${result.languages.join(', ')}`);
      onImportId?.(result.import_id);
      onRepositoryPath?.(result.repository_path);
      onScanLoaded({
        repository_path: result.repository_path,
        files: [],
        directories: [],
        extensions: [],
        languages: result.languages,
      });
      setIsLoading(false);
      setImportingSource('');
    },
    [onScanLoaded, onImportId, onRepositoryPath],
  );

  const handleImportError = useCallback(
    (message: string) => {
      setStatus(message);
      setIsLoading(false);
      setImportingSource('');
      onScanLoaded(null);
    },
    [onScanLoaded],
  );

  return (
    <div className="space-y-3">
      <form className="flex gap-2" onSubmit={handleLoad}>
        <div className="relative flex-1">
          <GitBranch className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="GitHub URL or local path  —  e.g. https://github.com/user/repo or /Users/you/project"
            disabled={isLoading}
            className="h-10 w-full rounded-md border border-border bg-card pl-9 pr-3 text-sm outline-none focus:border-accent disabled:opacity-50"
          />
        </div>
        <button
          type="submit"
          disabled={isLoading || !value.trim()}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Download className="h-4 w-4" />
          )}
          Load
        </button>
      </form>

      {isLoading && importingSource ? (
        <ImportProgressIndicator
          source={importingSource}
          sourceType={importingSourceType}
          onCompleted={handleImportCompleted}
          onError={handleImportError}
        />
      ) : status ? (
        <p className="truncate px-1 text-xs text-muted-foreground">{status}</p>
      ) : null}
    </div>
  );
}
