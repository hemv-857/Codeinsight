'use client';

import { MessageSquare, Plus, Trash2, X } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

export interface ConversationSession {
  id: string;
  repoName: string;
  questionCount: number;
  firstQuestion: string;
  timestamp: number;
}

const STORAGE_KEY = 'codeinsight-qa-history';

function loadHistory(): ConversationSession[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveHistory(sessions: ConversationSession[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  } catch {
    // localStorage full or unavailable
  }
}

interface ConversationHistoryProps {
  activeId: string | null;
  onSelect: (session: ConversationSession) => void;
  onNew: () => void;
  isOpen: boolean;
  onClose: () => void;
}

export function ConversationHistory({
  activeId,
  onSelect,
  onNew,
  isOpen,
  onClose,
}: ConversationHistoryProps) {
  const [sessions, setSessions] = useState<ConversationSession[]>([]);

  useEffect(() => {
    setSessions(loadHistory());
  }, []);

  const removeSession = useCallback((id: string) => {
    setSessions((prev) => {
      const next = prev.filter((s) => s.id !== id);
      saveHistory(next);
      return next;
    });
  }, []);

  if (!isOpen) return null;

  return (
    <div className="w-64 shrink-0 border-r border-border bg-card flex flex-col h-full">
      <div className="flex items-center justify-between p-3 border-b border-border">
        <span className="text-sm font-medium">History</span>
        <div className="flex gap-1">
          <button
            type="button"
            onClick={onNew}
            className="inline-flex h-7 w-7 items-center justify-center rounded-md hover:bg-muted transition-colors"
            title="New conversation"
          >
            <Plus className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-7 w-7 items-center justify-center rounded-md hover:bg-muted transition-colors"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-auto p-2 space-y-1">
        {sessions.length === 0 ? (
          <p className="text-xs text-muted-foreground p-2">No conversations yet.</p>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              className={`group flex items-start gap-2 rounded-md p-2 cursor-pointer transition-colors ${
                session.id === activeId ? 'bg-accent/20 border border-accent/30' : 'hover:bg-muted'
              }`}
              onClick={() => onSelect(session)}
            >
              <MessageSquare className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium truncate">{session.repoName}</p>
                <p className="text-[11px] text-muted-foreground truncate">
                  {session.firstQuestion}
                </p>
                <p className="text-[10px] text-muted-foreground">
                  {session.questionCount} question{session.questionCount !== 1 ? 's' : ''} &middot;{' '}
                  {new Date(session.timestamp).toLocaleDateString()}
                </p>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeSession(session.id);
                }}
                className="opacity-0 group-hover:opacity-100 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded hover:bg-destructive/20 transition-all"
              >
                <Trash2 className="h-3 w-3 text-destructive" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export function useConversationHistory() {
  const [sessions, setSessions] = useState<ConversationSession[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    setSessions(loadHistory());
  }, []);

  const startNew = useCallback(() => {
    setActiveId(null);
  }, []);

  const saveSession = useCallback(
    (repoName: string, firstQuestion: string, questionCount: number) => {
      setSessions((prev) => {
        const existing = prev.find((s) => s.id === activeId);
        let next: ConversationSession[];
        if (existing) {
          next = prev.map((s) =>
            s.id === activeId
              ? { ...s, repoName, questionCount, firstQuestion, timestamp: Date.now() }
              : s,
          );
        } else {
          const newSession: ConversationSession = {
            id: crypto.randomUUID(),
            repoName,
            questionCount,
            firstQuestion,
            timestamp: Date.now(),
          };
          next = [newSession, ...prev];
          setActiveId(newSession.id);
        }
        saveHistory(next);
        return next;
      });
    },
    [activeId],
  );

  return { sessions, activeId, setActiveId, startNew, saveSession };
}
