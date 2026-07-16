'use client';

import '@xyflow/react/dist/style.css';

import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
  type NodeMouseHandler,
} from '@xyflow/react';
import { GitBranch, Loader2, Network, RefreshCw, TriangleAlert } from 'lucide-react';
import { FormEvent, useMemo, useState } from 'react';

import { GraphControlToggle } from '@/components/graph-control-toggle';
import {
  type DependencyGraphResult,
  type RepositoryScanResult,
  buildDependencyGraph,
  buildImportedDependencyGraph,
} from '@/lib/api';

interface DependencyGraphPanelProps {
  scan: RepositoryScanResult | null;
}

export function DependencyGraphPanel({ scan }: DependencyGraphPanelProps) {
  const [repositoryPath, setRepositoryPath] = useState('');
  const [importId, setImportId] = useState('');
  const [graph, setGraph] = useState<DependencyGraphResult | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nodesDraggable, setNodesDraggable] = useState(false);
  const [showMiniMap, setShowMiniMap] = useState(true);
  const [showEdgeLabels, setShowEdgeLabels] = useState(true);

  const activePath = repositoryPath.trim() || scan?.repository_path || '';
  const selectedNode = graph?.nodes.find((node) => node.path === selectedPath) ?? null;
  const internalEdges = graph?.edges.filter((edge) => edge.target !== null) ?? [];
  const { nodes, edges } = useMemo(
    () => toFlowElements(graph, selectedPath, showEdgeLabels),
    [graph, selectedPath, showEdgeLabels],
  );

  async function loadGraph(source: 'path' | 'import') {
    setIsLoading(true);
    setError(null);
    try {
      const result =
        source === 'path'
          ? await buildDependencyGraph(activePath)
          : await buildImportedDependencyGraph(importId.trim());
      setGraph(result);
      setSelectedPath(result.nodes[0]?.path ?? null);
      setRepositoryPath(result.repository_path);
    } catch (loadError) {
      const message =
        loadError instanceof Error ? loadError.message : 'Dependency graph build failed';
      setGraph(null);
      setSelectedPath(null);
      setError(message);
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

  const onNodeClick: NodeMouseHandler = (_event, node) => {
    setSelectedPath(String(node.id));
  };

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row">
        <form className="flex min-w-0 flex-1 gap-2" onSubmit={submitPath}>
          <label className="sr-only" htmlFor="dependency-repository-path">
            Repository path
          </label>
          <input
            id="dependency-repository-path"
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
          <label className="sr-only" htmlFor="dependency-import-id">
            Import ID
          </label>
          <input
            id="dependency-import-id"
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
        <div className="h-[520px] overflow-hidden rounded-lg border border-border bg-card">
          {graph ? (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              fitView
              onNodeClick={onNodeClick}
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
              Build a dependency graph to inspect file-level imports and cycles.
            </div>
          )}
        </div>

        <aside className="space-y-4 rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Network className="h-5 w-5 text-accent" />
              <h3 className="text-lg font-semibold">Graph Details</h3>
            </div>
            {graph ? (
              <button
                type="button"
                onClick={() => void loadGraph('path')}
                className="rounded-md border border-border bg-muted p-2 text-muted-foreground hover:text-foreground"
                aria-label="Refresh dependency graph"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            ) : null}
          </div>

          {graph ? (
            <>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <Stat label="Files" value={graph.stats.file_count} />
                <Stat label="Internal" value={graph.stats.internal_dependency_count} />
                <Stat label="External" value={graph.stats.external_dependency_count} />
                <Stat label="Cycles" value={graph.stats.circular_dependency_count} />
              </div>

              <div className="space-y-2">
                <h4 className="text-sm font-medium">Selected File</h4>
                {selectedNode ? (
                  <div className="rounded-md bg-muted p-3 text-sm">
                    <p className="break-words font-medium">{selectedNode.path}</p>
                    <p className="mt-1 text-muted-foreground">{selectedNode.language}</p>
                    <p className="mt-2 text-muted-foreground">
                      {internalEdges.filter((edge) => edge.source === selectedNode.path).length}{' '}
                      outgoing /{' '}
                      {internalEdges.filter((edge) => edge.target === selectedNode.path).length}{' '}
                      incoming
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Select a node to inspect edges.</p>
                )}
              </div>

              <AlertList
                title="Unresolved Imports"
                values={graph.unresolved_imports}
                emptyLabel="No unresolved imports."
              />
              <AlertList
                title="Circular Dependencies"
                values={graph.circular_dependencies.map((cycle) => cycle.join(' -> '))}
                emptyLabel="No circular dependencies."
              />
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              The graph panel uses parsed imports from supported source files.
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

function AlertList({
  title,
  values,
  emptyLabel,
}: {
  title: string;
  values: string[];
  emptyLabel: string;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm font-medium">
        <TriangleAlert className="h-4 w-4 text-primary" />
        {title}
      </div>
      <div className="max-h-28 overflow-auto rounded-md bg-muted p-2 text-sm text-muted-foreground">
        {values.length ? (
          values.slice(0, 8).map((value, index) => (
            <p key={`${value}-${index}`} className="break-words py-1">
              {value}
            </p>
          ))
        ) : (
          <p>{emptyLabel}</p>
        )}
      </div>
    </div>
  );
}

function toFlowElements(
  graph: DependencyGraphResult | null,
  selectedPath: string | null,
  showEdgeLabels: boolean,
): { nodes: Node[]; edges: Edge[] } {
  if (!graph) {
    return { nodes: [], edges: [] };
  }

  const selectedNeighbors = new Set<string>();
  if (selectedPath) {
    for (const edge of graph.edges) {
      if (edge.source === selectedPath && edge.target) {
        selectedNeighbors.add(edge.target);
      }
      if (edge.target === selectedPath) {
        selectedNeighbors.add(edge.source);
      }
    }
  }

  const columns = Math.max(1, Math.ceil(Math.sqrt(graph.nodes.length)));
  const nodes: Node[] = graph.nodes.map((node, index) => ({
    id: node.path,
    position: {
      x: (index % columns) * 260,
      y: Math.floor(index / columns) * 120,
    },
    data: { label: compactPath(node.path) },
    style: {
      width: 210,
      border:
        node.path === selectedPath ? '2px solid hsl(174 64% 42%)' : '1px solid hsl(220 13% 28%)',
      background: selectedNeighbors.has(node.path) ? 'hsl(223 24% 18%)' : 'hsl(222 18% 12%)',
      color: 'hsl(210 30% 96%)',
      fontSize: 12,
    },
  }));
  const edges: Edge[] = graph.edges
    .filter((edge) => edge.target !== null)
    .map((edge, index) => ({
      id: `${edge.source}-${edge.target}-${index}`,
      source: edge.source,
      target: edge.target ?? '',
      label: showEdgeLabels ? edge.import_name : undefined,
      animated: false,
      style: {
        stroke:
          edge.source === selectedPath || edge.target === selectedPath
            ? 'hsl(38 92% 50%)'
            : 'hsl(174 64% 42%)',
      },
    }));
  return { nodes, edges };
}

function compactPath(path: string) {
  const parts = path.split('/');
  return parts.length > 2 ? `${parts.at(-2)}/${parts.at(-1)}` : path;
}
