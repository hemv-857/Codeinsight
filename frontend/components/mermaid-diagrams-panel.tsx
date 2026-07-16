'use client';

import { Copy, GitBranch, Loader2, Workflow } from 'lucide-react';
import { FormEvent, useState } from 'react';

import {
  type MermaidDiagram,
  type MermaidDiagramSet,
  type RepositoryScanResult,
  generateImportedMermaidDiagrams,
  generateMermaidDiagrams,
} from '@/lib/api';

interface MermaidDiagramsPanelProps {
  scan: RepositoryScanResult | null;
}

export function MermaidDiagramsPanel({ scan }: MermaidDiagramsPanelProps) {
  const [repositoryPath, setRepositoryPath] = useState('');
  const [importId, setImportId] = useState('');
  const [focus, setFocus] = useState('');
  const [diagrams, setDiagrams] = useState<MermaidDiagramSet | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activePath = repositoryPath.trim() || scan?.repository_path || '';

  async function generate(source: 'path' | 'import') {
    setIsLoading(true);
    setError(null);
    try {
      const focusValue = focus.trim() || undefined;
      const result =
        source === 'path'
          ? await generateMermaidDiagrams(activePath, focusValue)
          : await generateImportedMermaidDiagrams(importId.trim(), focusValue);
      setDiagrams(result);
      setRepositoryPath(result.repository_path);
    } catch (generateError) {
      setDiagrams(null);
      setError(
        generateError instanceof Error
          ? generateError.message
          : 'Mermaid diagram generation failed',
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

  return (
    <section className="space-y-4">
      <div className="grid gap-3 lg:grid-cols-2">
        <form className="space-y-3" onSubmit={submitPath}>
          <label className="sr-only" htmlFor="mermaid-repository-path">
            Repository path
          </label>
          <div className="flex gap-2">
            <input
              id="mermaid-repository-path"
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
                <Workflow className="h-4 w-4" />
              )}
              Generate
            </button>
          </div>
        </form>
        <form className="flex gap-2" onSubmit={submitImport}>
          <label className="sr-only" htmlFor="mermaid-import-id">
            Import ID
          </label>
          <input
            id="mermaid-import-id"
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

      {diagrams ? (
        <div className="space-y-4">
          <div className="grid gap-2 text-sm sm:grid-cols-4">
            <Stat label="Diagrams" value={diagrams.stats.diagram_count} />
            <Stat label="Deps" value={diagrams.stats.dependency_edge_count} />
            <Stat label="Calls" value={diagrams.stats.call_edge_count} />
            <Stat label="Components" value={diagrams.stats.component_count} />
          </div>
          <div className="grid gap-4 xl:grid-cols-3">
            {diagrams.diagrams.map((diagram) => (
              <DiagramCard key={diagram.kind} diagram={diagram} />
            ))}
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-card p-6 text-center text-sm text-muted-foreground">
          Generate Mermaid source for architecture, dependency, and call-flow diagrams.
        </div>
      )}
    </section>
  );
}

function DiagramCard({ diagram }: { diagram: MermaidDiagram }) {
  function copyDiagram() {
    void navigator.clipboard.writeText(diagram.code);
  }

  return (
    <article className="min-w-0 rounded-lg border border-border bg-card">
      <div className="flex items-start justify-between gap-3 border-b border-border p-4">
        <div>
          <h3 className="font-semibold">{diagram.title}</h3>
          <p className="mt-1 text-sm text-muted-foreground">{diagram.description}</p>
        </div>
        <button
          type="button"
          onClick={copyDiagram}
          className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-border bg-muted text-foreground transition-colors hover:bg-muted/80"
          aria-label={`Copy ${diagram.title}`}
        >
          <Copy className="h-4 w-4" />
        </button>
      </div>
      <pre className="max-h-[360px] overflow-auto whitespace-pre-wrap p-4 font-mono text-xs leading-5 text-foreground">
        {diagram.code}
      </pre>
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
