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

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[78%] rounded-2xl border p-4 shadow-sm ${
          isUser
            ? 'border-yellow-200/60 bg-yellow-400 text-black'
            : message.isHandoff
            ? 'border-orange-300/40 bg-orange-200/10 text-white'
            : 'border-white/10 bg-white/5 text-white backdrop-blur'
        }`}
      >
        <p className={`text-sm leading-7 ${isUser ? 'text-black' : 'text-white/90'}`}>
          {message.text}
        </p>
        {message.isHandoff && message.handoffReason && (
          <div className="mt-2 border-t border-orange-300/30 pt-2">
            <p className="text-xs text-orange-200">ارجاع: {message.handoffReason}</p>
          </div>
        )}
        <p
          className={`text-xs mt-1 ${
            isUser ? 'text-black/60' : 'text-white/45'
          }`}
        >
          {message.timestamp.toLocaleTimeString('fa-IR', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  );
}
