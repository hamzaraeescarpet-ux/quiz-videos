import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import nichesData from '../data/niches.js';

const BASE_URL = 'https://quizviral-nine.vercel.app';

export default function ToolLandingPage() {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const nicheInfo = nichesData.find(n => n.slug === slug);

  useEffect(() => {
    fetch(`/data/tool-pages/${slug}.json`)
      .then(res => {
        if (!res.ok) throw new Error('Not found');
        return res.json();
      })
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, [slug]);

  useEffect(() => {
    if (!data) return;

    const schema = {
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      "name": `QuizViral AI - ${data.niche} Quiz Maker`,
      "description": `Create engaging ${data.niche.toLowerCase()} quiz videos in minutes with QuizViral AI. Bulk generate faceless trivia videos for YouTube Shorts, TikTok, and Instagram Reels.`,
      "applicationCategory": "MultimediaApplication",
      "operatingSystem": "Web",
      "browserRequirements": "Modern web browser",
      "offers": {
        "@type": "Offer",
        "price": "9.99",
        "priceCurrency": "USD",
        "description": "Monthly premium subscription for unlimited quiz video generation"
      },
      "url": `${BASE_URL}/tools/${data.slug}-quiz-maker`
    };

    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.textContent = JSON.stringify(schema);
    script.id = 'software-schema';
    document.head.appendChild(script);

    const title = `${data.niche} Quiz Maker - Create ${data.niche} Trivia Videos | QuizViral AI`;
    const desc = `Create engaging ${data.niche.toLowerCase()} quiz videos with QuizViral AI. Bulk generate faceless trivia videos with ${data.niche.toLowerCase()} questions for YouTube Shorts, TikTok, and Instagram Reels. ${data.hero_headline}`;
    const canonical = `${BASE_URL}/tools/${data.slug}-quiz-maker`;

    document.title = title;
    let metaDesc = document.querySelector('meta[name="description"]');
    if (!metaDesc) {
      metaDesc = document.createElement('meta');
      metaDesc.name = 'description';
      document.head.appendChild(metaDesc);
    }
    metaDesc.content = desc;

    let ogTitle = document.querySelector('meta[property="og:title"]');
    if (!ogTitle) {
      ogTitle = document.createElement('meta');
      ogTitle.setAttribute('property', 'og:title');
      document.head.appendChild(ogTitle);
    }
    ogTitle.content = title;

    let ogDesc = document.querySelector('meta[property="og:description"]');
    if (!ogDesc) {
      ogDesc = document.createElement('meta');
      ogDesc.setAttribute('property', 'og:description');
      document.head.appendChild(ogDesc);
    }
    ogDesc.content = desc;

    let ogUrl = document.querySelector('meta[property="og:url"]');
    if (!ogUrl) {
      ogUrl = document.createElement('meta');
      ogUrl.setAttribute('property', 'og:url');
      document.head.appendChild(ogUrl);
    }
    ogUrl.content = canonical;

    let canonicalLink = document.querySelector('link[rel="canonical"]');
    if (!canonicalLink) {
      canonicalLink = document.createElement('link');
      canonicalLink.rel = 'canonical';
      document.head.appendChild(canonicalLink);
    }
    canonicalLink.href = canonical;

    return () => {
      const oldSchema = document.getElementById('software-schema');
      if (oldSchema) oldSchema.remove();
    };
  }, [data, slug]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center max-w-md">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Tool Page Not Found</h1>
          <p className="text-gray-500 mb-6">The tool page you're looking for doesn't exist or has been moved.</p>
          <Link to="/" className="inline-block px-6 py-3 bg-brand-500 text-white rounded-xl font-semibold hover:bg-brand-400 transition-colors">Go to Quiz Maker</Link>
        </div>
      </div>
    );
  }

  const nicheLower = data.niche.toLowerCase();

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-16">
      {/* Hero Section */}
      <section className="text-center space-y-6 py-12">
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-brand-600 leading-tight">
          {data.hero_headline}
        </h1>
        <p className="text-lg md:text-xl text-gray-500 dark:text-gray-400 max-w-3xl mx-auto">
          Turn your {nicheLower} knowledge into viral short-form videos. QuizViral AI generates 
          hundreds of {nicheLower} quiz videos from a single CSV upload — ready for YouTube Shorts, TikTok, and Instagram Reels.
        </p>
        <div className="flex gap-4 justify-center pt-4">
          <Link
            to="/"
            className="px-8 py-4 bg-gradient-to-r from-brand-600 to-brand-400 text-white font-bold text-lg rounded-xl hover:from-brand-500 hover:to-brand-300 transition-all shadow-lg shadow-brand-500/20"
          >
            {data.cta}
          </Link>
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-white dark:bg-dark-800/20 border border-gray-200 dark:border-dark-700/50 rounded-3xl p-8 md:p-12">
        <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-8 text-center">
          How to Create {data.niche} Quiz Videos
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center space-y-3">
            <div className="w-14 h-14 bg-brand-500/10 text-brand-500 rounded-2xl flex items-center justify-center mx-auto text-2xl font-bold">1</div>
            <h3 className="font-bold text-lg">Upload Your Questions</h3>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              Add your {nicheLower} trivia questions via CSV, PDF, or type them directly in our editor.
            </p>
          </div>
          <div className="text-center space-y-3">
            <div className="w-14 h-14 bg-brand-500/10 text-brand-500 rounded-2xl flex items-center justify-center mx-auto text-2xl font-bold">2</div>
            <h3 className="font-bold text-lg">Customize Your Style</h3>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              Pick colors, backgrounds, music, and voiceover style that matches your {nicheLower} theme.
            </p>
          </div>
          <div className="text-center space-y-3">
            <div className="w-14 h-14 bg-brand-500/10 text-brand-500 rounded-2xl flex items-center justify-center mx-auto text-2xl font-bold">3</div>
            <h3 className="font-bold text-lg">Generate & Publish</h3>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              Generate 100+ videos in one click and export them ready for YouTube Shorts, TikTok, and Reels.
            </p>
          </div>
        </div>
      </section>

      {/* Example Questions Preview */}
      {data.example_questions && data.example_questions.length > 0 && (
        <section>
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-8 text-center">
            Sample {data.niche} Quiz Questions
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {data.example_questions.map((q, i) => (
              <div key={i} className="bg-white dark:bg-dark-800/20 border border-gray-200 dark:border-dark-700/50 rounded-2xl p-6 space-y-4 hover:shadow-md transition-shadow">
                <div className="flex items-center gap-2 text-sm text-brand-500 font-semibold">
                  <span className="w-6 h-6 rounded-full bg-brand-500/10 flex items-center justify-center text-xs font-bold">{i + 1}</span>
                  Question {i + 1}
                </div>
                <p className="font-semibold text-gray-900 dark:text-white">{q.question}</p>
                <div className="grid grid-cols-2 gap-2">
                  {q.options.map((opt, j) => (
                    <div
                      key={j}
                      className={`text-xs md:text-sm px-3 py-2 rounded-lg border ${
                        opt === q.answer
                          ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700 text-green-700 dark:text-green-300 font-semibold'
                          : 'bg-gray-50 dark:bg-dark-900/40 border-gray-200 dark:border-dark-700 text-gray-600 dark:text-gray-400'
                      }`}
                    >
                      {opt}
                      {opt === q.answer && ' ✓'}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* CTA Section */}
      <section className="bg-gradient-to-br from-brand-600 to-brand-800 rounded-3xl p-8 md:p-12 text-center text-white space-y-6">
        <h2 className="text-3xl md:text-4xl font-extrabold">
          Ready to Create {data.niche} Quiz Videos?
        </h2>
        <p className="text-lg text-white/80 max-w-2xl mx-auto">
          Join thousands of creators using QuizViral AI to generate faceless quiz videos on autopilot.
          No editing skills needed.
        </p>
        <div className="pt-2">
          <Link
            to="/"
            className="inline-block px-10 py-4 bg-white text-brand-700 font-bold text-lg rounded-xl hover:bg-gray-100 transition-all shadow-lg"
          >
            {data.cta}
          </Link>
        </div>
      </section>

      {/* FAQ Section */}
      {data.faq && data.faq.length > 0 && (
        <section>
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-8 text-center">
            {data.niche} Quiz Maker — FAQ
          </h2>
          <div className="max-w-3xl mx-auto space-y-4">
            {data.faq.map((item, i) => (
              <details
                key={i}
                className="bg-white dark:bg-dark-800/20 border border-gray-200 dark:border-dark-700/50 rounded-xl overflow-hidden group"
              >
                <summary className="px-6 py-4 font-semibold text-gray-900 dark:text-white cursor-pointer hover:bg-gray-50 dark:hover:bg-dark-800/40 transition-colors flex items-center justify-between">
                  <span>{item.question}</span>
                  <svg className="w-5 h-5 text-gray-400 group-open:rotate-180 transition-transform flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </summary>
                <div className="px-6 pb-4 text-gray-600 dark:text-gray-400 leading-relaxed">
                  {item.answer}
                </div>
              </details>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
