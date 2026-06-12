import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="bg-dark-850 border-t border-dark-700/80 mt-16 py-8">
      <div className="container mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-6 text-sm text-gray-400">
        <div className="flex flex-col items-center md:items-start gap-3">
          <p>© {new Date().getFullYear()} <span className="font-bold text-gray-200">QuizViral AI</span>. All rights reserved.</p>
          <a 
            href="https://www.producthunt.com/products/quizviral-ai?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-quizviral-ai" 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-block hover:opacity-90 transition-opacity"
            id="ph-badge-footer"
          >
            <img 
              alt="QuizViral AI - Create 100+ Viral Faceless Videos in Just 1-Click! 🤖 | Product Hunt" 
              width="150" 
              height="32" 
              src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1169342&theme=light&t=1781246404032" 
              className="h-8 w-auto"
            />
          </a>
        </div>
        <div className="flex flex-wrap items-center justify-center md:justify-end gap-6 text-center md:text-left">
          <Link to="/about" className="hover:text-brand-400 transition-colors font-medium">About Us</Link>
          <Link to="/blog" className="hover:text-brand-400 transition-colors font-medium">Blog</Link>
          <Link to="/privacy" className="hover:text-brand-400 transition-colors font-medium">Privacy Policy</Link>
          <Link to="/terms" className="hover:text-brand-400 transition-colors font-medium">Terms of Service</Link>
          <Link to="/refunds" className="hover:text-brand-400 transition-colors font-medium">Refund Policy</Link>
          <Link to="/feedback" className="hover:text-brand-400 transition-colors font-medium text-brand-500 font-bold bg-brand-500/10 px-3 py-1.5 rounded-lg border border-brand-500/25">Feedback & Suggestions</Link>
        </div>
      </div>
    </footer>
  );
}
