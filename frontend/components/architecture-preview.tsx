'use client';

import '@xyflow/react/dist/style.css';

import { Background, Controls, ReactFlow, type Edge, type Node } from '@xyflow/react';

const nodes: Node[] = [
  {
    id: 'repository',
    position: { x: 0, y: 80 },
    data: { label: 'Repository' },
    type: 'input',
  },
  {
    id: 'parser',
    position: { x: 190, y: 0 },
    data: { label: 'Parser' },
  },
  {
    id: 'graph',
    position: { x: 390, y: 80 },
    data: { label: 'Knowledge Graph' },
  },
  {
    id: 'ai',
    position: { x: 590, y: 0 },
    data: { label: 'AI Layer' },
    type: 'output',
  },
  {
    id: 'docs',
    position: { x: 590, y: 160 },
    data: { label: 'Documentation' },
    type: 'output',
  },
];

const edges: Edge[] = [
  { id: 'repository-parser', source: 'repository', target: 'parser', animated: true },
  { id: 'parser-graph', source: 'parser', target: 'graph', animated: true },
  { id: 'graph-ai', source: 'graph', target: 'ai' },
  { id: 'graph-docs', source: 'graph', target: 'docs' },
];

export function ArchitecturePreview() {
  return (
    <div className="h-72 overflow-hidden rounded-lg border border-border bg-card">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        panOnScroll
      >
        <Background color="hsl(220 13% 26%)" gap={18} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
