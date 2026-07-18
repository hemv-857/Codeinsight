'use client';

import '@xyflow/react/dist/style.css';

import { Background, Controls, MiniMap, ReactFlow, type Edge, type Node } from '@xyflow/react';
import { Database, GitBranch, Loader2, Network, RefreshCw, Share2 } from 'lucide-react';
import { FormEvent, useEffect, useMemo, useState } from 'react';

import { useRepo } from '@/components/repo-context';
import { GraphControlToggle } from '@/components/graph-control-toggle';
import {
  type KnowledgeGraphResult,
  type RepositoryScanResult,
  buildImportedKnowledgeGraph,
  buildKnowledgeGraph,
} from '@/lib/api';

interface KnowledgeGraphPanelProps {
  scan: RepositoryScanResult | null;
}

export function KnowledgeGraphPanel({ scan }: KnowledgeGraphPanelProps) {
  const { pipelineResults } = useRepo();
  const [repositoryPath, setRepositoryPath] = useState('');
  const [importId, setImportId] = useState('');
  const [graph, setGraph] = useState<KnowledgeGraphResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nodesDraggable, setNodesDraggable] = useState(false);
  const [showMiniMap, setShowMiniMap] = useState(true);
  const [showEdgeLabels, setShowEdgeLabels] = useState(true);

  useEffect(() => {
    const data = pipelineResults.knowledge as KnowledgeGraphResult | undefined;
    if (data && !graph) setGraph(data);
  }, [pipelineResults, graph]);

  const activePath = repositoryPath.trim() || scan?.repository_path || '';
  const activeImportId = importId.trim();
  const lastSource = activeImportId ? ('import' as const) : ('path' as const);
  const { nodes, edges } = useMemo(
    () => toFlowElements(graph, showEdgeLabels),
    [graph, showEdgeLabels],
  );

  async function loadGraph(source: 'path' | 'import') {
    setIsLoading(true);
    setError(null);
    try {
      const result =
        source === 'path'
          ? await buildKnowledgeGraph(activePath)
          : await buildImportedKnowledgeGraph(importId.trim());
      setGraph(result);
      setRepositoryPath(result.repository_path);
    } catch (loadError) {
      setGraph(null);
      setError(loadError instanceof Error ? loadError.message : 'Knowledge graph build failed');
    } finally {
      setIsLoading(false);
    }
  }

  function submitPath(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (activePath) {
      void loadGraph('path');
    }
  }

  function submitImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (importId.trim()) {
      void loadGraph('import');
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row">
        <form className="flex min-w-0 flex-1 gap-2" onSubmit={submitPath}>
          <label className="sr-only" htmlFor="knowledge-repository-path">
            Repository path
          </label>
          <input
            id="knowledge-repository-path"
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
              <Network className="h-4 w-4" />
            )}
            Build
          </button>
        </form>

        <form className="flex min-w-0 flex-1 gap-2" onSubmit={submitImport}>
          <label className="sr-only" htmlFor="knowledge-import-id">
            Import ID
          </label>
          <input
            id="knowledge-import-id"
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

      <div className="flex flex-wrap gap-2 rounded-lg border border-border bg-card p-2">
        <GraphControlToggle
          label="Drag Nodes"
          enabled={nodesDraggable}
          onChange={setNodesDraggable}
        />
        <GraphControlToggle label="Minimap" enabled={showMiniMap} onChange={setShowMiniMap} />
        <GraphControlToggle
          label="Edge Labels"
          enabled={showEdgeLabels}
          onChange={setShowEdgeLabels}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
        <div className="h-[420px] overflow-hidden rounded-lg border border-border bg-card">
          {graph ? (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              fitView
              nodesDraggable={nodesDraggable}
              nodesConnectable={false}
              panOnScroll
            >
              <Background color="hsl(220 13% 26%)" gap={18} />
              {showMiniMap ? (
                <MiniMap
                  nodeColor="hsl(174 64% 42%)"
                  maskColor="hsl(222 18% 8% / 0.72)"
                  pannable
                  zoomable
                />
              ) : null}
              <Controls />
            </ReactFlow>
          ) : (
            <div className="flex h-full items-center justify-center p-6 text-center text-sm text-muted-foreground">
              Build a knowledge graph to persist repository architecture relationships.
            </div>
          )}
        </div>

        <aside className="space-y-4 rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Share2 className="h-5 w-5 text-accent" />
              <h3 className="text-lg font-semibold">Knowledge Graph</h3>
            </div>
            {graph ? (
              <button
                type="button"
                onClick={() => void loadGraph(lastSource)}
                className="rounded-md border border-border bg-muted p-2 text-muted-foreground hover:text-foreground"
                aria-label="Refresh knowledge graph"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            ) : null}
          </div>

          {graph ? (
            <>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <Stat label="Nodes" value={graph.stats.node_count} />
                <Stat label="Edges" value={graph.stats.edge_count} />
                <Stat label="Files" value={graph.stats.file_count} />
                <Stat label="Symbols" value={graph.stats.symbol_count} />
              </div>

              <div className="rounded-md bg-muted p-3 text-sm">
                <p className="font-medium">Relationships</p>
                <p className="mt-2 text-muted-foreground">
                  {graph.stats.dependency_edge_count} imports / {graph.stats.call_edge_count} calls
                </p>
              </div>

              <div className="rounded-md bg-muted p-3 text-sm">
                <div className="flex items-center gap-2 font-medium">
                  <Database className="h-4 w-4 text-primary" />
                  Persistence
                </div>
                <p className="mt-2 break-words text-muted-foreground">
                  {graph.persistence.persisted ? 'Persisted' : 'Not persisted'} to{' '}
                  {graph.persistence.backend}
                  {graph.persistence.durable_backend
                    ? ` + ${graph.persistence.durable_backend}`
                    : ''}
                </p>
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              The knowledge graph combines files, symbols, imports, and calls into the persisted
              architecture model.
            </p>
          )}
        </aside>
      </div>
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

function toFlowElements(
  graph: KnowledgeGraphResult | null,
  showEdgeLabels: boolean,
): { nodes: Node[]; edges: Edge[] } {
  if (!graph) {
    return { nodes: [], edges: [] };
  }

  const nodes: Node[] = [
    createNode('repository', 'Repository', compactPath(graph.repository_path), 0, 120),
    createNode('files', 'Files', String(graph.stats.file_count), 260, 40),
    createNode('symbols', 'Symbols', String(graph.stats.symbol_count), 520, 40),
    createNode('imports', 'Imports', String(graph.stats.dependency_edge_count), 260, 220),
    createNode('calls', 'Calls', String(graph.stats.call_edge_count), 520, 220),
    createNode('storage', 'Graph Store', graph.persistence.backend, 780, 120),
  ];

  const edges: Edge[] = [
    createEdge('repository-files', 'repository', 'files', 'contains', showEdgeLabels),
    createEdge('files-symbols', 'files', 'symbols', 'defines', showEdgeLabels),
    createEdge('files-imports', 'files', 'imports', 'imports', showEdgeLabels),
    createEdge('symbols-calls', 'symbols', 'calls', 'calls', showEdgeLabels),
    createEdge('imports-storage', 'imports', 'storage', 'persists', showEdgeLabels),
    createEdge('calls-storage', 'calls', 'storage', 'persists', showEdgeLabels),
  ];

  return { nodes, edges };
}

function createNode(id: string, title: string, detail: string, x: number, y: number): Node {
  return {
    id,
    position: { x, y },
    data: { label: `${title}\n${detail}` },
    style: {
      width: 180,
      whiteSpace: 'pre-line',
      border: '1px solid hsl(220 13% 28%)',
      background: 'hsl(222 18% 12%)',
      color: 'hsl(210 30% 96%)',
      fontSize: 12,
    },
  };
}

function createEdge(
  id: string,
  source: string,
  target: string,
  label: string,
  showLabel: boolean,
): Edge {
  return {
    id,
    source,
    target,
    label: showLabel ? label : undefined,
    style: { stroke: 'hsl(174 64% 42%)' },
  };
}

function compactPath(path: string) {
  return path.split('/').at(-1) || path;
}
