import ChatInterface from '@/components/ChatInterface';

export default function Home() {
  return (
    <main
      className="min-h-screen bg-[#07090f] text-white [background:radial-gradient(circle_at_20%_20%,rgba(244,186,44,.18),transparent_35%),radial-gradient(circle_at_80%_10%,rgba(40,114,255,.18),transparent_30%),linear-gradient(125deg,#05070e_0%,#0a1020_50%,#080a12_100%)]"
      dir="rtl"
    >
      <div className="mx-auto w-full max-w-[1100px] px-4 py-10 sm:px-6 lg:px-8">
        <div className="pb-10">
          <div className="mb-4">
            <h2 className="text-2xl font-bold">چت پشتیبانی</h2>
            <p className="mt-1 text-white/70">سوالات عمومی حساب و تراکنش</p>
          </div>
          <ChatInterface />
        </div>
      </div>
    </main>
  );
}
