import { Check } from 'lucide-react';
import { useAuth } from '../AuthContext';

export default function Pricing() {
  const { currentUser, isPremium, credits, login } = useAuth();

  const handleCheckout = (planType) => {
    if (!currentUser) {
      alert("Please login first to link your premium account!");
      login();
      return;
    }

    // Track InitiateCheckout event in Facebook Pixel
    if (window.fbq) {
      window.fbq('track', 'InitiateCheckout', {
        value: planType === 'yearly' ? 19.99 : 9.99,
        currency: 'USD',
        content_name: planType === 'yearly' ? 'Yearly Unlimited' : 'Monthly Unlimited',
        content_category: 'Subscription'
      });
    }

    // =========================================================================
    // REPLACE THESE PLACEHOLDERS WITH YOUR DODO PAYMENTS CHECKOUT LINKS FROM THE DASHBOARD
    // Example: "https://checkout.dodopayments.com/buy/p_12345..."
    const DODO_MONTHLY_LINK = "https://checkout.dodopayments.com/buy/pdt_0NhJ9Hy2r0jliZi6RYOP3?quantity=1&redirect_url=https%3A%2F%2Fquizviral-nine.vercel.app%2Fsuccess";
    const DODO_YEARLY_LINK = "https://checkout.dodopayments.com/buy/pdt_0NhJ8B12iV14QguVLXSkD?quantity=1&redirect_url=https%3A%2F%2Fquizviral-nine.vercel.app%2Fsuccess";
    // =========================================================================

    const checkoutBaseUrl = planType === 'yearly' ? DODO_YEARLY_LINK : DODO_MONTHLY_LINK;

    if (checkoutBaseUrl.startsWith("YOUR_DODO_")) {
      alert("System upgrade in progress: Dodo Payments checkout links are not yet configured. Please provide the product links in the configuration.");
      return;
    }

    // Append the customer's email to pre-fill on Dodo Payments checkout screen
    const separator = checkoutBaseUrl.includes('?') ? '&' : '?';
    const checkoutUrl = `${checkoutBaseUrl}${separator}email=${encodeURIComponent(currentUser.email)}`;
    window.open(checkoutUrl, '_blank');
  };

  const plans = [
    {
      name: 'Monthly Unlimited',
      price: '$9.99',
      period: '/mo',
      description: 'Supercharge your content creation for a single month.',
      features: [
        '🎬 Unlimited Video Generation - Generate as many viral quiz videos as you want all month.',
        '⚡ No Credit Limits - Fully bypass the 5 daily credit limit for continuous creation.',
        '🎨 Custom Branding - Upload your own logo and remove all watermarks.',
        '📺 High Definition Render - Clean 1080p videos ready to post on TikTok, Reels, & Shorts.',
        '🚀 Priority Rendering Speed - Faster compile times compared to the free tier.'
      ],
      cta: 'Subscribe Monthly',
      popular: false,
      planType: 'monthly'
    },
    {
      name: 'Yearly Unlimited',
      price: '$19.99',
      period: '/yr',
      description: 'Pay for 2 months, get 12! Best value for creators.',
      features: [
        '🔥 Pay for 2 Months, Get 12! - Access the premium suite for an entire year (Save 83% instantly).',
        '🚀 VIP Priority Engine - The absolute fastest rendering queue with zero queue wait times.',
        '🎨 Elite Layout Pass - Full access to all premium templates, styles, and vertical backgrounds.',
        '💎 Massive Savings - Keep $50+ in your pocket compared to the monthly subscription.',
        '🌟 Complete Brand Ownership - Full custom branding, zero watermarks, and custom assets.',
        '👑 VIP Customer Care - Priority 24/7 dedicated support & direct feature requests to developers.'
      ],
      cta: 'Subscribe Yearly',
      popular: true,
      planType: 'yearly'
    }
  ];

  return (
    <div className="space-y-12 animate-in fade-in duration-500 py-8">
      <header className="text-center max-w-2xl mx-auto px-4">
        <h1 className="text-3xl md:text-4xl font-extrabold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-brand-400 to-brand-600">
          Unlock Unlimited Generation
        </h1>
        <p className="text-lg md:text-xl text-gray-400">
          {isPremium 
            ? "You are currently on the Unlimited Premium Plan! Enjoy your unrestricted access."
            : `You have ${credits} credits remaining today. Upgrade now to generate unlimited videos!`}
        </p>
      </header>

      <div className="flex flex-col md:flex-row justify-center gap-8 max-w-5xl mx-auto px-4 mt-8 md:mt-0">
        {plans.map((plan) => (
          <div 
            key={plan.name} 
            className={`relative rounded-2xl p-8 border w-full md:w-1/2 flex flex-col justify-between ${
              plan.popular 
                ? 'bg-dark-800 border-brand-500 shadow-2xl shadow-brand-500/20 transform md:-translate-y-4' 
                : 'bg-dark-800/50 border-dark-700'
            }`}
          >
            {plan.popular && (
              <div className="absolute top-0 right-1/2 translate-x-1/2 -translate-y-1/2 bg-gradient-to-r from-brand-600 to-brand-400 text-white px-4 py-1 rounded-full text-xs font-bold shadow-lg tracking-wide whitespace-nowrap">
                ✨ Most Popular - Save 83%
              </div>
            )}
            
            <div className="mb-8">
              <h3 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-2">{plan.name}</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm h-10">{plan.description}</p>
              <div className="mt-4 flex items-baseline text-5xl font-extrabold text-gray-900 dark:text-white">
                {plan.price}
                {plan.period && <span className="ml-1 text-xl font-medium text-gray-500 dark:text-gray-400">{plan.period}</span>}
              </div>
              {plan.planType === 'yearly' && (
                <div className="mt-3 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-xs font-semibold animate-pulse flex flex-col gap-1">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-red-500 animate-ping"></span>
                    <span>⚡ URGENT: Launch Deal Ending Tonight!</span>
                  </div>
                  <p className="text-gray-450 dark:text-gray-400 font-normal">
                    This $19.99/yr promotional price is only valid until 12:00 AM midnight tonight. Afterwards, it will increase to <strong>$99.99/yr</strong>.
                  </p>
                </div>
              )}
            </div>

            <ul className="mb-8 space-y-4 flex-grow">
              {plan.features.map(feature => {
                const parts = feature.split(' - ');
                return (
                  <li key={feature} className="flex items-start gap-3 text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-brand-100 dark:bg-brand-900/50 flex items-center justify-center text-brand-650 dark:text-brand-400 mt-0.5">
                      <Check className="w-3 h-3" />
                    </div>
                    <span>
                      {parts.length > 1 ? (
                        <>
                          <strong className="text-gray-900 dark:text-white font-semibold">{parts[0]}</strong> — <span className="text-gray-600 dark:text-gray-400">{parts[1]}</span>
                        </>
                      ) : (
                        feature
                      )}
                    </span>
                  </li>
                );
              })}
            </ul>

            <button 
              onClick={() => handleCheckout(plan.planType)}
              disabled={isPremium}
              className={`w-full py-3 rounded-xl font-bold transition-all text-center block border ${
                isPremium 
                  ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20 cursor-default'
                  : plan.popular 
                    ? 'bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-700 hover:to-brand-650 text-white border-brand-600 hover:border-brand-700 shadow-lg shadow-brand-500/25 transform active:scale-98' 
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-900 border-gray-200 dark:bg-dark-700 dark:hover:bg-dark-600 dark:text-white dark:border-dark-600 shadow-sm'
              }`}
            >
              {isPremium ? 'Currently Active ✓' : plan.cta}
            </button>
            {!isPremium && (
              <p className="text-xs text-center text-gray-500 mt-3">
                Secure checkout powered by Dodo Payments.
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

