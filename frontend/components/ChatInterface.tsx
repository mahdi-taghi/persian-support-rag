'use client';

import { useEffect, useRef, useState } from 'react';
import Message from './Message';

interface MessageRow {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  isHandoff?: boolean;
  handoffReason?: string;
}

function apiMessageUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_ORIGIN?.replace(/\/$/, '');
  if (base) {
    return `${base}/api/chat/message/`;
  }
  if (process.env.NODE_ENV === 'development') {
    return 'http://127.0.0.1:8000/api/chat/message/';
  }
  throw new Error('NEXT_PUBLIC_API_ORIGIN is required');
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<MessageRow[]>([
    {
      id: 'welcome',
      text: "سلام چجوری میتونم کمکتون کنم؟",
      sender: 'assistant',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: MessageRow = {
      id: Date.now().toString(),
      text: input,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(apiMessageUrl(), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input }),
      });

      if (!response.ok) {
        throw new Error('bad_status');
      }

      const data = await response.json();
      const assistantMessage: MessageRow = {
        id: String(Date.now() + 1),
        text: data.answer,
        sender: 'assistant',
        timestamp: new Date(),
        isHandoff: data.handoff_required || false,
        handoffReason: data.handoff_reason || '',
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: String(Date.now() + 1),
          text: 'ارتباط برقرار نشد؛ یک بار دیگر امتحان کنید.',
          sender: 'assistant',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="mx-auto flex h-[700px] w-full max-w-4xl flex-col overflow-hidden rounded-3xl border border-white/15 bg-[#0b1120]/90 shadow-[0_20px_90px_rgba(8,14,30,.65)] backdrop-blur">
      <header className="border-b border-white/10 bg-gradient-to-r from-[#0f172a] via-[#121b31] to-[#182038] p-5 text-white">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold tracking-tight">پشتیبانی تبدیل</h2>
            <p className="mt-1 text-sm text-white/70">پاسخ‌گویی سریع به سوالات حساب و تراکنش</p>
          </div>
          <span className="inline-flex items-center rounded-full border border-emerald-300/30 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-200">
            آنلاین
          </span>
        </div>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto bg-[#0a0f1d] px-4 py-5 sm:px-5">
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="rounded-2xl border border-white/15 bg-white/5 px-4 py-3 shadow-sm backdrop-blur-sm">
              <div className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-white/70 [animation-delay:0ms]" />
                <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-white/70 [animation-delay:180ms]" />
                <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-white/70 [animation-delay:360ms]" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t border-white/10 bg-[#0f1628]/95 p-4 sm:p-5">
        <div className="flex items-end gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="پیام خود را بنویسید..."
            className="min-h-12 flex-1 rounded-xl border border-white/15 bg-[#0b1120] px-4 py-3 text-right text-white placeholder:text-white/40 outline-none transition focus:border-yellow-300/60 focus:ring-2 focus:ring-yellow-300/40"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="min-h-12 rounded-xl bg-yellow-400 px-6 py-3 font-bold text-black transition hover:bg-yellow-300 disabled:cursor-not-allowed disabled:bg-slate-500"
          >
            ارسال
          </button>
        </div>
      </form>
    </section>
  );
}
