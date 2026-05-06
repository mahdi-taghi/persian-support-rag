import ChatInterface from '@/components/ChatInterface';

export default function Home() {
  return (
    <main
      className="min-h-screen bg-[#07090f] text-white [background:radial-gradient(circle_at_15%_20%,rgba(244,186,44,.15),transparent_36%),radial-gradient(circle_at_80%_10%,rgba(40,114,255,.16),transparent_34%),linear-gradient(125deg,#05070e_0%,#090f1e_52%,#070a12_100%)]"
      dir="rtl"
    >
      <div className="mx-auto w-full max-w-[1200px] px-4 py-10 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl pb-10">
          <div className="mb-5">
            <h1 className="text-2xl font-bold sm:text-3xl">چت پشتیبانی</h1>
            <p className="mt-2 text-sm text-white/70 sm:text-base">
              سوالات عمومی حساب، تراکنش و راهنمایی سریع کاربران
            </p>
          </div>
          <ChatInterface />
        </div>
      </div>
    </main>
  );
}
