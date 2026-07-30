import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { blogPosts } from './src/data/blogPosts.js';
import niches from './src/data/niches.js';

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

  // 3. Generate Tool Landing Pages
  const TOOLS_DATA_DIR = path.join(__dirname, 'public', 'data', 'tool-pages');
  const TOOLS_OUTPUT_DIR = path.join(DIST_DIR, 'tools');

  if (fs.existsSync(TOOLS_DATA_DIR)) {
    console.log(`Starting pre-rendering of ${niches.length} tool landing pages...`);

    niches.forEach(niche => {
      const dataPath = path.join(TOOLS_DATA_DIR, `${niche.slug}.json`);
      if (!fs.existsSync(dataPath)) {
        console.log(`  SKIP: Data file not found for ${niche.slug}`);
        return;
      }

      let toolData;
      try {
        toolData = JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
      } catch (e) {
        console.log(`  ERROR: Failed to parse data for ${niche.slug}`);
        return;
      }

      const toolDir = path.join(TOOLS_OUTPUT_DIR, niche.slug);
      if (!fs.existsSync(toolDir)) {
        fs.mkdirSync(toolDir, { recursive: true });
      }

      const title = `${toolData.niche} Quiz Maker - Create ${toolData.niche} Trivia Videos | QuizViral AI`;
      const desc = `Create engaging ${toolData.niche.toLowerCase()} quiz videos with QuizViral AI. Bulk generate faceless trivia videos with ${toolData.niche.toLowerCase()} questions for YouTube Shorts, TikTok, and Instagram Reels.`;

      const heroHtml = `
        <div class="max-w-6xl mx-auto px-4 py-8">
          <section class="text-center space-y-6 py-12">
            <h1 class="text-4xl md:text-5xl lg:text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-brand-600 leading-tight">
              ${toolData.hero_headline}
            </h1>
            <p class="text-lg md:text-xl text-gray-500 dark:text-gray-400 max-w-3xl mx-auto">
              Turn your ${toolData.niche.toLowerCase()} knowledge into viral short-form videos. QuizViral AI generates
              hundreds of ${toolData.niche.toLowerCase()} quiz videos from a single CSV upload — ready for YouTube Shorts, TikTok, and Instagram Reels.
            </p>
            <div class="flex gap-4 justify-center pt-4">
              <a href="/" class="inline-block px-8 py-4 bg-gradient-to-r from-brand-600 to-brand-400 text-white font-bold text-lg rounded-xl hover:from-brand-500 hover:to-brand-300 transition-all shadow-lg shadow-brand-500/20">
                ${toolData.cta}
              </a>
            </div>
          </section>

          <section class="bg-white dark:bg-dark-800/20 border border-gray-200 dark:border-dark-700/50 rounded-3xl p-8 md:p-12 my-16">
            <h2 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-8 text-center">
              How to Create ${toolData.niche} Quiz Videos
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div class="text-center space-y-3">
                <div class="w-14 h-14 bg-brand-500/10 text-brand-500 rounded-2xl flex items-center justify-center mx-auto text-2xl font-bold">1</div>
                <h3 class="font-bold text-lg">Upload Your Questions</h3>
                <p class="text-gray-500 dark:text-gray-400 text-sm">
                  Add your ${toolData.niche.toLowerCase()} trivia questions via CSV, PDF, or type them directly in our editor.
                </p>
              </div>
              <div class="text-center space-y-3">
                <div class="w-14 h-14 bg-brand-500/10 text-brand-500 rounded-2xl flex items-center justify-center mx-auto text-2xl font-bold">2</div>
                <h3 class="font-bold text-lg">Customize Your Style</h3>
                <p class="text-gray-500 dark:text-gray-400 text-sm">
                  Pick colors, backgrounds, music, and voiceover style that matches your ${toolData.niche.toLowerCase()} theme.
                </p>
              </div>
              <div class="text-center space-y-3">
                <div class="w-14 h-14 bg-brand-500/10 text-brand-500 rounded-2xl flex items-center justify-center mx-auto text-2xl font-bold">3</div>
                <h3 class="font-bold text-lg">Generate & Publish</h3>
                <p class="text-gray-500 dark:text-gray-400 text-sm">
                  Generate 100+ videos in one click and export them ready for YouTube Shorts, TikTok, and Reels.
                </p>
              </div>
            </div>
          </section>

          ${toolData.example_questions ? `
          <section class="my-16">
            <h2 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-8 text-center">
              Sample ${toolData.niche} Quiz Questions
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              ${toolData.example_questions.map((q, i) => `
                <div class="bg-white dark:bg-dark-800/20 border border-gray-200 dark:border-dark-700/50 rounded-2xl p-6 space-y-4">
                  <div class="flex items-center gap-2 text-sm text-brand-500 font-semibold">
                    <span class="w-6 h-6 rounded-full bg-brand-500/10 flex items-center justify-center text-xs font-bold">${i + 1}</span>
                    Question ${i + 1}
                  </div>
                  <p class="font-semibold text-gray-900 dark:text-white">${q.question}</p>
                  <div class="grid grid-cols-2 gap-2">
                    ${q.options.map(opt => `
                      <div class="text-xs md:text-sm px-3 py-2 rounded-lg border ${opt === q.answer ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700 text-green-700 dark:text-green-300 font-semibold' : 'bg-gray-50 dark:bg-dark-900/40 border-gray-200 dark:border-dark-700 text-gray-600 dark:text-gray-400'}">
                        ${opt}${opt === q.answer ? ' ✓' : ''}
                      </div>
                    `).join('')}
                  </div>
                </div>
              `).join('')}
            </div>
          </section>
          ` : ''}

          <section class="bg-gradient-to-br from-brand-600 to-brand-800 rounded-3xl p-8 md:p-12 text-center text-white space-y-6 my-16">
            <h2 class="text-3xl md:text-4xl font-extrabold">
              Ready to Create ${toolData.niche} Quiz Videos?
            </h2>
            <p class="text-lg text-white/80 max-w-2xl mx-auto">
              Join thousands of creators using QuizViral AI to generate faceless quiz videos on autopilot.
              No editing skills needed.
            </p>
            <div class="pt-2">
              <a href="/" class="inline-block px-10 py-4 bg-white text-brand-700 font-bold text-lg rounded-xl hover:bg-gray-100 transition-all shadow-lg">
                ${toolData.cta}
              </a>
            </div>
          </section>

          ${toolData.faq ? `
          <section class="my-16">
            <h2 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-8 text-center">
              ${toolData.niche} Quiz Maker - FAQ
            </h2>
            <div class="max-w-3xl mx-auto space-y-4">
              ${toolData.faq.map(item => `
                <details class="bg-white dark:bg-dark-800/20 border border-gray-200 dark:border-dark-700/50 rounded-xl overflow-hidden group">
                  <summary class="px-6 py-4 font-semibold text-gray-900 dark:text-white cursor-pointer hover:bg-gray-50 dark:hover:bg-dark-800/40 transition-colors flex items-center justify-between">
                    <span>${item.question}</span>
                    <svg class="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </summary>
                  <div class="px-6 pb-4 text-gray-600 dark:text-gray-400 leading-relaxed">
                    ${item.answer}
                  </div>
                </details>
              `).join('')}
            </div>
          </section>
          ` : ''}
        </div>
      `;

      let toolHtml = templateHtml
        .replace('<title>QuizViral AI - Create 100+ Viral Quiz Videos in 1-Click</title>', `<title>${title}</title>`)
        .replace('<div id="root"></div>', `<div id="root">${heroHtml}</div>`);

      const metaTags = `
      <meta name="description" content="${desc}" />
      <meta name="keywords" content="${toolData.niche.toLowerCase()}, quiz maker, trivia videos, faceless content, ${toolData.niche.toLowerCase()} quiz, youtube shorts" />
      <meta property="og:type" content="website" />
      <meta property="og:title" content="${title}" />
      <meta property="og:description" content="${desc}" />
      <meta property="og:url" content="https://quizviral-nine.vercel.app/tools/${niche.slug}" />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content="${title}" />
      <meta name="twitter:description" content="${desc}" />
      <link rel="canonical" href="https://quizviral-nine.vercel.app/tools/${niche.slug}" />
      <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          "name": "QuizViral AI - ${toolData.niche} Quiz Maker",
          "description": "Create engaging ${toolData.niche.toLowerCase()} quiz videos in minutes with QuizViral AI. Bulk generate faceless trivia videos for YouTube Shorts, TikTok, and Instagram Reels.",
          "applicationCategory": "MultimediaApplication",
          "operatingSystem": "Web",
          "offers": {
            "@type": "Offer",
            "price": "9.99",
            "priceCurrency": "USD"
          },
          "url": "https://quizviral-nine.vercel.app/tools/${niche.slug}"
        }
      </script>
      `;

      toolHtml = toolHtml.replace('</head>', `${metaTags}\n</head>`);

      fs.writeFileSync(path.join(toolDir, 'index.html'), toolHtml, 'utf-8');
      console.log(`  Generated pre-rendered tool page: /tools/${niche.slug}`);
    });

    console.log(`Tool page pre-rendering finished!`);
  } else {
    console.log(`SKIP: Tool pages data directory not found at ${TOOLS_DATA_DIR}`);
  }
}

runPrerender();
