interface MessageProps {
  message: {
    id: string;
    text: string;
    sender: 'user' | 'assistant';
    timestamp: Date;
    isHandoff?: boolean;
    handoffReason?: string;
  };
}

export default function Message({ message }: MessageProps) {
  const isUser = message.sender === 'user';
  const messageTime = message.timestamp.toLocaleTimeString('fa-IR', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[82%] rounded-2xl border px-4 py-3 shadow-sm transition ${
          isUser
            ? 'border-yellow-300/70 bg-gradient-to-br from-yellow-300 to-yellow-400 text-slate-900'
            : message.isHandoff
            ? 'border-orange-300/45 bg-orange-500/10 text-white backdrop-blur-sm'
            : 'border-white/15 bg-white/5 text-white backdrop-blur-sm'
        }`}
      >
        <p className={`text-sm leading-7 ${isUser ? 'text-slate-900' : 'text-white/90'}`}>
          {message.text}
        </p>
        {message.isHandoff && message.handoffReason && (
          <div className="mt-3 border-t border-orange-300/30 pt-2.5">
            <p className="text-xs text-orange-100">
              ارجاع به پشتیبان انسانی: {message.handoffReason}
            </p>
          </div>
        )}
        <p className={`mt-2 text-[11px] ${isUser ? 'text-slate-800/70' : 'text-white/50'}`}>
          {messageTime}
        </p>
      </div>
    </div>
  );
}
