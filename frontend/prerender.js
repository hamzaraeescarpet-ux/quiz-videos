import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { blogPosts } from './src/data/blogPosts.js';

// Resolve paths
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DIST_DIR = path.join(__dirname, 'dist');
const TEMPLATE_PATH = path.join(DIST_DIR, 'index.html');

// Read Facebook latest video if it exists
let latestFbVideoUrl = "https://www.facebook.com/watch/?v=892872416450589";
try {
  const fbDataFile = path.join(__dirname, 'src', 'data', 'latestFbVideo.js');
  if (fs.existsSync(fbDataFile)) {
    const content = fs.readFileSync(fbDataFile, 'utf-8');
    const match = content.match(/latestFbVideoUrl\s*=\s*["']([^"']+)["']/);
    if (match) {
      latestFbVideoUrl = match[1];
    }
  }
} catch (e) {
  console.log("Could not read latestFbVideo.js, using default fallback:", e);
}

// Markdown parser helper for pre-rendering
function parseInlineStyles(text) {
  if (!text) return '';
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  
  // Bold: **text**
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-gray-900 dark:text-white">$1</strong>');
  // Italic: *text*
  html = html.replace(/\*(.*?)\*/g, '<em class="italic">$1</em>');
  // Code: `code`
  html = html.replace(/`(.*?)`/g, '<code class="bg-gray-100 dark:bg-dark-900 px-1.5 py-0.5 rounded font-mono text-sm text-brand-400">$1</code>');
  // Links: [text](url)
  html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" class="text-brand-500 hover:underline">$1</a>');
  
  return html;
}

function parseMarkdownToHtml(markdownText) {
  if (!markdownText) return '';
  const blocks = markdownText.split('\n\n');
  
  return blocks.map((block) => {
    block = block.trim();
    if (!block) return '';
    
    // Headers
    if (block.startsWith('# ')) {
      return `<h1 class="text-3xl md:text-5xl font-black text-gray-900 dark:text-white mt-8 mb-4 border-b pb-4">${parseInlineStyles(block.slice(2))}</h1>`;
    }
    if (block.startsWith('## ')) {
      return `<h2 class="text-2xl md:text-3xl font-black text-gray-900 dark:text-white mt-8 mb-4 border-l-4 border-brand-500 pl-4">${parseInlineStyles(block.slice(3))}</h2>`;
    }
    if (block.startsWith('### ')) {
      return `<h3 class="text-xl md:text-2xl font-extrabold text-brand-600 dark:text-brand-400 mt-6 mb-3">${parseInlineStyles(block.slice(4))}</h3>`;
    }
    
    // Bullet list
    if (block.startsWith('- ') || block.startsWith('* ')) {
      const items = block.split('\n').map(item => item.replace(/^[-*]\s+/, ''));
      const liItems = items.map(item => `<li class="my-1.5">${parseInlineStyles(item)}</li>`).join('');
      return `<ul class="list-disc pl-6 my-4 space-y-1 text-gray-700 dark:text-gray-300">${liItems}</ul>`;
    }
    
    // Numbered list
    if (/^\d+\.\s+/.test(block)) {
      const items = block.split('\n').map(item => item.replace(/^\d+\.\s+/, ''));
      const liItems = items.map(item => `<li class="my-1.5">${parseInlineStyles(item)}</li>`).join('');
      return `<ol class="list-decimal pl-6 my-4 space-y-1 text-gray-700 dark:text-gray-300">${liItems}</ol>`;
    }
    
    // Blockquote
    if (block.startsWith('> ')) {
      return `<blockquote class="border-l-4 border-brand-500 bg-brand-500/5 px-4 py-3 rounded-r-xl italic my-5 text-gray-800 dark:text-gray-200">${parseInlineStyles(block.slice(2))}</blockquote>`;
    }
    
    // Code block
    if (block.startsWith('```')) {
      const lines = block.split('\n');
      const code = lines.slice(1, -1).join('\n');
      return `<pre class="bg-gray-900 text-brand-300 border border-gray-800 rounded-xl p-4 my-5 overflow-x-auto text-sm font-mono"><code>${code}</code></pre>`;
    }
    
    // Tables
    if (block.includes('|') && block.split('\n')[1] && block.split('\n')[1].includes('-')) {
      const lines = block.trim().split('\n');
      const headers = lines[0].split('|').map(h => h.trim()).filter(h => h);
      const rows = lines.slice(2).map(r => r.split('|').map(c => c.trim()).filter(c => c));
      
      const ths = headers.map(h => `<th class="px-4 py-2 border-b border-gray-700 font-bold text-left">${h}</th>`).join('');
      const trs = rows.map(r => `<tr class="hover:bg-gray-50 dark:hover:bg-dark-800/40">${r.map(c => `<td class="px-4 py-2 border-b border-gray-700">${parseInlineStyles(c)}</td>`).join('')}</tr>`).join('');
      
      return `<div class="overflow-x-auto my-6"><table class="min-w-full text-sm text-gray-700 dark:text-gray-300 border-collapse"><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table></div>`;
    }
    
    // Default Paragraph
    return `<p class="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">${parseInlineStyles(block)}</p>`;
  }).join('\n');
}

// Generate pre-rendered site
function runPrerender() {
  if (!fs.existsSync(TEMPLATE_PATH)) {
    console.error(`Error: Template file not found at ${TEMPLATE_PATH}. Please run npm build first.`);
    process.exit(1);
  }

  const templateHtml = fs.readFileSync(TEMPLATE_PATH, 'utf-8');

  console.log(`Starting pre-rendering of ${blogPosts.length} blog posts...`);

  // 1. Generate Blog Listing Page (dist/blog/index.html)
  const blogListDir = path.join(DIST_DIR, 'blog');
  if (!fs.existsSync(blogListDir)) {
    fs.mkdirSync(blogListDir, { recursive: true });
  }

  const blogListingContent = `
    <div class="space-y-10 py-8 max-w-6xl mx-auto px-4">
      <header class="border-b border-gray-200 dark:border-dark-700 pb-6">
        <h1 class="text-3xl md:text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-brand-600">
          QuizViral Creator Blog
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-2 text-sm md:text-base">
          Expert growth tips, ChatGPT prompts, and SEO tutorials to scale your viral faceless channels and drive traffic.
        </p>
      </header>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-8">
        ${blogPosts.map(post => `
          <article class="bg-white dark:bg-dark-800/40 border border-gray-200 dark:border-dark-700/60 rounded-2xl overflow-hidden flex flex-col justify-between hover:shadow-xl transition-all">
            <div>
              <div class="aspect-video w-full bg-dark-900 overflow-hidden relative">
                <img src="${post.image}" alt="${post.title}" class="w-full h-full object-cover" />
              </div>
              <div class="p-6 space-y-3">
                <div class="flex gap-4 text-xs text-gray-500">
                  <span>${post.date}</span>
                  <span>${post.readTime}</span>
                </div>
                <h2 class="text-xl font-bold text-gray-950 dark:text-gray-100">
                  <a href="/blog/${post.slug}" class="hover:text-brand-500">${post.title}</a>
                </h2>
                <p class="text-gray-500 dark:text-gray-400 text-sm line-clamp-3">${post.excerpt}</p>
              </div>
            </div>
            <div class="p-6 pt-0">
              <a href="/blog/${post.slug}" class="text-sm font-semibold text-brand-400 hover:text-brand-300">Read Full Article &rarr;</a>
            </div>
          </article>
        `).join('')}
      </div>
    </div>
  `;

  let listHtml = templateHtml
    .replace('<title>QuizViral AI - Create 100+ Viral Quiz Videos in 1-Click</title>', '<title>QuizViral AI Creator Blog - Expert Growth Tips & SEO Guides</title>')
    .replace('<div id="root"></div>', `<div id="root">${blogListingContent}</div>`);

  // Ensure robots allow crawlers to find this index too
  fs.writeFileSync(path.join(blogListDir, 'index.html'), listHtml, 'utf-8');
  console.log(`Generated pre-rendered blog index page at dist/blog/index.html`);

  // 2. Generate Blog Post Detail Pages (dist/blog/[slug]/index.html)
  blogPosts.forEach(post => {
    const postDir = path.join(blogListDir, post.slug);
    if (!fs.existsSync(postDir)) {
      fs.mkdirSync(postDir, { recursive: true });
    }

    const fbVideoEmbed = latestFbVideoUrl ? `
      <div class="my-6 aspect-video w-full rounded-2xl overflow-hidden border border-gray-200 dark:border-dark-700/40 shadow-md">
        <iframe
          src="https://www.facebook.com/plugins/video.php?height=314&href=${encodeURIComponent(latestFbVideoUrl)}&show_text=false&width=560"
          width="100%"
          height="100%"
          style="border:none;overflow:hidden"
          scrolling="no"
          frameborder="0"
          allowfullscreen="true"
          allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"
          title="Latest Facebook Video"
        ></iframe>
      </div>
    ` : '';

    const postContentHtml = `
      <div class="py-4 max-w-6xl mx-auto px-4">
        <a href="/blog" class="inline-flex items-center gap-1 text-sm font-bold text-gray-400 hover:text-brand-400 transition-colors mb-6">
          &larr; Back to Blog Listing
        </a>
        <div class="flex flex-col lg:flex-row gap-10 items-start">
          <article class="w-full lg:w-2/3 bg-white dark:bg-dark-800/20 border border-gray-200 dark:border-dark-700/50 rounded-3xl p-6 md:p-10 shadow-xl space-y-6">
            <div class="aspect-video w-full rounded-2xl overflow-hidden shadow-lg border border-gray-200 dark:border-dark-700/40 relative bg-dark-900">
              <img src="${post.image}" alt="${post.title}" class="w-full h-full object-cover" />
            </div>
            
            <div class="flex items-center gap-4 text-xs md:text-sm text-gray-500 border-b pb-4">
              <span>${post.date}</span>
              <span class="border-r h-4"></span>
              <span>${post.readTime}</span>
              <span class="border-r h-4"></span>
              <span class="font-semibold text-brand-500">By ${post.author || 'QuizViral AI Team'}</span>
            </div>

            <!-- Facebook Video Embed -->
            ${fbVideoEmbed}

            <div class="prose prose-invert max-w-none pt-2">
              ${parseMarkdownToHtml(post.content)}
            </div>
          </article>
        </div>
      </div>
    `;

    // Replace Title
    let postHtml = templateHtml.replace(
      '<title>QuizViral AI - Create 100+ Viral Quiz Videos in 1-Click</title>',
      `<title>${post.title} | QuizViral AI Blog</title>`
    );

    // Replace <div id="root"></div> with our pre-rendered content
    postHtml = postHtml.replace(
      '<div id="root"></div>',
      `<div id="root">${postContentHtml}</div>`
    );

    // Inject Search Engine and Social Media Meta Tags
    const metaTags = `
    <meta name="description" content="${post.metaDescription || post.excerpt}" />
    <meta name="keywords" content="${(post.seoKeywords || []).join(', ')}" />
    <!-- Open Graph / Facebook Meta Tags -->
    <meta property="og:type" content="article" />
    <meta property="og:title" content="${post.title}" />
    <meta property="og:description" content="${post.metaDescription || post.excerpt}" />
    <meta property="og:image" content="${post.image}" />
    <meta property="og:url" content="https://quizviral-nine.vercel.app/blog/${post.slug}" />
    <!-- Twitter Meta Tags -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="${post.title}" />
    <meta name="twitter:description" content="${post.metaDescription || post.excerpt}" />
    <meta name="twitter:image" content="${post.image}" />
    `;

    postHtml = postHtml.replace('</head>', `${metaTags}\n</head>`);

    fs.writeFileSync(path.join(postDir, 'index.html'), postHtml, 'utf-8');
    console.log(`Generated pre-rendered detail page for: /blog/${post.slug}`);
  });

  console.log(`Pre-rendering finished successfully!`);
}

runPrerender();
