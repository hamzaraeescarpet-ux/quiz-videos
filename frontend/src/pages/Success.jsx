import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { CheckCircle, XCircle, Sparkles, Home, AlertTriangle } from 'lucide-react';

export default function Success() {
  const { refreshUserStatus } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const status = searchParams.get('status');

  useEffect(() => {
    // If the payment failed, skip Facebook Pixel purchase tracking and sync status checks
    if (status === 'failed') {
      setLoading(false);
      return;
    }

    // 1. Track Purchase in Facebook Pixel
    const plan = searchParams.get('plan') || 'monthly';
    const value = plan === 'yearly' ? 19.99 : 9.99;
    
    if (window.fbq) {
      window.fbq('track', 'Purchase', {
        value: value,
        currency: 'USD',
        content_name: plan === 'yearly' ? 'Yearly Unlimited' : 'Monthly Unlimited',
        content_category: 'Subscription'
      });
    }

    // 2. Refresh user status in the background
    const syncStatus = async () => {
      // Small delay to allow webhook to execute first
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await refreshUserStatus();
      setLoading(false);
    };

    syncStatus();
  }, [refreshUserStatus, searchParams, status]);

  if (status === 'failed') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] px-4 text-center animate-in fade-in duration-500">
        <div className="bg-white dark:bg-dark-800 p-8 md:p-12 rounded-3xl border border-gray-200 dark:border-dark-700 shadow-2xl max-w-md w-full relative overflow-hidden">
          {/* Decorative background glow */}
          <div className="absolute -top-10 -left-10 w-40 h-40 bg-red-500/10 rounded-full blur-2xl pointer-events-none"></div>
          <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-red-500/10 rounded-full blur-2xl pointer-events-none"></div>

          <div className="flex justify-center mb-6">
            <div className="p-4 bg-red-500/10 rounded-full border border-red-500/20 text-red-500 animate-bounce">
              <XCircle className="w-16 h-16" />
            </div>
          </div>

          <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white mb-2">
            Payment Failed!
          </h1>
          <p className="text-red-600 dark:text-red-400 font-semibold mb-6 flex items-center justify-center gap-1.5">
            <AlertTriangle className="w-4 h-4" /> Transaction Declined <AlertTriangle className="w-4 h-4" />
          </p>

          <p className="text-gray-600 dark:text-gray-300 text-sm mb-8 leading-relaxed">
            We were unable to process your payment. This could be due to insufficient funds, strict local verification, or an invalid card number.
            <span className="block mt-2 font-medium text-gray-400">Your account was not upgraded. Please check your card or try again.</span>
          </p>

          <div className="flex flex-col gap-3">
            <button
              onClick={() => navigate('/pricing')}
              className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-red-600 to-red-500 hover:from-red-700 hover:to-red-600 text-white font-bold transition-all flex items-center justify-center gap-2 shadow-lg shadow-red-500/25"
            >
              Try Again
            </button>
            <button
              onClick={() => navigate('/')}
              className="w-full py-3 px-6 rounded-xl border border-gray-200 dark:border-dark-700 text-gray-700 dark:text-gray-200 font-bold hover:bg-gray-50 dark:hover:bg-dark-700 transition-all flex items-center justify-center gap-2"
            >
              <Home className="w-4 h-4" /> Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] px-4 text-center animate-in fade-in duration-500">
      <div className="bg-white dark:bg-dark-800 p-8 md:p-12 rounded-3xl border border-gray-200 dark:border-dark-700 shadow-2xl max-w-md w-full relative overflow-hidden">
        {/* Decorative background glow */}
        <div className="absolute -top-10 -left-10 w-40 h-40 bg-green-500/10 rounded-full blur-2xl pointer-events-none"></div>
        <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-brand-500/10 rounded-full blur-2xl pointer-events-none"></div>

        <div className="flex justify-center mb-6">
          <div className="p-4 bg-green-500/10 rounded-full border border-green-500/20 text-green-500 animate-bounce">
            <CheckCircle className="w-16 h-16" />
          </div>
        </div>

        <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white mb-2">
          Payment Successful!
        </h1>
        <p className="text-brand-600 dark:text-brand-400 font-semibold mb-6 flex items-center justify-center gap-1.5">
          <Sparkles className="w-4 h-4" /> Welcome to Premium! <Sparkles className="w-4 h-4" />
        </p>

        <p className="text-gray-600 dark:text-gray-300 text-sm mb-8 leading-relaxed">
          Thank you for subscribing to QuizViral AI. Your account is being upgraded. 
          {loading ? (
            <span className="block mt-2 font-medium text-brand-500 animate-pulse">Updating your account, please wait...</span>
          ) : (
            <span className="block mt-2 font-medium text-green-500">Account successfully upgraded!</span>
          )}
        </p>

        <div className="bg-gray-50 dark:bg-dark-900/50 rounded-2xl p-4 text-left border border-gray-100 dark:border-dark-700/50 mb-8 space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-semibold text-gray-400 uppercase">Your Premium Perks:</div>
          <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
            <span className="text-green-500">✓</span> Unlimited Video Generation
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
            <span className="text-green-500">✓</span> Upload Custom Logos
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
            <span className="text-green-500">✓</span> High-speed Rendering Priority
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
            <span className="text-green-500">✓</span> Full Access to Premium Templates
          </div>
        </div>

        <button
          onClick={() => navigate('/')}
          className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-brand-600 to-brand-400 text-white font-bold hover:from-brand-500 hover:to-brand-300 transition-all flex items-center justify-center gap-2 shadow-lg shadow-brand-500/25"
        >
          <Home className="w-4 h-4" /> Back to Dashboard
        </button>
      </div>
    </div>
  );
}
