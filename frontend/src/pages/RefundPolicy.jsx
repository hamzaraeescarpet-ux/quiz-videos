export default function RefundPolicy() {
  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
      <header className="text-center space-y-2">
        <h1 className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-brand-400 to-brand-600">
          Refund & Cancellation Policy
        </h1>
        <p className="text-gray-400">Last updated: May 2026</p>
      </header>

      <section className="bg-dark-800 p-6 md:p-8 rounded-2xl border border-dark-700 shadow-xl space-y-6 text-gray-300 text-sm md:text-base leading-relaxed">
        <h2 className="text-xl font-bold text-brand-300">Our Guarantee</h2>
        <p className="text-gray-200 font-medium">
          Since we offer a free trial tier to test the software, all paid subscription sales are final. No refunds will be issued after video quota usage. However, users can cancel their recurring subscription at any time with a single click from their dashboard to prevent future billing.
        </p>

        <h2 className="text-xl font-bold text-brand-300">cancellation Instructions</h2>
        <p>
          You can instantly cancel your premium plan membership at any time directly through the dashboard. There are absolutely no hidden fees, cancellation penalties, or contracts. Once cancelled, your premium access will continue until the end of your current billing period, and no further charges will be made.
        </p>
      </section>
    </div>
  );
}
