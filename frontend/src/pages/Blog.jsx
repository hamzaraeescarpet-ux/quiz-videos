import { Link } from 'react-router-dom';
import { blogPosts } from '../data/blogPosts';
import { BookOpen, Calendar, Clock, ArrowRight } from 'lucide-react';

export default function Blog() {
  return (
    <div className="space-y-10 animate-in fade-in duration-500 py-8">
      {/* SEO metadata injected directly or handled in header */}
      <header className="px-2 flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-gray-200 dark:border-dark-700">
        <div className="space-y-2 max-w-2xl">
          <h1 id="blog-title" className="text-3xl md:text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-brand-400 to-brand-600">
            QuizViral Creator Blog
          </h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm md:text-base">
            Expert growth tips, ChatGPT prompts, and SEO tutorials to scale your viral faceless channels and drive traffic.
          </p>
        </div>
        
        {/* Product Hunt Badge */}
        <div className="flex-shrink-0 bg-white dark:bg-dark-800 border border-gray-200 dark:border-dark-700/60 p-4 rounded-xl flex items-center justify-between gap-4 max-w-sm">
          <div className="text-xs space-y-1">
            <h4 className="font-bold text-gray-950 dark:text-white">We are on Product Hunt! 🚀</h4>
            <p className="text-gray-500 dark:text-gray-400">Support our launch and check us out!</p>
          </div>
          <a 
            href="https://www.producthunt.com/products/quizviral-ai?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-quizviral-ai" 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-block hover:opacity-95 transition-opacity"
            id="ph-badge-blog-header"
          >
            <img 
              alt="QuizViral AI - Create 100+ Viral Faceless Videos in Just 1-Click! 🤖 | Product Hunt" 
              width="180" 
              height="39" 
              src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1169342&theme=light&t=1781246404032" 
              className="h-9 w-auto"
            />
          </a>
        </div>
      </header>

      {/* Blog Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {blogPosts.map((post) => (
          <article 
            key={post.slug}
            className="bg-white dark:bg-dark-800/40 border border-gray-200 dark:border-dark-700/60 rounded-2xl overflow-hidden flex flex-col justify-between hover:border-brand-500/50 hover:shadow-xl hover:shadow-brand-500/5 transition-all duration-300 group"
          >
            <div>
              {/* Blog Image */}
              <Link to={`/blog/${post.slug}`} className="block overflow-hidden relative aspect-video bg-dark-900/60 border-b border-gray-200 dark:border-dark-700/40">
                {/* Ambient Blurred Backdrop */}
                <img 
                  src={post.image} 
                  alt=""
                  className="absolute inset-0 w-full h-full object-cover blur-md opacity-30 scale-110 pointer-events-none"
                />
                {/* Centered Sharp Image */}
                <img 
                  src={post.image} 
                  alt={post.title}
                  className="relative z-10 w-full h-full object-contain group-hover:scale-102 transition-transform duration-300"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-dark-900/30 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-20" />
              </Link>

              {/* Card Body */}
              <div className="p-6 space-y-4">
                {/* Meta details */}
                <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-brand-500" />
                    {post.date}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-brand-500" />
                    {post.readTime}
                  </span>
                </div>

                {/* Title */}
                <h2 className="text-xl font-bold text-gray-950 dark:text-gray-100 group-hover:text-brand-500 dark:group-hover:text-brand-400 transition-colors line-clamp-2">
                  <Link to={`/blog/${post.slug}`}>{post.title}</Link>
                </h2>

                {/* Excerpt */}
                <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed line-clamp-3">
                  {post.excerpt}
                </p>
              </div>
            </div>

            {/* Card Footer */}
            <div className="p-6 pt-0">
              <Link 
                to={`/blog/${post.slug}`}
                className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-400 hover:text-brand-300 transition-colors group/btn"
              >
                Read Full Article
                <ArrowRight className="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" />
              </Link>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
