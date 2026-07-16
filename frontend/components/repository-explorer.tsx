'use client';

import { ChevronRight, FileCode2, FolderTree, GitBranch, Loader2, Search } from 'lucide-react';
import { FormEvent, useMemo, useState } from 'react';

import {
  type RepositoryFileEntry,
  type RepositoryScanResult,
  scanImportedRepository,
  scanRepository,
} from '@/lib/api';

interface RepositoryExplorerProps {
  onScanLoaded: (scan: RepositoryScanResult | null) => void;
}

interface TreeNode {
  name: string;
  path: string;
  files: RepositoryFileEntry[];
  children: Map<string, TreeNode>;
}

export function RepositoryExplorer({ onScanLoaded }: RepositoryExplorerProps) {
  const [repositoryPath, setRepositoryPath] = useState('');
  const [importId, setImportId] = useState('');
  const [scan, setScan] = useState<RepositoryScanResult | null>(null);
  const [query, setQuery] = useState('');
  const [language, setLanguage] = useState('all');
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedFile = scan?.files.find((file) => file.path === selectedPath) ?? null;
  const filteredFiles = useMemo(
    () => filterFiles(scan?.files ?? [], query, language),
    [scan?.files, query, language],
  );
  const tree = useMemo(() => buildTree(filteredFiles), [filteredFiles]);

  async function loadScan(source: 'path' | 'import') {
    setIsLoading(true);
    setError(null);
    try {
      const result =
        source === 'path'
          ? await scanRepository(repositoryPath.trim())
          : await scanImportedRepository(importId.trim());
      setScan(result);
      setSelectedPath(result.files[0]?.path ?? null);
      onScanLoaded(result);
    } catch (loadError) {
      const message = loadError instanceof Error ? loadError.message : 'Repository scan failed';
      setError(message);
      setScan(null);
      setSelectedPath(null);
      onScanLoaded(null);
    } finally {
      setIsLoading(false);
    }
  }

  function submitPath(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (repositoryPath.trim()) {
      void loadScan('path');
    }
  }

  function submitImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (importId.trim()) {
      void loadScan('import');
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row">
        <form className="flex min-w-0 flex-1 gap-2" onSubmit={submitPath}>
          <label className="sr-only" htmlFor="repository-path">
            Repository path
          </label>
          <input
            id="repository-path"
            value={repositoryPath}
            onChange={(event) => setRepositoryPath(event.target.value)}
            placeholder="/path/to/repository"
            className="h-10 min-w-0 flex-1 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent"
          />
          <button
            type="submit"
            disabled={isLoading || !repositoryPath.trim()}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FolderTree className="h-4 w-4" />
            )}
            Scan
          </button>
        </form>

        <form className="flex min-w-0 flex-1 gap-2" onSubmit={submitImport}>
          <label className="sr-only" htmlFor="import-id">
            Import ID
          </label>
          <input
            id="import-id"
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

      <div className="grid min-h-[420px] gap-4 lg:grid-cols-[300px_1fr_320px]">
        <aside className="rounded-lg border border-border bg-card">
          <div className="border-b border-border p-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <FolderTree className="h-4 w-4 text-accent" />
              File Tree
            </div>
          </div>
          <div className="max-h-[520px] overflow-auto p-2">
            {scan ? (
              <TreeView node={tree} selectedPath={selectedPath} onSelect={setSelectedPath} />
            ) : (
              <EmptyExplorerState label="Scan a repository to populate the tree." />
            )}
          </div>
        </aside>

        <div className="rounded-lg border border-border bg-card">
          <div className="grid gap-3 border-b border-border p-3 md:grid-cols-[1fr_180px]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Filter files"
                className="h-10 w-full rounded-md border border-border bg-muted pl-9 pr-3 text-sm outline-none focus:border-accent"
              />
            </div>
            <select
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              className="h-10 rounded-md border border-border bg-muted px-3 text-sm outline-none focus:border-accent"
            >
              <option value="all">All languages</option>
              {scan?.languages.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>
          <div className="max-h-[520px] overflow-auto">
            {filteredFiles.length ? (
              filteredFiles.map((file) => (
                <button
                  key={file.path}
                  type="button"
                  onClick={() => setSelectedPath(file.path)}
                  className={`grid w-full grid-cols-[1fr_auto] gap-3 border-b border-border px-3 py-2 text-left text-sm transition-colors hover:bg-muted ${
                    selectedPath === file.path ? 'bg-muted' : ''
                  }`}
                >
                  <span className="min-w-0 truncate">{file.path}</span>
                  <span className="text-muted-foreground">{file.language ?? file.extension}</span>
                </button>
              ))
            ) : (
              <EmptyExplorerState
                label={scan ? 'No files match the current filters.' : 'No repository loaded.'}
              />
            )}
          </div>
        </div>

        <aside className="rounded-lg border border-border bg-card p-4">
          {selectedFile ? (
            <FileDetails file={selectedFile} />
          ) : (
            <EmptyExplorerState label="Select a file to inspect metadata." />
          )}
        </aside>
      </div>
    </section>
  );
}

function TreeView({
  node,
  selectedPath,
  onSelect,
}: {
  node: TreeNode;
  selectedPath: string | null;
  onSelect: (path: string) => void;
}) {
  return (
    <div className="space-y-1">
      {[...node.children.values()].map((child) => (
        <TreeFolder key={child.path} node={child} selectedPath={selectedPath} onSelect={onSelect} />
      ))}
      {node.files.map((file) => (
        <TreeFile key={file.path} file={file} selectedPath={selectedPath} onSelect={onSelect} />
      ))}
    </div>
  );
}

function TreeFolder({
  node,
  selectedPath,
  onSelect,
}: {
  node: TreeNode;
  selectedPath: string | null;
  onSelect: (path: string) => void;
}) {
  return (
    <details open>
      <summary className="flex cursor-pointer list-none items-center gap-2 rounded-md px-2 py-1 text-sm hover:bg-muted">
        <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="truncate">{node.name}</span>
      </summary>
      <div className="ml-3 border-l border-border pl-2">
        <TreeView node={node} selectedPath={selectedPath} onSelect={onSelect} />
      </div>
    </details>
  );
}

function TreeFile({
  file,
  selectedPath,
  onSelect,
}: {
  file: RepositoryFileEntry;
  selectedPath: string | null;
  onSelect: (path: string) => void;
}) {
  const name = file.path.split('/').at(-1) ?? file.path;
  return (
    <button
      type="button"
      onClick={() => onSelect(file.path)}
      className={`flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-sm hover:bg-muted ${
        selectedPath === file.path ? 'bg-muted text-accent' : ''
      }`}
    >
      <FileCode2 className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
      <span className="min-w-0 truncate">{name}</span>
    </button>
  );
}

function FileDetails({ file }: { file: RepositoryFileEntry }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <FileCode2 className="h-5 w-5 text-accent" />
        <h3 className="min-w-0 truncate text-lg font-semibold">{file.path}</h3>
      </div>
      <dl className="space-y-3 text-sm">
        <Detail label="Language" value={file.language ?? 'Unknown'} />
        <Detail label="Extension" value={file.extension || 'none'} />
        <Detail label="Size" value={`${file.size_bytes.toLocaleString()} bytes`} />
      </dl>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-muted p-3">
      <dt className="text-xs uppercase text-muted-foreground">{label}</dt>
      <dd className="mt-1 break-words text-sm">{value}</dd>
    </div>
  );
}

function EmptyExplorerState({ label }: { label: string }) {
  return <div className="p-4 text-sm text-muted-foreground">{label}</div>;
}

function filterFiles(files: RepositoryFileEntry[], query: string, language: string) {
  const normalizedQuery = query.trim().toLowerCase();
  return files.filter((file) => {
    const matchesLanguage = language === 'all' || file.language === language;
    const matchesQuery = !normalizedQuery || file.path.toLowerCase().includes(normalizedQuery);
    return matchesLanguage && matchesQuery;
  });
}

function buildTree(files: RepositoryFileEntry[]): TreeNode {
  const root: TreeNode = { name: '', path: '', files: [], children: new Map() };
  for (const file of files) {
    const parts = file.path.split('/');
    let current = root;
    for (const part of parts.slice(0, -1)) {
      const path = current.path ? `${current.path}/${part}` : part;
      const existing = current.children.get(part);
      if (existing) {
        current = existing;
      } else {
        const child: TreeNode = { name: part, path, files: [], children: new Map() };
        current.children.set(part, child);
        current = child;
      }
    }
    current.files.push(file);
  }
  return root;
}
