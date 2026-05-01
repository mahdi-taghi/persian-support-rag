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
    <div className="mx-auto flex h-[640px] w-full max-w-5xl flex-col overflow-hidden rounded-3xl border border-yellow-300/25 bg-[#0b1120]/95 shadow-[0_0_50px_rgba(244,186,44,.12)]">
      <div className="border-b border-white/10 bg-gradient-to-r from-[#0f172a] via-[#151d33] to-[#1c243c] p-4 text-white">
        <div>
          <h2 className="text-xl font-bold">پشتیبانی تبدیل</h2>
          <p className="text-sm text-white/70">چت آنلاین</p>
        </div>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto bg-[#0a0f1d] p-4">
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 shadow-sm backdrop-blur">
              <div className="flex space-x-2 space-x-reverse">
                <span className="h-2 w-2 animate-bounce rounded-full bg-yellow-300" />
                <span className="delay-100 h-2 w-2 animate-bounce rounded-full bg-yellow-300" />
                <span className="delay-200 h-2 w-2 animate-bounce rounded-full bg-yellow-300" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t border-white/10 bg-[#0f1628] p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="پیام…"
            className="flex-1 rounded-xl border border-white/15 bg-[#0b1120] p-3 text-right text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-yellow-300/70"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="rounded-xl bg-yellow-400 px-6 py-3 font-bold text-black transition hover:bg-yellow-300 disabled:cursor-not-allowed disabled:bg-gray-400"
          >
            ارسال
          </button>
        </div>
      </form>
    </div>
  );
}
