"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// ─── Types ─────────────────────────────────────────────────────────────────

type Role = "user" | "assistant";

interface Message {
  id: string;
  role: Role;
  content: string;
  chip: string;
}

interface Tile {
  message_id: string;
  summary_chip: string;
  last_message_preview: string;
  updated_at: string;
}

// ─── Helpers ───────────────────────────────────────────────────────────────

const API = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text);
  }
  return res.json() as Promise<T>;
}

function uid() {
  return crypto.randomUUID();
}

// ─── Sub-components ────────────────────────────────────────────────────────

function TileItem({
  tile,
  active,
  onClick,
}: {
  tile: Tile;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-4 py-3 border-b border-zinc-800 transition-colors hover:bg-zinc-800 ${
        active ? "bg-zinc-800" : ""
      }`}
    >
      <span className="inline-block text-xs font-semibold bg-violet-600 text-white rounded-full px-2 py-0.5 mb-1 max-w-full truncate">
        {tile.summary_chip}
      </span>
      <p className="text-xs text-zinc-400 truncate">{tile.last_message_preview}</p>
    </button>
  );
}

interface ChatBubbleProps {
  message: Message;
}

function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-violet-600 flex items-center justify-center text-white text-xs font-bold mr-2 shrink-0 mt-1">
          C
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap break-words shadow ${
          isUser
            ? "bg-violet-600 text-white rounded-br-sm"
            : "bg-zinc-800 text-zinc-100 rounded-bl-sm"
        }`}
      >
        {message.content}
        {message.chip && (
          <span className="block mt-1 text-[10px] opacity-60 italic">
            {message.chip}
          </span>
        )}
      </div>
    </div>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────

export default function Home() {
  const [sessionId, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [tiles, setTiles] = useState<Tile[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const mediaRecRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // ── Init session ──────────────────────────────────────────────────────────

  useEffect(() => {
    const stored = sessionStorage.getItem("cyrus_session_id");
    if (stored) {
      setSessionId(stored);
      loadTiles(stored);
    } else {
      createSession();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function createSession() {
    try {
      const data = await apiFetch<{ session_id: string }>("/api/sessions", {
        method: "POST",
      });
      sessionStorage.setItem("cyrus_session_id", data.session_id);
      setSessionId(data.session_id);
    } catch (e) {
      setError("Could not reach the Cyrus AI backend. Is it running?");
      console.error(e);
    }
  }

  async function loadTiles(sid: string) {
    try {
      const data = await apiFetch<{ tiles: Tile[] }>(
        `/api/sessions/${sid}/tiles`
      );
      setTiles(data.tiles ?? []);
    } catch {
      // tiles fail silently on first load
    }
  }

  // ── Scroll to bottom ──────────────────────────────────────────────────────

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Send message ──────────────────────────────────────────────────────────

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || loading || !sessionId) return;
      setError(null);

      const userMsg: Message = {
        id: uid(),
        role: "user",
        content: text.trim(),
        chip: "",
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setLoading(true);

      try {
        const data = await apiFetch<{
          assistant_message: string;
          summary_chip: string;
        }>("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            message: text.trim(),
            locale: navigator.language?.split("-")[0] ?? "en",
          }),
        });

        const assistantMsg: Message = {
          id: uid(),
          role: "assistant",
          content: data.assistant_message,
          chip: data.summary_chip,
        };
        setMessages((prev) => [...prev, assistantMsg]);
        await loadTiles(sessionId);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "An error occurred.");
      } finally {
        setLoading(false);
      }
    },
    [loading, sessionId]
  );

  // ── Keyboard handler ──────────────────────────────────────────────────────

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  // ── Voice recording ───────────────────────────────────────────────────────

  async function startRecording() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const rec = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];
      rec.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      rec.start(200);
      mediaRecRef.current = rec;
      setRecording(true);
    } catch {
      setError("Microphone access denied. Please allow mic in browser settings.");
    }
  }

  async function stopRecording() {
    setRecording(false);
    const rec = mediaRecRef.current;
    if (!rec) return;

    await new Promise<void>((resolve) => {
      rec.onstop = () => resolve();
      rec.stop();
      rec.stream.getTracks().forEach((t) => t.stop());
    });

    const blob = new Blob(chunksRef.current, { type: "audio/webm" });
    const form = new FormData();
    form.append("audio", blob, "voice.webm");

    setLoading(true);
    try {
      const data = await apiFetch<{ text: string }>("/api/stt", {
        method: "POST",
        body: form,
      });
      const transcribed = data.text?.trim();
      if (transcribed) {
        setInput(transcribed);
        textareaRef.current?.focus();
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "STT error.");
    } finally {
      setLoading(false);
    }
  }

  // ── New chat ──────────────────────────────────────────────────────────────

  async function newChat() {
    sessionStorage.removeItem("cyrus_session_id");
    setMessages([]);
    setTiles([]);
    setInput("");
    setError(null);
    await createSession();
  }

  // ─────────────────────────────────────────────────────────────────────────

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100 overflow-hidden">
      {/* ── Sidebar overlay (mobile) ───────────────────────────────────────── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Sidebar ───────────────────────────────────────────────────────── */}
      <aside
        className={`
          fixed md:relative z-30 md:z-auto
          w-72 h-full flex flex-col
          bg-zinc-900 border-r border-zinc-800
          transform transition-transform duration-200
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
        `}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center text-white font-bold text-sm">
              C
            </div>
            <span className="font-semibold text-sm">Cyrus AI</span>
          </div>
          <button
            onClick={newChat}
            className="text-xs bg-zinc-800 hover:bg-zinc-700 px-2 py-1 rounded-md transition-colors"
          >
            + New
          </button>
        </div>

        {/* Tiles */}
        <div className="flex-1 overflow-y-auto">
          {tiles.length === 0 ? (
            <p className="text-center text-zinc-500 text-xs mt-8 px-4">
              Your conversation history will appear here.
            </p>
          ) : (
            tiles.map((tile) => (
              <TileItem
                key={tile.message_id}
                tile={tile}
                active={false}
                onClick={() => setSidebarOpen(false)}
              />
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-zinc-800 text-[10px] text-zinc-600 text-center">
          Cyrus AI v0.1 · Student MVP
        </div>
      </aside>

      {/* ── Main chat area ─────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center gap-3 px-4 py-3 border-b border-zinc-800 bg-zinc-900 shrink-0">
          <button
            className="md:hidden p-1 rounded-md hover:bg-zinc-800 transition-colors"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open sidebar"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-violet-600 flex items-center justify-center text-white text-[10px] font-bold">
              C
            </div>
            <span className="font-semibold text-sm">Cyrus AI</span>
          </div>
          {loading && (
            <span className="ml-auto text-xs text-zinc-400 animate-pulse">
              Thinking…
            </span>
          )}
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {messages.length === 0 && !loading && (
            <div className="flex flex-col items-center justify-center h-full text-center gap-3 text-zinc-500">
              <div className="w-16 h-16 rounded-2xl bg-violet-600 flex items-center justify-center text-3xl text-white font-bold shadow-lg">
                C
              </div>
              <p className="text-lg font-semibold text-zinc-300">
                Hi, I&apos;m Cyrus!
              </p>
              <p className="text-sm max-w-xs">
                Your AI coding assistant. Ask me anything — code, math, writing,
                and more.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <ChatBubble key={msg.id} message={msg} />
          ))}

          {loading && (
            <div className="flex justify-start mb-3">
              <div className="w-7 h-7 rounded-full bg-violet-600 flex items-center justify-center text-white text-xs font-bold mr-2 shrink-0 mt-1">
                C
              </div>
              <div className="bg-zinc-800 rounded-2xl rounded-bl-sm px-4 py-3">
                <span className="flex gap-1">
                  <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce [animation-delay:300ms]" />
                </span>
              </div>
            </div>
          )}

          {error && (
            <div className="mx-auto max-w-md bg-red-900/40 border border-red-700 text-red-300 text-xs rounded-xl px-4 py-2 mb-3 text-center">
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* ── Input bar ───────────────────────────────────────────────────── */}
        <div className="shrink-0 px-4 py-3 border-t border-zinc-800 bg-zinc-900">
          <div className="flex items-end gap-2 max-w-3xl mx-auto">
            {/* Voice record button (WhatsApp-style press-and-hold) */}
            <button
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onTouchStart={(e) => {
                e.preventDefault();
                startRecording();
              }}
              onTouchEnd={(e) => {
                e.preventDefault();
                stopRecording();
              }}
              disabled={loading}
              aria-label="Press and hold to record voice"
              className={`p-2.5 rounded-full transition-all shrink-0 ${
                recording
                  ? "bg-red-600 animate-pulse scale-110 shadow-lg shadow-red-700/50"
                  : "bg-zinc-700 hover:bg-zinc-600"
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <svg
                className="w-5 h-5"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M12 1a4 4 0 0 1 4 4v6a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4zm-1 14.93A7.001 7.001 0 0 1 5 9H3a9 9 0 0 0 8 8.94V21H9v2h6v-2h-2v-2.07A9 9 0 0 0 21 9h-2a7 7 0 0 1-6 6.93z" />
              </svg>
            </button>

            {/* Text input */}
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask Cyrus anything… (Enter to send, Shift+Enter for new line)"
              rows={1}
              disabled={loading}
              className="flex-1 resize-none bg-zinc-800 border border-zinc-700 rounded-2xl px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500 disabled:opacity-50 leading-relaxed max-h-36 overflow-y-auto"
              style={{ overflowY: "auto" }}
            />

            {/* Send button */}
            <button
              onClick={() => sendMessage(input)}
              disabled={loading || !input.trim()}
              aria-label="Send message"
              className="p-2.5 rounded-full bg-violet-600 hover:bg-violet-500 transition-colors shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            </button>
          </div>

          {recording && (
            <p className="text-center text-red-400 text-xs mt-1 animate-pulse">
              🔴 Recording… release to transcribe
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
