import { useEffect } from 'react';
import { Check } from 'lucide-react';
import { useAuth } from '../AuthContext';

export default function Pricing() {
  const { currentUser, isPremium, credits, login } = useAuth();

  useEffect(() => {
    // Load Paddle.js dynamically
    const script = document.createElement('script');
    script.src = "https://cdn.paddle.com/paddle/v2/paddle.js";
    script.async = true;
    script.onload = () => {
      if (window.Paddle) {
        window.Paddle.Initialize({ 
          token: 'live_56eeba45e39e5067a60984c4aa6', // Set the secure public client token
          environment: 'production'
        });
      }
    };
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  const handleCheckout = (planType) => {
    if (!currentUser) {
      alert("Please login first to link your premium account!");
      login();
      return;
    }

    if (window.Paddle) {
      window.Paddle.Checkout.open({
        items: [
          {
            priceId: 'pri_01ksyx8mzzm3w41kxs3vdym7kr', // Paddle Price ID for $4.99
            quantity: 1
          }
        ],
        customer: {
          email: currentUser.email
        },
        customData: {
          email: currentUser.email,
          plan: planType
        }
      });
    } else {
      alert("Billing system is loading, please try again in a moment!");
    }
  };

  const plans = [
    {
      name: 'Monthly Unlimited',
      price: '$4.99',
      period: '/mo',
      description: 'Generate unlimited videos for a month.',
      features: ['Unlimited bulk video generation', 'Bypass the 5 credits limit', 'Custom logo branding', '1080p high quality', 'Priority rendering speed'],
      cta: 'Subscribe Monthly',
      popular: true,
      planType: 'monthly'
    },
    {
      name: 'Yearly Unlimited',
      price: '$49.99',
      period: '/yr',
      description: 'Best value! Generate unlimited videos all year.',
      features: ['Everything in Monthly', 'Save over 15% compared to monthly', 'Cancel anytime', 'Premium templates unlock'],
      cta: 'Subscribe Yearly',
      popular: false,
      planType: 'yearly' // Redirects to same standard payment or prompt for yearly
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
            : `You have ${credits} credits remaining today. Upgrade now to generate up to 100 videos every day!`}
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
              <div className="absolute top-0 right-1/2 translate-x-1/2 -translate-y-1/2 bg-gradient-to-r from-brand-600 to-brand-400 text-white px-3 py-1 rounded-full text-sm font-bold shadow-lg">
                Most Popular
              </div>
            )}
            
            <div className="mb-8">
              <h3 className="text-xl font-bold text-gray-200 mb-2">{plan.name}</h3>
              <p className="text-gray-400 text-sm h-10">{plan.description}</p>
              <div className="mt-4 flex items-baseline text-5xl font-extrabold text-white">
                {plan.price}
                {plan.period && <span className="ml-1 text-xl font-medium text-gray-400">{plan.period}</span>}
              </div>
            </div>

            <ul className="mb-8 space-y-4 flex-grow">
              {plan.features.map(feature => (
                <li key={feature} className="flex items-center gap-3 text-gray-300 text-sm">
                  <div className="flex-shrink-0 w-5 h-5 rounded-full bg-brand-900/50 flex items-center justify-center text-brand-400">
                    <Check className="w-3 h-3" />
                  </div>
                  {feature}
                </li>
              ))}
            </ul>

            <button 
              onClick={() => handleCheckout(plan.planType)}
              className={`w-full py-3 rounded-xl font-bold transition-all text-center block shadow ${
                isPremium 
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed pointer-events-none'
                  : plan.popular 
                    ? 'bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-500/25' 
                    : 'bg-dark-700 hover:bg-dark-600 text-white'
              }`}
            >
              {isPremium ? 'Currently Active' : plan.cta}
            </button>
            {!isPremium && (
              <p className="text-xs text-center text-gray-500 mt-3">
                Secure checkout powered by Paddle. Cancel anytime.
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
