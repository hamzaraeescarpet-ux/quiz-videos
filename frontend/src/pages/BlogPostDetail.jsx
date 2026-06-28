import { useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { blogPosts } from '../data/blogPosts';
import { latestFbVideoUrl } from '../data/latestFbVideo';
import { Calendar, Clock, ChevronLeft, ArrowRight } from 'lucide-react';

export default function BlogPostDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const post = blogPosts.find(p => p.slug === slug);

  // Auto-scroll to top when loading a new post
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [slug]);

  // Set document title and meta description dynamically for SEO
  useEffect(() => {
    if (post) {
      document.title = `${post.title} | QuizViral AI Blog`;
      
      // Update meta description if element exists, or create it
      let metaDesc = document.querySelector('meta[name="description"]');
      if (!metaDesc) {
        metaDesc = document.createElement('meta');
        metaDesc.setAttribute('name', 'description');
        document.head.appendChild(metaDesc);
      }
      metaDesc.setAttribute('content', post.metaDescription);

      // Update meta keywords
      let metaKeywords = document.querySelector('meta[name="keywords"]');
      if (!metaKeywords) {
        metaKeywords = document.createElement('meta');
        metaKeywords.setAttribute('name', 'keywords');
        document.head.appendChild(metaKeywords);
      }
      metaKeywords.setAttribute('content', post.seoKeywords.join(', '));
    }
    
    return () => {
      // Restore defaults
      document.title = 'QuizViral AI - Create Viral Quiz Videos in 1-Click';
    };
  }, [post]);

  if (!post) {
    return (
      <div className="text-center py-20 space-y-6 animate-in fade-in duration-500">
        <h2 className="text-2xl font-bold text-red-400">Blog Post Not Found</h2>
        <p className="text-gray-400">The article you are looking for does not exist or has been moved.</p>
        <Link 
          to="/blog" 
          className="inline-flex items-center gap-1.5 px-5 py-2.5 bg-dark-800 hover:bg-dark-700 text-white rounded-xl border border-dark-750 font-semibold transition-all"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Blog
        </Link>
      </div>
    );
  }

  // Helper to parse inline **bold**, *italic*, [links](url)
  // Helper to parse inline **bold**, *italic*, [links](url)
  const parseInlineStyles = (text) => {
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
      
    // Bold: **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="text-gray-900 dark:text-white font-bold">$1</strong>');
    
    // Italic: *text*
    html = html.replace(/\*(.*?)\*/g, '<em class="italic text-gray-650 dark:text-gray-250">$1</em>');
    
    // Code: `code`
    html = html.replace(/`(.*?)`/g, '<code class="bg-dark-900 border border-dark-700 px-1.5 py-0.5 rounded font-mono text-sm text-brand-300">$1</code>');
    
    // Links: [text](url)
    html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-brand-400 hover:text-brand-300 underline font-semibold transition-all">$1</a>');
    
    return html;
  };

  // Simple Markdown Parser to render blocks beautifully in dark glassmorphism styling
  const renderContent = (markdownText) => {
    const blocks = markdownText.split('\n\n');
    return blocks.map((block, idx) => {
      block = block.trim();
      if (!block) return null;
      
      // Header 1: # Header
      if (block.startsWith('# ')) {
        return (
          <h1 key={idx} className="text-3xl md:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-brand-600 via-brand-500 to-indigo-600 dark:from-brand-300 dark:via-brand-400 dark:to-indigo-300 mt-12 mb-8 leading-tight tracking-tight border-b border-gray-200 dark:border-dark-700/60 pb-4">
            {block.slice(2)}
          </h1>
        );
      }
      
      // Header 2: ## Header
      if (block.startsWith('## ')) {
        return (
          <h2 key={idx} className="text-2xl md:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-brand-600 to-indigo-600 dark:from-brand-300 dark:to-indigo-300 mt-10 mb-5 border-l-4 border-brand-500 pl-4 tracking-tight leading-snug">
            {block.slice(3)}
          </h2>
        );
      }
      
      // Header 3: ### Header
      if (block.startsWith('### ')) {
        return (
          <h3 key={idx} className="text-xl md:text-2xl font-extrabold italic text-brand-600 dark:text-brand-400 mt-8 mb-4 tracking-tight">
            {block.slice(4)}
          </h3>
        );
      }
      
      // Bullet list: - Item 1\n- Item 2
      if (block.startsWith('- ') || block.startsWith('* ')) {
        const items = block.split('\n').map(item => item.replace(/^[-*]\s+/, ''));
        return (
          <ul key={idx} className="list-disc pl-6 my-5 space-y-2.5 text-gray-700 dark:text-gray-300 text-base md:text-lg">
            {items.map((item, i) => (
              <li key={i} dangerouslySetInnerHTML={{ __html: parseInlineStyles(item) }} />
            ))}
          </ul>
        );
      }
      
      // Number list: 1. Item 1\n2. Item 2
      if (/^\d+\.\s+/.test(block)) {
        const items = block.split('\n').map(item => item.replace(/^\d+\.\s+/, ''));
        return (
          <ol key={idx} className="list-decimal pl-6 my-5 space-y-2.5 text-gray-700 dark:text-gray-300 text-base md:text-lg">
            {items.map((item, i) => (
              <li key={i} dangerouslySetInnerHTML={{ __html: parseInlineStyles(item) }} />
            ))}
          </ol>
        );
      }
      
      // Blockquote: > text
      if (block.startsWith('> ')) {
        return (
          <blockquote key={idx} className="border-l-4 border-brand-500 bg-brand-500/5 px-5 py-4 rounded-r-2xl italic my-6 text-gray-800 dark:text-gray-200">
            {block.slice(2)}
          </blockquote>
        );
      }
      
      // Code block: ```javascript\ncode\n```
      if (block.startsWith('```')) {
        const lines = block.split('\n');
        const code = lines.slice(1, -1).join('\n');
        return (
          <pre key={idx} className="bg-dark-900 border border-dark-700/80 rounded-2xl p-5 my-6 overflow-x-auto text-sm font-mono text-brand-300 shadow-inner">
            <code>{code}</code>
          </pre>
        );
      }
      
      // Normal paragraph
      return (
        <p 
          key={idx} 
          className="text-gray-700 dark:text-gray-300 leading-relaxed mb-5 text-base md:text-lg"
          dangerouslySetInnerHTML={{ __html: parseInlineStyles(block) }}
        />
      );
    });
  };

  const schemaMarkup = {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": post.title,
    "image": [post.image],
    "datePublished": post.date ? new Date(post.date).toISOString() : new Date().toISOString(),
    "dateModified": post.date ? new Date(post.date).toISOString() : new Date().toISOString(),
    "author": [{
      "@type": "Person",
      "name": post.author || "QuizViral AI Team",
      "url": "https://quizviral-nine.vercel.app/"
    }],
    "publisher": {
      "@type": "Organization",
      "name": "QuizViral AI",
      "logo": {
        "@type": "ImageObject",
        "url": "https://quizviral-nine.vercel.app/favicon.svg"
      }
    },
    "description": post.metaDescription
  };

  return (
    <div className="animate-in fade-in duration-500 py-4 max-w-6xl mx-auto">
      {/* JSON-LD Article Schema Markup for Google Rich Cards */}
      <script type="application/ld+json">
        {JSON.stringify(schemaMarkup)}
      </script>
      {/* Back button */}
      <Link 
        to="/blog" 
        className="inline-flex items-center gap-1 text-sm font-bold text-gray-400 hover:text-brand-400 transition-colors mb-6 group"
      >
        <ChevronLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
        Back to Blog Listing
      </Link>
 
       <div className="flex flex-col lg:flex-row gap-10 items-start">
         
         {/* Main Content Card */}
         <article className="w-full lg:w-2/3 bg-white dark:bg-dark-800/20 border border-gray-200 dark:border-dark-700/50 rounded-3xl p-6 md:p-10 shadow-xl space-y-6">
           {/* Header image */}
           <div className="aspect-video w-full rounded-2xl overflow-hidden shadow-lg border border-gray-200 dark:border-dark-700/40 relative bg-dark-900 flex items-center justify-center">
             {/* Ambient Blurred Backdrop */}
             <img 
               src={post.image} 
               alt=""
               className="absolute inset-0 w-full h-full object-cover blur-lg opacity-30 scale-110 pointer-events-none"
             />
             {/* Centered Sharp Image */}
             <img 
               src={post.image} 
               alt={post.title} 
               className="relative z-10 w-full h-full object-contain"
             />
           </div>
 
           {/* Meta specs */}
           <div className="flex flex-wrap items-center gap-4 text-xs md:text-sm text-gray-500 dark:text-gray-400 pt-2 border-b border-gray-200 dark:border-dark-700/50 pb-4">
             <span className="flex items-center gap-1.5">
               <Calendar className="w-4 h-4 text-brand-500" />
               {post.date}
             </span>
             <span className="border-r border-gray-200 dark:border-dark-700 h-4" />
             <span className="flex items-center gap-1.5">
               <Clock className="w-4 h-4 text-brand-500" />
               {post.readTime}
             </span>
             <span className="border-r border-gray-200 dark:border-dark-700 h-4" />
             <span className="font-semibold text-brand-500 dark:text-brand-400">By {post.author}</span>
           </div>

           {/* Facebook Video Embed */}
           {latestFbVideoUrl && (
             <div className="my-6 aspect-video w-full rounded-2xl overflow-hidden border border-gray-200 dark:border-dark-700/40 shadow-md">
               <iframe
                 src={`https://www.facebook.com/plugins/video.php?height=314&href=${encodeURIComponent(latestFbVideoUrl)}&show_text=false&width=560`}
                 width="100%"
                 height="100%"
                 style={{ border: 'none', overflow: 'hidden' }}
                 scrolling="no"
                 frameBorder="0"
                 allowFullScreen={true}
                 allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"
                 title="Latest Facebook Video"
               ></iframe>
             </div>
           )}
 
           {/* Rendered content */}
           <div className="prose prose-invert max-w-none pt-2">
             {renderContent(post.content)}
           </div>

           {/* Social Share Section */}
           <div className="border-t border-b border-gray-200 dark:border-dark-700/50 py-6 my-8 flex flex-col sm:flex-row items-center justify-between gap-4">
             <div>
               <h4 className="font-bold text-gray-900 dark:text-white text-base">Share this guide with fellow creators!</h4>
               <p className="text-xs text-gray-500 dark:text-gray-400">Help others scale their faceless trivia channels.</p>
             </div>
             <div className="flex flex-wrap gap-2.5">
               {/* Twitter */}
               <a 
                 href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(post.title)}&url=${encodeURIComponent(window.location.href)}`} 
                 target="_blank" 
                 rel="noopener noreferrer"
                 className="p-2.5 rounded-xl bg-dark-800 hover:bg-dark-700 border border-dark-750 text-gray-200 hover:text-white transition-all flex items-center justify-center gap-2 text-xs font-semibold"
               >
                 <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                 Tweet
               </a>
               {/* Facebook */}
               <a 
                 href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(window.location.href)}`} 
                 target="_blank" 
                 rel="noopener noreferrer"
                 className="p-2.5 rounded-xl bg-[#1877F2]/10 hover:bg-[#1877F2]/20 border border-[#1877F2]/30 text-[#1877F2] dark:text-[#3b82f6] transition-all flex items-center justify-center gap-2 text-xs font-semibold"
               >
                 <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
                 Share
               </a>
               {/* WhatsApp */}
               <a 
                 href={`https://api.whatsapp.com/send?text=${encodeURIComponent(post.title + ' - ' + window.location.href)}`} 
                 target="_blank" 
                 rel="noopener noreferrer"
                 className="p-2.5 rounded-xl bg-[#25D366]/10 hover:bg-[#25D366]/20 border border-[#25D366]/30 text-[#25D366] transition-all flex items-center justify-center gap-2 text-xs font-semibold"
               >
                 <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946C.06 5.348 5.397.01 12.008.01c3.202.001 6.212 1.246 8.477 3.514 2.266 2.268 3.507 5.28 3.505 8.484-.004 6.657-5.34 11.997-11.953 11.997-2.005-.001-3.973-.502-5.724-1.455L0 24zm6.59-4.846c1.665.989 3.3 1.478 4.965 1.479 5.48.002 9.94-4.453 9.943-9.932.002-2.654-1.026-5.15-2.895-7.022C16.732 1.797 14.238.77 11.584.77c-5.49 0-9.957 4.461-9.96 9.94-.001 1.777.47 3.501 1.365 5.011L1.93 20.35l4.717-1.196z"/></svg>
                 WhatsApp
               </a>
               {/* Copy Link */}
               <button 
                 onClick={() => {
                   navigator.clipboard.writeText(window.location.href);
                   alert("Article link copied to clipboard! 📋");
                 }}
                 className="p-2.5 rounded-xl bg-brand-500/10 hover:bg-brand-500/20 border border-brand-500/30 text-brand-400 hover:text-brand-300 transition-all flex items-center justify-center gap-2 text-xs font-semibold"
               >
                 Copy Link
               </button>
             </div>
           </div>
 
           {/* Bottom callout inside blog content with site links and PH badge */}
           <div className="bg-brand-500/5 border border-brand-500/20 rounded-2xl p-6 mt-10 space-y-4">
             <div className="space-y-1.5">
               <h3 className="font-bold text-gray-950 dark:text-white text-lg">Scale Your Content with AI Video Automation</h3>
               <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                 Take the manual work out of creating viral faceless quiz videos. Simply write your trivia questions, download a CSV, and let QuizViral AI render dozens of finished high-retention short videos in seconds!
               </p>
             </div>
             <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2 border-t border-brand-500/10">
               <Link 
                 to="/" 
                 className="w-full sm:w-auto px-5 py-2.5 bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-700 hover:to-brand-650 text-white font-bold rounded-xl text-center shadow-lg shadow-brand-500/20 text-sm transition-all"
               >
                 Try QuizViral AI for Free
               </Link>
               <div className="flex-shrink-0">
                 <a 
                   href="https://www.producthunt.com/products/quizviral-ai?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-quizviral-ai" 
                   target="_blank" 
                   rel="noopener noreferrer"
                   className="inline-block hover:opacity-95 transition-opacity"
                   id="ph-badge-blog-footer"
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
             </div>
           </div>
         </article>
 
         {/* Sidebar */}
         <aside className="w-full lg:w-1/3 space-y-6 sticky top-24">
           {/* Product Hunt Sidebar card */}
           <div className="bg-white dark:bg-dark-800/30 border border-gray-200 dark:border-dark-700/60 rounded-3xl p-6 space-y-4 shadow-md">
             <h3 className="font-bold text-gray-900 dark:text-white text-lg flex items-center gap-2">
               🔥 Support Our Launch!
             </h3>
             <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">
               We are live on Product Hunt! Check out our features, read creator reviews, and support our community space by clicking the badge below:
             </p>
             <div className="pt-2 flex justify-center lg:justify-start">
               <a 
                 href="https://www.producthunt.com/products/quizviral-ai?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-quizviral-ai" 
                 target="_blank" 
                 rel="noopener noreferrer"
                 className="inline-block hover:scale-[1.02] active:scale-98 transition-all"
                 id="ph-badge-blog-sidebar"
               >
                 <img 
                   alt="QuizViral AI - Create 100+ Viral Faceless Videos in Just 1-Click! 🤖 | Product Hunt" 
                   width="250" 
                   height="54" 
                   src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1169342&theme=light&t=1781246404032" 
                 />
               </a>
             </div>
           </div>
 
           {/* Sidebar Links */}
           <div className="bg-white dark:bg-dark-800/30 border border-gray-200 dark:border-dark-700/60 rounded-3xl p-6 space-y-4 shadow-md">
             <h3 className="font-bold text-gray-900 dark:text-white text-lg">
               📚 Related Articles
             </h3>
             <ul className="space-y-3">
               {blogPosts.filter(p => p.slug !== slug).map(p => (
                 <li key={p.slug}>
                   <Link 
                     to={`/blog/${p.slug}`}
                     className="group block space-y-1"
                   >
                     <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 group-hover:text-brand-500 dark:group-hover:text-brand-400 transition-colors line-clamp-2">
                       {p.title}
                     </h4>
                     <span className="text-xs text-gray-500 font-medium">{p.readTime}</span>
                   </Link>
                 </li>
               ))}
             </ul>
           </div>
         </aside>
 
       </div>
     </div>
  );
}
