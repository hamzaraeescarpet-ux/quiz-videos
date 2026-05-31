import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="bg-dark-850 border-t border-dark-700/80 mt-16 py-8">
      <div className="container mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-gray-400">
        <div>
          <p>© {new Date().getFullYear()} <span className="font-bold text-gray-200">QuizViral AI</span>. All rights reserved.</p>
        </div>
        <div className="flex flex-wrap items-center gap-6">
          <Link to="/about" className="hover:text-brand-400 transition-colors font-medium">About Us</Link>
          <Link to="/privacy" className="hover:text-brand-400 transition-colors font-medium">Privacy Policy</Link>
          <Link to="/terms" className="hover:text-brand-400 transition-colors font-medium">Terms of Service</Link>
          <Link to="/refunds" className="hover:text-brand-400 transition-colors font-medium">Refund Policy</Link>
          <Link to="/feedback" className="hover:text-brand-400 transition-colors font-medium text-brand-500 font-bold bg-brand-500/10 px-3 py-1.5 rounded-lg border border-brand-500/25">Feedback & Suggestions</Link>
        </div>
      </div>
    </footer>
  );
}
