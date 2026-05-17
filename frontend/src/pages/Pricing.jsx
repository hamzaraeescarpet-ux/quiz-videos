import { Check } from 'lucide-react';

export default function Pricing() {
  const plans = [
    {
      name: 'Free Tier',
      price: '$0',
      description: 'Perfect to test the waters.',
      features: ['Up to 5 total videos', 'Standard background options', 'Watermarked output', '720p resolution'],
      cta: 'Current Plan',
      popular: false
    },
    {
      name: 'Pro Creator',
      price: '$29',
      period: '/mo',
      description: 'For consistent daily uploads.',
      features: ['Unlimited videos', 'Custom logo branding', '1080p high quality', 'Priority rendering speed', 'All premium templates'],
      cta: 'Upgrade to Pro',
      popular: true
    },
    {
      name: 'Agency',
      price: '$99',
      period: '/mo',
      description: 'For high volume channels.',
      features: ['Everything in Pro', 'Custom AI voices', 'API Access', 'Account manager'],
      cta: 'Contact Sales',
      popular: false
    }
  ];

  return (
    <div className="space-y-12 animate-in fade-in duration-500 py-8">
      <header className="text-center max-w-2xl mx-auto px-4">
        <h1 className="text-3xl md:text-4xl font-extrabold mb-4">Simple, transparent pricing</h1>
        <p className="text-lg md:text-xl text-gray-400">Scale your viral content factory without limits. Start for free.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto px-4 mt-8 md:mt-0">
        {plans.map((plan) => (
          <div 
            key={plan.name} 
            className={`relative rounded-2xl p-8 border ${
              plan.popular 
                ? 'bg-dark-800 border-brand-500 shadow-2xl shadow-brand-500/20 transform md:-translate-y-4' 
                : 'bg-dark-800/50 border-dark-700'
            } flex flex-col`}
          >
            {plan.popular && (
              <div className="absolute top-0 right-1/2 translate-x-1/2 -translate-y-1/2 bg-gradient-to-r from-brand-600 to-brand-400 text-white px-3 py-1 rounded-full text-sm font-bold shadow-lg">
                Most Popular
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

            <button 
              className={`w-full py-3 rounded-xl font-bold transition-all ${
                plan.popular 
                  ? 'bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-500/25' 
                  : 'bg-dark-700 hover:bg-dark-600 text-white'
              }`}
            >
              {plan.cta}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
