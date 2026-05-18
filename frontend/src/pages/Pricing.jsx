import { Check } from 'lucide-react';
import { useAuth } from '../AuthContext';

export default function Pricing() {
  const { isPremium, credits } = useAuth();

  const plans = [
    {
      name: 'Monthly Unlimited',
      price: '$4.99',
      period: '/mo',
      description: 'Generate unlimited videos for a month.',
      features: ['Unlimited bulk video generation', 'Bypass the 5 credits limit', 'Custom logo branding', '1080p high quality', 'Priority rendering speed'],
      cta: 'Subscribe Monthly',
      popular: false,
      gumroadLink: 'https://hamzaraeescarpet.gumroad.com/l/quizviral-ai'
    },
    {
      name: 'Yearly Unlimited',
      price: '$9.99',
      period: '/yr',
      description: 'Best value! Generate unlimited videos all year.',
      features: ['Everything in Monthly', 'Save over 80% compared to monthly', 'Cancel anytime', 'Premium templates unlock'],
      cta: 'Subscribe Yearly',
      popular: true,
      gumroadLink: 'https://hamzaraeescarpet.gumroad.com/l/quizviral-ai'
    }
  ];

  return (
    <div className="space-y-12 animate-in fade-in duration-500 py-8">
      <header className="text-center max-w-2xl mx-auto px-4">
        <h1 className="text-3xl md:text-4xl font-extrabold mb-4">Unlock Unlimited Generation</h1>
        <p className="text-lg md:text-xl text-gray-400">
          {isPremium 
            ? "You are currently on the Unlimited Premium Plan! Enjoy your unrestricted access."
            : `You have ${credits} credits remaining. Upgrade now to generate unlimited videos.`}
        </p>
      </header>

      <div className="flex flex-col md:flex-row justify-center gap-8 max-w-5xl mx-auto px-4 mt-8 md:mt-0">
        {plans.map((plan) => (
          <div 
            key={plan.name} 
            className={`relative rounded-2xl p-8 border w-full md:w-1/2 flex flex-col ${
              plan.popular 
                ? 'bg-dark-800 border-brand-500 shadow-2xl shadow-brand-500/20 transform md:-translate-y-4' 
                : 'bg-dark-800/50 border-dark-700'
            }`}
          >
            {plan.popular && (
              <div className="absolute top-0 right-1/2 translate-x-1/2 -translate-y-1/2 bg-gradient-to-r from-brand-600 to-brand-400 text-white px-3 py-1 rounded-full text-sm font-bold shadow-lg">
                Best Value
              </div>
            )}
            
            <div className="mb-8">
              <h3 className="text-xl font-bold text-gray-200 mb-2">{plan.name}</h3>
              <p className="text-gray-400 text-sm h-10">{plan.description}</p>
              <div className="mt-4 flex items-baseline text-5xl font-extrabold">
                {plan.price}
                {plan.period && <span className="ml-1 text-xl font-medium text-gray-400">{plan.period}</span>}
              </div>
            </div>

            <ul className="mb-8 space-y-4 flex-grow">
              {plan.features.map(feature => (
                <li key={feature} className="flex items-center gap-3 text-gray-300">
                  <div className="flex-shrink-0 w-5 h-5 rounded-full bg-brand-900/50 flex items-center justify-center text-brand-400">
                    <Check className="w-3 h-3" />
                  </div>
                  {feature}
                </li>
              ))}
            </ul>

            <a 
              href={plan.gumroadLink}
              target="_blank"
              rel="noopener noreferrer"
              className={`w-full py-3 rounded-xl font-bold transition-all text-center block ${
                isPremium 
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed pointer-events-none'
                  : plan.popular 
                    ? 'bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-500/25' 
                    : 'bg-dark-700 hover:bg-dark-600 text-white'
              }`}
            >
              {isPremium ? 'Currently Active' : plan.cta}
            </a>
            {!isPremium && (
              <p className="text-xs text-center text-gray-500 mt-3">
                After payment, your Google email will be upgraded within 24 hours. Contact admin for instant activation.
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
