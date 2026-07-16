'use client';

import { Bug, FileCode2, Loader2 } from 'lucide-react';
import { FormEvent, useState } from 'react';

import { type ParsedStackTrace, type StackTraceFrame, parseStackTrace } from '@/lib/api';

const sampleTrace = `Traceback (most recent call last):
  File "app/services/payment.py", line 42, in charge
    gateway.charge(card)
PaymentError: card declined`;

export function StackTracePanel() {
  const [stackTrace, setStackTrace] = useState(sampleTrace);
  const [result, setResult] = useState<ParsedStackTrace | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stackTrace.trim()) {
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      setResult(await parseStackTrace(stackTrace));
    } catch (parseError) {
      setResult(null);
      setError(parseError instanceof Error ? parseError.message : 'Stack trace parsing failed');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="space-y-4">
      <form className="space-y-3" onSubmit={submit}>
        <label className="sr-only" htmlFor="stack-trace-input">
          Stack trace
        </label>
        <textarea
          id="stack-trace-input"
          value={stackTrace}
          onChange={(event) => setStackTrace(event.target.value)}
          rows={7}
          className="min-h-36 w-full resize-y rounded-md border border-border bg-card px-3 py-3 font-mono text-sm outline-none focus:border-accent"
        />
        <button
          type="submit"
          disabled={isLoading || !stackTrace.trim()}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Bug className="h-4 w-4" />}
          Parse Trace
        </button>
      </form>

      {error ? (
        <div className="rounded-md border border-red-400/30 bg-red-950/30 px-3 py-2 text-sm text-red-100">
          {error}
        </div>
      ) : null}

      {result ? (
        <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
          <aside className="space-y-3 rounded-lg border border-border bg-card p-4">
            <div className="flex items-center gap-2">
              <FileCode2 className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">Parsed Trace</h3>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <Stat label="Frames" value={result.stats.frame_count} />
              <Stat label="Files" value={result.stats.file_count} />
            </div>
            <div className="rounded-md bg-muted p-3 text-sm">
              <p className="text-xs uppercase text-muted-foreground">Language</p>
              <p className="mt-1 font-medium">{result.language}</p>
            </div>
            {result.error_type ? (
              <div className="rounded-md bg-muted p-3 text-sm">
                <p className="text-xs uppercase text-muted-foreground">Error</p>
                <p className="mt-1 break-words font-medium">{result.error_type}</p>
                {result.message ? (
                  <p className="mt-1 break-words text-muted-foreground">{result.message}</p>
                ) : null}
              </div>
            ) : null}
          </aside>
          <div className="max-h-[420px] overflow-auto rounded-lg border border-border bg-card">
            {result.frames.length ? (
              result.frames.map((frame, index) => (
                <FrameCard key={`${frame.file_path}-${frame.line}-${index}`} frame={frame} />
              ))
            ) : (
              <div className="p-6 text-center text-sm text-muted-foreground">
                No stack frames were detected.
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-card p-6 text-center text-sm text-muted-foreground">
          Paste a stack trace to extract files, functions, lines, and error metadata.
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

function FrameCard({ frame }: { frame: StackTraceFrame }) {
  return (
    <article className="space-y-2 border-b border-border p-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <p className="break-words text-sm font-medium">
            {frame.file_path}:{frame.line}
            {frame.column ? `:${frame.column}` : ''}
          </p>
          {frame.function ? (
            <p className="mt-1 break-words text-sm text-muted-foreground">{frame.function}</p>
          ) : null}
        </div>
        <p className="text-xs uppercase text-accent">{frame.language}</p>
      </div>
      <p className="break-words font-mono text-xs text-muted-foreground">{frame.raw}</p>
    </article>
  );
}
