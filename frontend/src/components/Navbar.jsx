import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Layers, History, CreditCard, Sparkles, Menu, X, MessageSquare } from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '../AuthContext';

export default function Navbar() {
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  const { currentUser, login, logout } = useAuth();

  const navLinks = [
    { name: 'Dashboard', path: '/', icon: Layers },
    { name: 'History', path: '/history', icon: History },
    { name: 'Pricing', path: '/pricing', icon: CreditCard },
    { name: 'Feedback', path: '/feedback', icon: MessageSquare },
  ];

  return (
    <nav className="bg-dark-800 border-b border-dark-700 sticky top-0 z-50 shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-brand-500" />
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-brand-400 to-brand-600">
              QuizViral AI
            </span>
          </div>
          
          {/* Desktop Menu */}
          <div className="hidden md:flex items-center gap-4">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={clsx(
                    'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200',
                    isActive 
                      ? 'bg-brand-900/50 text-brand-400' 
                      : 'text-gray-300 hover:bg-dark-700 hover:text-white'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {link.name}
                </Link>
              );
            })}
            
            {/* Desktop Auth Buttons */}
            {currentUser ? (
              <div className="flex items-center gap-3 ml-4 border-l border-dark-600 pl-4">
                <span className="text-sm text-gray-300 font-medium truncate max-w-[150px]">
                  {currentUser.email}
                </span>
                <button 
                  onClick={logout}
                  className="bg-dark-700 hover:bg-red-500/20 hover:text-red-400 text-gray-300 px-3 py-1.5 rounded-md text-sm font-medium transition-all"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <button 
                onClick={login}
                className="ml-4 bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 rounded-md text-sm font-bold shadow-lg shadow-brand-500/25 transition-all flex items-center gap-2"
              >
                Login / Sign In
              </button>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-gray-300 hover:text-white focus:outline-none focus:ring-2 focus:ring-brand-500 rounded-md p-2"
            >
              {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden bg-dark-800 border-t border-dark-700">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  onClick={() => setIsOpen(false)}
                  className={clsx(
                    'flex items-center gap-2 px-3 py-3 rounded-md text-base font-medium transition-all duration-200',
                    isActive 
                      ? 'bg-brand-900/50 text-brand-400' 
                      : 'text-gray-300 hover:bg-dark-700 hover:text-white'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  {link.name}
                </Link>
              );
            })}
            
            {/* Mobile Auth Buttons */}
            <div className="border-t border-dark-700 pt-4 pb-2 mt-4 px-3">
              {currentUser ? (
                <div className="flex flex-col gap-3">
                  <span className="text-sm text-gray-400">Signed in as {currentUser.email}</span>
                  <button 
                    onClick={() => { logout(); setIsOpen(false); }}
                    className="w-full bg-dark-700 text-left text-red-400 px-3 py-2 rounded-md font-medium"
                  >
                    Sign Out
                  </button>
                </div>
              ) : (
                <button 
                  onClick={() => { login(); setIsOpen(false); }}
                  className="w-full bg-brand-600 hover:bg-brand-500 text-white px-3 py-2 rounded-md font-bold text-center"
                >
                  Login / Sign In
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
