'use client';

import { Code, Download, Maximize2, Minimize2 } from 'lucide-react';
import { useId, useCallback, useEffect, useRef, useState } from 'react';

interface MermaidDiagramProps {
  code: string;
  title: string;
}

export function MermaidDiagram({ code, title }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const diagramId = useId();
  const [showSource, setShowSource] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [renderError, setRenderError] = useState<string | null>(null);

  const renderDiagram = useCallback(async () => {
    if (!containerRef.current || showSource || !code.trim()) return;

    try {
      const mermaid = (await import('mermaid')).default;
      mermaid.initialize({
        startOnLoad: false,
        theme: 'dark',
        themeVariables: {
          primaryColor: 'hsl(222 18% 16%)',
          primaryTextColor: 'hsl(210 30% 96%)',
          primaryBorderColor: 'hsl(174 64% 42%)',
          lineColor: 'hsl(174 64% 42%)',
          secondaryColor: 'hsl(223 24% 18%)',
          tertiaryColor: 'hsl(222 18% 12%)',
          fontFamily: 'ui-sans-serif, system-ui, sans-serif',
          fontSize: '13px',
        },
        flowchart: {
          curve: 'basis',
          padding: 16,
          htmlLabels: true,
          useMaxWidth: true,
        },
        securityLevel: 'strict',
      });

      const { svg } = await mermaid.render(diagramId, code);
      if (containerRef.current) {
        containerRef.current.innerHTML = svg;
        setRenderError(null);
      }
    } catch (err) {
      setRenderError(err instanceof Error ? err.message : 'Failed to render diagram');
    }
  }, [code, diagramId, showSource]);

  useEffect(() => {
    void renderDiagram();
  }, [renderDiagram]);

  function downloadSvg() {
    const svg = containerRef.current?.querySelector('svg');
    if (!svg) return;
    const blob = new Blob([svg.outerHTML], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.toLowerCase().replace(/\s+/g, '-')}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div
      className={`rounded-lg border border-border bg-card overflow-hidden ${
        isFullscreen ? 'fixed inset-0 z-50 m-0 rounded-none' : ''
      }`}
    >
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h4 className="text-sm font-semibold">{title}</h4>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setShowSource(!showSource)}
            className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label={showSource ? 'Show diagram' : 'Show source code'}
            title={showSource ? 'Show diagram' : 'Show source code'}
          >
            <Code className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={downloadSvg}
            className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Download SVG"
            title="Download SVG"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {showSource ? (
        <div className="p-4">
          <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-md bg-muted p-4 font-mono text-xs leading-5 text-muted-foreground">
            {code}
          </pre>
        </div>
      ) : (
        <div
          className={`flex items-center justify-center overflow-auto p-6 ${
            isFullscreen ? 'h-[calc(100vh-52px)]' : 'min-h-[300px] max-h-[500px]'
          }`}
        >
          {renderError ? (
            <div className="space-y-3 text-center">
              <p className="text-sm text-red-400">{renderError}</p>
              <button
                type="button"
                onClick={() => setShowSource(true)}
                className="text-sm text-accent underline-offset-4 hover:underline"
              >
                View source instead
              </button>
            </div>
          ) : (
            <div ref={containerRef} className="w-full [&>svg]:w-full [&>svg]:h-auto" />
          )}
        </div>
      )}
    </div>
  );
}
