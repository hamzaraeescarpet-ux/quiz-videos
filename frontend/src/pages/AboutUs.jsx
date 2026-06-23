export default function AboutUs() {
  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
      <header className="text-center space-y-2">
        <h1 className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-brand-400 to-brand-600">
          About QuizViral AI
        </h1>
        <p className="text-gray-400">Revolutionizing dynamic video creation using advanced AI automation.</p>
      </header>

      <section className="bg-dark-800 p-6 md:p-8 rounded-2xl border border-dark-700 shadow-xl space-y-6">
        <h2 className="text-xl font-bold text-brand-300">Who We Are</h2>
        <p className="text-gray-300 text-sm md:text-base leading-relaxed">
          QuizViral AI is a cutting-edge software-as-a-service (SaaS) platform designed for content creators, marketers, educators, and social media enthusiasts who want to scale their video factories with zero manual work. 
        </p>
        <p className="text-gray-300 text-sm md:text-base leading-relaxed">
          We believe video automation should be accessible, lightning-fast, and premium. Our platform enables users to convert structured question data (from CSV and PDF) into gorgeous, engaging short trivia videos customized with high-end animations, game show layouts, logos, voiceovers, and dynamic background tracks in seconds.
        </p>
      </section>

      <section className="bg-dark-800 p-6 md:p-8 rounded-2xl border border-dark-700 shadow-xl space-y-6">
        <h2 className="text-xl font-bold text-brand-300">Key Technology Features</h2>
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm md:text-base text-gray-300">
          <li className="flex items-start gap-2 bg-dark-900/50 p-4 rounded-xl border border-dark-700">
            <span className="text-xl">🤖</span>
            <div>
              <strong className="text-white block">AI Voice Generation</strong>
              Professional neural voiceovers generated dynamically from questions text.
            </div>
          </li>
          <li className="flex items-start gap-2 bg-dark-900/50 p-4 rounded-xl border border-dark-700">
            <span className="text-xl">🎨</span>
            <div>
              <strong className="text-white block">Visual Customizer</strong>
              Vibrant box styling and color picking tools to align with any brand aesthetic.
            </div>
          </li>
          <li className="flex items-start gap-2 bg-dark-900/50 p-4 rounded-xl border border-dark-700">
            <span className="text-xl">⚡</span>
            <div>
              <strong className="text-white block">Bulk PDF / CSV Parsing</strong>
              Robust layout mapping filters to quickly read structured texts into data grids.
            </div>
          </li>
          <li className="flex items-start gap-2 bg-dark-900/50 p-4 rounded-xl border border-dark-700">
            <span className="text-xl">🍿</span>
            <div>
              <strong className="text-white block">Dynamic Overlays</strong>
              Rounded game capsules with reactive dims and correct answer highlights.
            </div>
          </li>
        </ul>
      </section>
    </div>
  );
}
