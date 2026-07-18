'use client';

import { Database, GitBranch, Loader2, Search } from 'lucide-react';
import { FormEvent, useState } from 'react';

import {
  type RepositoryScanResult,
  type SearchResult,
  type SearchResultItem,
  type VectorStoreResult,
  indexImportedRepositoryVectors,
  indexRepositoryVectors,
  searchImportedRepository,
  searchRepository,
} from '@/lib/api';

interface RepositorySearchPanelProps {
  scan: RepositoryScanResult | null;
}

export function RepositorySearchPanel({ scan }: RepositorySearchPanelProps) {
  const [repositoryPath, setRepositoryPath] = useState('');
  const [importId, setImportId] = useState('');
  const [query, setQuery] = useState('');
  const [limit, setLimit] = useState(10);
  const [indexResult, setIndexResult] = useState<VectorStoreResult | null>(null);
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);
  const [isIndexing, setIsIndexing] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activePath = repositoryPath.trim() || scan?.repository_path || '';
  const activeImportId = importId.trim();

  async function indexVectors() {
    setIsIndexing(true);
    setError(null);
    try {
      const result = activeImportId
        ? await indexImportedRepositoryVectors(activeImportId)
        : await indexRepositoryVectors(activePath);
      setIndexResult(result);
      setRepositoryPath(result.repository_path);
    } catch (indexError) {
      setError(indexError instanceof Error ? indexError.message : 'Vector indexing failed');
    } finally {
      setIsIndexing(false);
    }
  }

  async function runSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSearching(true);
    setError(null);
    try {
      const result = activeImportId
        ? await searchImportedRepository(activeImportId, query.trim(), limit)
        : await searchRepository(activePath, query.trim(), limit);
      setSearchResult(result);
      setRepositoryPath(result.repository_path);
    } catch (searchError) {
      setSearchResult(null);
      setError(searchError instanceof Error ? searchError.message : 'Repository search failed');
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <section className="space-y-4">
      <div className="grid gap-3 lg:grid-cols-[1fr_220px]">
        <label className="sr-only" htmlFor="search-repository-path">
          Repository path
        </label>
        <input
          id="search-repository-path"
          value={repositoryPath}
          onChange={(event) => setRepositoryPath(event.target.value)}
          placeholder={scan?.repository_path ?? '/path/to/repository'}
          className="h-10 min-w-0 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent"
        />
        <label className="sr-only" htmlFor="search-import-id">
          Import ID
        </label>
        <input
          id="search-import-id"
          value={importId}
          onChange={(event) => setImportId(event.target.value)}
          placeholder="import id"
          className="h-10 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent"
        />
      </div>

      <div className="flex flex-col gap-3 lg:flex-row">
        <form className="flex min-w-0 flex-1 gap-2" onSubmit={runSearch}>
          <label className="sr-only" htmlFor="repository-search-query">
            Search query
          </label>
          <div className="relative min-w-0 flex-1">
            <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <input
              id="repository-search-query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search symbols, files, and architecture context"
              className="h-10 w-full rounded-md border border-border bg-card pl-9 pr-3 text-sm outline-none focus:border-accent"
            />
          </div>
          <select
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value))}
            className="h-10 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent"
            aria-label="Result limit"
          >
            {[5, 10, 20, 50].map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={isSearching || !query.trim() || (!activePath && !activeImportId)}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
          >
            {isSearching ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            Search
          </button>
        </form>

        <button
          type="button"
          onClick={() => void indexVectors()}
          disabled={isIndexing || (!activePath && !activeImportId)}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-border bg-muted px-4 text-sm font-medium text-foreground transition-colors hover:bg-muted/80 disabled:pointer-events-none disabled:opacity-50"
        >
          {isIndexing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : activeImportId ? (
            <GitBranch className="h-4 w-4" />
          ) : (
            <Database className="h-4 w-4" />
          )}
          Index Vectors
        </button>
      </div>

      {!indexResult && activePath ? (
        <div className="rounded-md border border-accent/30 bg-accent/10 px-3 py-2 text-sm text-accent">
          Click &quot;Index Vectors&quot; first to enable semantic search.
        </div>
      ) : null}

      {error ? (
        <div className="rounded-md border border-red-400/30 bg-red-950/30 px-3 py-2 text-sm text-red-100">
          {error}
        </div>
      ) : null}

      {indexResult ? (
        <div className="grid gap-2 rounded-lg border border-border bg-card p-3 text-sm md:grid-cols-4">
          <Stat label="Embeddings" value={indexResult.stored_embedding_count} />
          <Stat label="Dimensions" value={indexResult.dimensions} />
          <Stat label="Backend" value={indexResult.backend} />
          <Stat label="Skipped" value={indexResult.skipped_file_count} />
        </div>
      ) : null}

      <div className="rounded-lg border border-border bg-card">
        <div className="flex items-center justify-between gap-3 border-b border-border p-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Search className="h-4 w-4 text-accent" />
            Results
          </div>
          {searchResult ? (
            <p className="text-sm text-muted-foreground">
              {searchResult.stats.result_count} of {searchResult.stats.searched_embedding_count}
            </p>
          ) : null}
        </div>
        <div className="max-h-[560px] overflow-auto">
          {searchResult?.results.length ? (
            searchResult.results.map((item) => <SearchResultCard key={item.chunk_id} item={item} />)
          ) : (
            <div className="p-6 text-center text-sm text-muted-foreground">
              Index vectors, then search for a symbol, file, or architecture concept.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-md bg-muted p-3">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 break-words text-lg font-semibold">{value}</p>
    </div>
  );
}

function SearchResultCard({ item }: { item: SearchResultItem }) {
  const symbol = [item.symbol_parent, item.symbol_name].filter(Boolean).join('.');
  return (
    <article className="space-y-3 border-b border-border p-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <p className="break-words text-sm font-medium">
            {item.path}:{item.start_line}-{item.end_line}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {item.language} / {item.kind}
            {symbol ? ` / ${symbol}` : ''}
          </p>
        </div>
        <div className="grid grid-cols-4 gap-2 text-right text-xs text-muted-foreground">
          <Score label="total" value={item.score} />
          <Score label="vector" value={item.vector_score} />
          <Score label="keyword" value={item.keyword_score} />
          <Score label="graph" value={item.graph_score} />
        </div>
      </div>
      <pre className="max-h-48 overflow-auto rounded-md bg-muted p-3 text-xs leading-relaxed text-foreground">
        <code>{item.content}</code>
      </pre>
      {item.related_paths.length ? (
        <p className="break-words text-xs text-muted-foreground">
          Related: {item.related_paths.slice(0, 5).join(', ')}
        </p>
      ) : null}
    </article>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p>{label}</p>
      <p className="font-medium text-foreground">{value.toFixed(2)}</p>
    </div>
  );
}
