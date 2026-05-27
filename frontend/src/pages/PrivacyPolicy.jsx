export default function PrivacyPolicy() {
  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
      <header className="text-center space-y-2">
        <h1 className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-brand-400 to-brand-600">
          Privacy Policy
        </h1>
        <p className="text-gray-400">Last updated: May 2026</p>
      </header>

      <section className="bg-dark-800 p-6 md:p-8 rounded-2xl border border-dark-700 shadow-xl space-y-6 text-gray-300 text-sm md:text-base leading-relaxed">
        <h2 className="text-xl font-bold text-brand-300">1. Information We Collect</h2>
        <p>
          QuizViral AI collects minimal user information necessary to provide video automation services. This includes your email and profile name obtained via Google Authentication. We also save local storage parameters for active daily quota limits.
        </p>
        
        <h2 className="text-xl font-bold text-brand-300">2. Cookies & Advertising</h2>
        <p>
          We use strictly necessary cookies to keep you signed in. We also leverage third-party advertising partners like Google AdSense to monetize our platform. AdSense may use cookies to serve personalized advertisements based on your visits to our website and other websites across the Internet.
        </p>

        <h2 className="text-xl font-bold text-brand-300">3. Data Protection</h2>
        <p>
          Your login records are managed securely via Firebase. The CSV/PDF files and dynamic background videos you upload are stored securely on our systems, processed in real-time, and custom assets are automatically deleted immediately after compilation to guarantee maximum privacy.
        </p>

        <h2 className="text-xl font-bold text-brand-300">4. Third-Party Links</h2>
        <p>
          Our site includes links to third-party services. We are not responsible for the privacy practices or contents of those external platforms. We encourage users to read the privacy statements of every website they visit.
        </p>
      </section>
    </div>
  );
}
