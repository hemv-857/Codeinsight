'use client';

import { Bot, Download, GitBranch, History, Loader2, Send, User } from 'lucide-react';
import { FormEvent, useCallback, useRef, useState } from 'react';

import { ConversationHistory, useConversationHistory } from '@/components/conversation-history';
import { EmptyState } from '@/components/empty-state';
import { ImportProgressIndicator } from '@/components/import-progress';
import { isGithubUrl } from '@/lib/utils';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8002';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  mode?: string;
  confidence?: number;
  supportingFiles?: string[];
}

export function RepositoryQAPanel() {
  const [repoInput, setRepoInput] = useState('');
  const [activeRepo, setActiveRepo] = useState('');
  const [activeImportId, setActiveImportId] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const [importStatus, setImportStatus] = useState('');
  const [importingSource, setImportingSource] = useState('');
  const [importingSourceType, setImportingSourceType] = useState<'github' | 'local'>('local');

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [historyOpen, setHistoryOpen] = useState(false);
  const { activeId, setActiveId, saveSession } = useConversationHistory();

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  function startImport() {
    const source = repoInput.trim();
    if (!source) return;
    setIsImporting(true);
    setImportingSource(source);
    setImportingSourceType(isGithubUrl(source) ? 'github' : 'local');
    setImportStatus('Importing repository...');
  }

  const handleImportCompleted = useCallback(
    (result: {
      import_id: string;
      repository_path: string;
      file_count: number;
      languages: string[];
    }) => {
      setActiveImportId(result.import_id);
      setActiveRepo(result.repository_path);
      setImportStatus(`Ready: ${result.file_count} files indexed`);
      setIsImporting(false);
      setImportingSource('');
      setMessages([]);
    },
    [],
  );

  const handleImportError = useCallback((message: string) => {
    setImportStatus(`Error: ${message}`);
    setIsImporting(false);
    setImportingSource('');
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = input.trim();
    if (!question || isStreaming) return;

    const repo = activeRepo || repoInput.trim();
    if (!repo) return;

    setInput('');
    const userMsg: Message = { role: 'user', content: question };
    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);

    const assistantIdx = messages.length + 1;
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

    try {
      abortRef.current = new AbortController();
      const endpoint = activeImportId
        ? `${API_BASE_URL}/api/repositories/imports/${activeImportId}/question/stream`
        : `${API_BASE_URL}/api/repositories/question/stream`;
      const body = activeImportId ? { question } : { repository_path: repo, question };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: abortRef.current.signal,
      });

      if (!response.ok) throw new Error(`Q&A failed: ${response.status}`);

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response stream');

      const decoder = new TextDecoder();
      let buffer = '';
      let answerText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            if (line.slice(7).trim() === 'answer.done') {
              setIsStreaming(false);
              const repoName =
                activeRepo.split('/').pop() || repoInput.split('/').pop() || 'Unknown';
              const userCount = messages.filter((m) => m.role === 'user').length + 1;
              saveSession(repoName, question, userCount);
              return;
            }
          } else if (line.startsWith('data: ')) {
            try {
              const payload = JSON.parse(line.slice(6));
              if (payload.text) {
                answerText += payload.text;
                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[assistantIdx];
                  if (last) updated[assistantIdx] = { ...last, content: answerText };
                  return updated;
                });
              } else if (payload.mode) {
                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[assistantIdx];
                  if (last) {
                    updated[assistantIdx] = {
                      ...last,
                      mode: payload.mode,
                      confidence: payload.confidence,
                      supportingFiles: payload.supporting_files,
                    };
                  }
                  return updated;
                });
              }
            } catch {
              // skip malformed
            }
          }
        }
        scrollToBottom();
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return;
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[assistantIdx];
        if (last) {
          updated[assistantIdx] = {
            ...last,
            content: `Error: ${error instanceof Error ? error.message : 'Q&A failed'}`,
          };
        }
        return updated;
      });
    } finally {
      setIsStreaming(false);
    }
  }

  function stopStreaming() {
    abortRef.current?.abort();
    setIsStreaming(false);
  }

  function handleNewConversation() {
    setMessages([]);
    setActiveId(null);
  }

  const repoReady = Boolean(activeRepo || repoInput.trim());

  return (
    <section className="space-y-4">
      <div
        className="flex rounded-lg border border-border bg-card overflow-hidden"
        style={{ height: 540 }}
      >
        <ConversationHistory
          activeId={activeId}
          isOpen={historyOpen}
          onClose={() => setHistoryOpen(false)}
          onSelect={(session) => {
            setActiveId(session.id);
            setRepoInput(session.repoName);
          }}
          onNew={handleNewConversation}
        />

        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex items-center gap-2 border-b border-border p-3">
            <button
              type="button"
              onClick={() => setHistoryOpen(!historyOpen)}
              className="inline-flex h-7 w-7 items-center justify-center rounded-md hover:bg-muted transition-colors"
              title="Toggle history"
            >
              <History className="h-4 w-4" />
            </button>
            <Bot className="h-4 w-4 text-accent" />
            <span className="text-sm font-medium">Repository Q&A</span>
          </div>

          <div className="p-3 space-y-3 border-b border-border">
            <div className="flex gap-2">
              <input
                value={repoInput}
                onChange={(e) => setRepoInput(e.target.value)}
                placeholder="GitHub URL or local path"
                disabled={isImporting}
                className="flex-1 h-10 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent disabled:opacity-50"
              />
              <button
                type="button"
                onClick={startImport}
                disabled={isImporting || !repoInput.trim()}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
              >
                {isImporting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                Load
              </button>
            </div>
            {isImporting && importingSource ? (
              <ImportProgressIndicator
                source={importingSource}
                sourceType={importingSourceType}
                onCompleted={handleImportCompleted}
                onError={handleImportError}
              />
            ) : importStatus ? (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <GitBranch className="h-3 w-3" />
                {importStatus}
              </div>
            ) : null}
          </div>

          <div className="flex-1 overflow-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <EmptyState
                illustration="chat"
                icon="chat"
                title="Ask about your codebase"
                description={
                  repoReady
                    ? 'Ask questions about architecture, functions, or dependencies. Powered by Groq LLM.'
                    : 'Load a repository above to start asking questions.'
                }
              />
            ) : (
              messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border ${
                      msg.role === 'user' ? 'bg-primary' : 'bg-muted'
                    }`}
                  >
                    {msg.role === 'user' ? (
                      <User className="h-4 w-4 text-primary-foreground" />
                    ) : (
                      <Bot className="h-4 w-4 text-accent" />
                    )}
                  </div>
                  <div
                    className={`max-w-[80%] rounded-lg border border-border p-3 text-sm ${
                      msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{msg.content || '...'}</div>
                    {msg.mode && msg.role === 'assistant' ? (
                      <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                        <span className="rounded bg-accent/20 px-1.5 py-0.5">{msg.mode}</span>
                        {msg.confidence ? (
                          <span className="rounded bg-accent/20 px-1.5 py-0.5">
                            {(msg.confidence * 100).toFixed(0)}%
                          </span>
                        ) : null}
                        {msg.supportingFiles?.slice(0, 3).map((f) => (
                          <span
                            key={f}
                            className="rounded bg-accent/20 px-1.5 py-0.5 truncate max-w-[150px]"
                          >
                            {f}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          <form
            className="flex items-center gap-2 border-t border-border p-3"
            onSubmit={handleSubmit}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                repoReady
                  ? 'Ask about architecture, functions, dependencies...'
                  : 'Load a repository first'
              }
              disabled={!repoReady || isStreaming}
              className="flex-1 h-10 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-accent disabled:opacity-50"
            />
            {isStreaming ? (
              <button
                type="button"
                onClick={stopStreaming}
                className="inline-flex h-10 items-center justify-center rounded-md bg-destructive px-4 text-sm font-medium text-destructive-foreground hover:bg-destructive/90"
              >
                Stop
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim() || !repoReady}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
              </button>
            )}
          </form>
        </div>
      </div>
    </section>
  );
}
