'use client';

import { Copy, FileText, GitBranch, Loader2 } from 'lucide-react';
import { FormEvent, useState } from 'react';

import {
  type GeneratedArchitectureDoc,
  type RepositoryScanResult,
  generateArchitectureDocs,
  generateImportedArchitectureDocs,
} from '@/lib/api';

interface ArchitectureDocsPanelProps {
  scan: RepositoryScanResult | null;
}

export function ArchitectureDocsPanel({ scan }: ArchitectureDocsPanelProps) {
  const [repositoryPath, setRepositoryPath] = useState('');
  const [importId, setImportId] = useState('');
  const [focus, setFocus] = useState('');
  const [document, setDocument] = useState<GeneratedArchitectureDoc | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const activePath = repositoryPath.trim() || scan?.repository_path || '';

  async function generate(source: 'path' | 'import') {
    setIsLoading(true);
    setError(null);
    try {
      const focusValue = focus.trim() || undefined;
      const result =
        source === 'path'
          ? await generateArchitectureDocs(activePath, focusValue)
          : await generateImportedArchitectureDocs(importId.trim(), focusValue);
      setDocument(result);
      setRepositoryPath(result.repository_path);
    } catch (generateError) {
      setDocument(null);
      setError(
        generateError instanceof Error
          ? generateError.message
          : 'Architecture docs generation failed',
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
    if (document) {
      void navigator.clipboard.writeText(document.markdown).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
    }
  }

  return (
    <section className="space-y-4">
      <div className="grid gap-3 lg:grid-cols-2">
        <form className="space-y-3" onSubmit={submitPath}>
          <label className="sr-only" htmlFor="architecture-docs-repository-path">
            Repository path
          </label>
          <div className="flex gap-2">
            <input
              id="architecture-docs-repository-path"
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
                <FileText className="h-4 w-4" />
              )}
              Generate
            </button>
          </div>
        </form>
        <form className="flex gap-2" onSubmit={submitImport}>
          <label className="sr-only" htmlFor="architecture-docs-import-id">
            Import ID
          </label>
          <input
            id="architecture-docs-import-id"
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

      <input
        value={focus}
        onChange={(event) => setFocus(event.target.value)}
        placeholder="optional focus, such as authentication or checkout"
        className="h-10 w-full rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent"
      />

      {error ? (
        <div className="rounded-md border border-red-400/30 bg-red-950/30 px-3 py-2 text-sm text-red-100">
          {error}
        </div>
      ) : null}

      {document ? (
        <div className="grid gap-4 xl:grid-cols-[260px_1fr]">
          <aside className="space-y-3 rounded-lg border border-border bg-card p-4">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">{document.title}</h3>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <Stat label="Sections" value={document.stats.section_count} />
              <Stat label="Words" value={document.stats.word_count} />
              <Stat label="Components" value={document.stats.component_count} />
              <Stat label="Conf" value={Math.round(document.stats.confidence * 100)} />
            </div>
            <button
              type="button"
              onClick={copyMarkdown}
              className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-md border border-border bg-muted px-4 text-sm font-medium text-foreground transition-colors hover:bg-muted/80"
            >
              <Copy className="h-4 w-4" />
              {copied ? 'Copied!' : 'Copy Markdown'}
            </button>
            <div className="rounded-md bg-muted p-3 text-sm">
              <p className="text-xs uppercase text-muted-foreground">Evidence</p>
              <p className="mt-1 font-medium">{document.stats.evidence_path_count} paths</p>
            </div>
          </aside>
          <pre className="max-h-[520px] overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-card p-4 font-mono text-sm leading-6 text-foreground">
            {document.markdown}
          </pre>
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-card p-6 text-center text-sm text-muted-foreground">
          Generate architecture Markdown from repository summary, dependency, call, and parser
          evidence.
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
