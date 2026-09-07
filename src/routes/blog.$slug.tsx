import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect, useMemo } from "react";
import { Nav, Footer } from "../components/layout";
import { blogPosts as fallbackPosts, BlogPost } from "../lib/blogData";
import { api } from "../lib/api";
import { safeFormatDateTime } from "../lib/formatDate";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";
import { Copy, Check } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/blog/$slug")({
  component: BlogPostDetailPage,
});

function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(code);
      setCopied(true);
      toast.success("Code copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="relative group my-6 rounded-[8px] border border-border bg-[#0d1117] text-gray-100 overflow-hidden font-mono">
      <div className="flex items-center justify-between px-4 py-2 bg-[#161b22] border-b border-gray-800 text-[11px] font-semibold text-gray-400 select-none">
        <span className="uppercase tracking-wider font-mono">{language || "code"}</span>
        <button
          onClick={handleCopy}
          type="button"
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-200 text-[11px] font-medium transition-colors cursor-pointer"
        >
          {copied ? (
            <>
              <Check className="size-3.5 text-emerald-400" />
              <span className="text-emerald-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="size-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-4 overflow-x-auto text-[13.5px] leading-relaxed select-text font-mono text-gray-100 max-w-full">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function renderMarkdownContent(content: string) {
  if (!content) return null;
  const elements: React.ReactNode[] = [];
  
  // Split into code block chunks and text chunks
  const codeBlockRegex = /```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  let keyCounter = 0;

  const processTextChunk = (text: string) => {
    const lines = text.split("\n");
    let inList = false;
    let listItems: string[] = [];

    const flushList = () => {
      if (inList && listItems.length > 0) {
        elements.push(
          <ul key={`ul-${keyCounter++}`} className="my-5 list-disc pl-6 space-y-2 text-foreground font-sans text-[17px] leading-[1.7]">
            {listItems.map((item, idx) => (
              <li key={idx} dangerouslySetInnerHTML={{ __html: formatInline(item) }} />
            ))}
          </ul>
        );
        listItems = [];
        inList = false;
      }
    };

    lines.forEach((line) => {
      const trimmed = line.trim();

      if (trimmed.startsWith("### ")) {
        flushList();
        elements.push(
          <h3 key={`h3-${keyCounter++}`} className="text-xl font-bold text-foreground mt-8 mb-3 font-sans tracking-tight">
            {trimmed.replace("### ", "")}
          </h3>
        );
      } else if (trimmed.startsWith("## ")) {
        flushList();
        elements.push(
          <h2 key={`h2-${keyCounter++}`} className="text-2xl font-bold text-primary mt-10 mb-4 font-sans tracking-tight border-b border-border pb-2">
            {trimmed.replace("## ", "")}
          </h2>
        );
      } else if (trimmed === "---") {
        flushList();
        elements.push(<hr key={`hr-${keyCounter++}`} className="my-8 border-border" />);
      } else if (trimmed.startsWith("- ") || trimmed.startsWith("1. ") || trimmed.startsWith("2. ") || trimmed.startsWith("3. ") || trimmed.startsWith("4. ") || trimmed.startsWith("5. ") || trimmed.startsWith("6. ") || trimmed.startsWith("7. ") || trimmed.startsWith("8. ") || trimmed.startsWith("9. ")) {
        inList = true;
        listItems.push(trimmed.replace(/^[-1234567890\.]+\s+/, ""));
      } else if (trimmed.length > 0) {
        flushList();
        elements.push(
          <p
            key={`p-${keyCounter++}`}
            className="my-4 text-[17px] leading-[1.7] text-foreground font-sans"
            dangerouslySetInnerHTML={{ __html: formatInline(trimmed) }}
          />
        );
      }
    });

    flushList();
  };

  const formatInline = (text: string) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/`([^`]+)`/g, "<code class='bg-muted px-1.5 py-0.5 rounded text-[13px] font-mono border border-border'>$1</code>")
      .replace(/\[(.*?)\]\((.*?)\)/g, "<a href='$2' class='text-[#0a5c38] dark:text-[#3fb68e] font-semibold underline hover:opacity-80'>$1</a>");
  };

  while ((match = codeBlockRegex.exec(content)) !== null) {
    const textBefore = content.substring(lastIndex, match.index);
    if (textBefore) {
      processTextChunk(textBefore);
    }

    const language = match[1] || "code";
    const code = match[2];
    elements.push(<CodeBlock key={`code-${keyCounter++}`} code={code} language={language} />);

    lastIndex = match.index + match[0].length;
  }

  const remainingText = content.substring(lastIndex);
  if (remainingText) {
    processTextChunk(remainingText);
  }

  return elements;
}

function BlogPostDetailPage() {
  const { slug } = Route.useParams();
  const fallback = fallbackPosts.find((p) => p.slug === slug) || fallbackPosts[0];
  const [post, setPost] = useState<BlogPost>(fallback);
  const [allPosts, setAllPosts] = useState<BlogPost[]>(fallbackPosts);

  useEffect(() => {
    async function loadData() {
      try {
        const [detailRes, listRes] = await Promise.all([
          api.getBlogPostDetail(slug),
          api.getBlogPosts(),
        ]);

        if (detailRes && detailRes.title) {
          setPost({
            id: detailRes.id,
            slug: detailRes.slug || slug,
            title: detailRes.title,
            excerpt: detailRes.excerpt || "",
            meta_description: detailRes.meta_description || detailRes.excerpt || "",
            date: safeFormatDateTime(detailRes.published_date || detailRes.created_at, "24 July 2026"),
            readTime: detailRes.read_time || (detailRes.reading_time ? `${detailRes.reading_time} min read` : "5 min read"),
            author: detailRes.author || "Shamsuddeen Yusuf",
            category: detailRes.category || "recruitment",
            category_display: detailRes.category_display || (detailRes.category === "tech" ? "Tech Guides" : "Recruitment Guides"),
            content: detailRes.body || detailRes.content || "",
          });
        }

        if (listRes && listRes.results && listRes.results.length > 0) {
          const mapped: BlogPost[] = listRes.results.map((p: any) => ({
            id: p.id,
            slug: p.slug,
            title: p.title,
            excerpt: p.excerpt || "",
            meta_description: p.meta_description,
            date: safeFormatDateTime(p.published_date || p.created_at, "24 July 2026"),
            readTime: p.read_time || `${p.reading_time || 5} min read`,
            author: p.author || "Shamsuddeen Yusuf",
            category: p.category || "recruitment",
            category_display: p.category_display || (p.category === "tech" ? "Tech Guides" : "Recruitment Guides"),
            content: p.body || p.content || "",
          }));
          setAllPosts(mapped);
        }
      } catch (e) {
        // Fallback to static post data
      }
    }
    loadData();
  }, [slug]);

  // Find two related posts from the same category
  const relatedPosts = useMemo(() => {
    const categoryName = (post.category || "").toLowerCase();
    const currentSlug = post.slug;

    const sameCategory = allPosts.filter((p) => {
      if (p.slug === currentSlug) return false;
      const cat = (p.category || "").toLowerCase();
      if (categoryName.includes("tech")) return cat.includes("tech");
      return cat.includes("recruitment") || cat.includes("scam") || cat.includes("directory") || !cat.includes("tech");
    });

    if (sameCategory.length >= 2) return sameCategory.slice(0, 2);

    // Fallback: fill with other posts if category has < 2 other items
    const rest = allPosts.filter((p) => p.slug !== currentSlug && !sameCategory.includes(p));
    return [...sameCategory, ...rest].slice(0, 2);
  }, [allPosts, post]);

  const isTechCategory = (post.category || "").toLowerCase().includes("tech");
  const categoryDisplay = isTechCategory ? "Tech Guides" : "Recruitment Guides";

  const blogArticleSchema = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "headline": post.title,
    "description": post.meta_description || post.excerpt,
    "datePublished": post.published_date || "2026-07-24T00:00:00Z",
    "author": {
      "@type": "Person",
      "name": "Shamsuddeen Yusuf",
      "url": "https://github.com/shamsuddeein"
    },
    "publisher": {
      "@type": "Organization",
      "name": "RecruitmentAlert",
      "url": "https://www.recruitmentalert.com.ng"
    }
  };

  const breadcrumbSchema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {
        "@type": "ListItem",
        "position": 1,
        "name": "Home",
        "item": "https://www.recruitmentalert.com.ng"
      },
      {
        "@type": "ListItem",
        "position": 2,
        "name": "Blog",
        "item": "https://www.recruitmentalert.com.ng/blog"
      },
      {
        "@type": "ListItem",
        "position": 3,
        "name": post.title,
        "item": `https://www.recruitmentalert.com.ng/blog/${post.slug}`
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between font-sans selection:bg-secondary/25">
      <SeoHead
        title={`${post.title} — RecruitmentAlert`}
        description={post.meta_description || post.excerpt}
        canonicalUrl={`/blog/${post.slug}`}
        jsonLd={[blogArticleSchema, breadcrumbSchema]}
      />
      <Nav />
      <main id="main-content" tabIndex={-1} className="flex-1 mx-auto max-w-[960px] w-full px-4 sm:px-6 py-12 outline-none">
        
        <div className="max-w-[680px] mx-auto mb-6">
          <BackButton to="/blog" label="Back to Blog" />
        </div>

        {/* Breadcrumb */}
        <div className="mb-6 font-mono text-xs uppercase tracking-wide text-muted-foreground max-w-[680px] mx-auto">
          <Link to="/" className="hover:text-primary">Home</Link> &rarr; <Link to="/blog" className="hover:text-primary">Blog</Link> &rarr; {categoryDisplay}
        </div>

        {/* Header */}
        <div className="space-y-4 border-b border-border pb-8 text-left max-w-[680px] mx-auto">
          <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-muted-foreground">
            <span
              className={`px-2.5 py-1 rounded font-bold uppercase tracking-wider text-[11px] ${
                isTechCategory
                  ? "bg-purple-100 dark:bg-purple-950/50 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800"
                  : "bg-[#0a5c38]/10 dark:bg-[#3fb68e]/10 text-[#0a5c38] dark:text-[#3fb68e] border border-[#0a5c38]/20 dark:border-[#3fb68e]/20"
              }`}
            >
              {categoryDisplay}
            </span>
            <span>&middot;</span>
            <span>{post.readTime}</span>
            <span>&middot;</span>
            <span>By Shamsuddeen Yusuf</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-primary leading-tight font-sans">
            {post.title}
          </h1>
          {post.excerpt && (
            <p className="text-sm sm:text-base text-muted-foreground font-sans leading-relaxed">
              {post.excerpt}
            </p>
          )}
        </div>

        {/* Article Body - max 680px, font 17px, line height 1.7 */}
        <article className="py-8 font-sans max-w-[680px] mx-auto text-[17px] leading-[1.7]">
          {renderMarkdownContent(post.content || post.body || "")}
        </article>

        {/* Author Bio Card */}
        <div className="mt-12 max-w-[680px] mx-auto rounded-[8px] border border-border bg-card p-6 space-y-3">
          <div className="flex items-center gap-3">
            <div className="size-10 rounded-full bg-[#0a5c38] dark:bg-[#3fb68e] text-white dark:text-[#0c1015] flex items-center justify-center font-bold text-sm font-mono shrink-0">
              SY
            </div>
            <div>
              <h4 className="text-sm font-bold text-foreground">Written by Shamsuddeen Yusuf</h4>
              <p className="text-xs text-muted-foreground font-sans mt-0.5">
                Software Engineer & Founder of RecruitmentAlert. Building real-time monitoring infrastructure for 42 Nigerian federal government portals.
              </p>
            </div>
          </div>
        </div>

        {/* Related Posts Section */}
        {relatedPosts.length > 0 && (
          <section className="mt-16 pt-10 border-t border-border max-w-[680px] mx-auto space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-primary font-sans">Related Articles</h3>
              <Link to="/blog" className="text-xs font-semibold text-[#0a5c38] dark:text-[#3fb68e] hover:underline font-mono">
                View all guides &rarr;
              </Link>
            </div>

            <div className="grid gap-6 sm:grid-cols-2">
              {relatedPosts.map((rel) => (
                <article
                  key={rel.slug}
                  className="group flex flex-col justify-between rounded-[8px] border border-border bg-card p-5 interactive-card hover:border-[#0a5c38]/50 dark:hover:border-[#3fb68e]/50"
                >
                  <div className="space-y-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider font-mono text-muted-foreground">
                      {(rel.category || "").toLowerCase().includes("tech") ? "Tech Guides" : "Recruitment Guides"}
                    </span>
                    <h4 className="text-sm font-bold text-foreground group-hover:text-primary transition-colors leading-snug line-clamp-2">
                      <Link to="/blog/$slug" params={{ slug: rel.slug }}>
                        {rel.title}
                      </Link>
                    </h4>
                  </div>
                  <div className="mt-4 pt-3 border-t border-border/40 flex items-center justify-between text-[11px] text-muted-foreground">
                    <span>{rel.readTime || `${rel.reading_time || 5} min read`}</span>
                    <Link
                      to="/blog/$slug"
                      params={{ slug: rel.slug }}
                      className="text-[#0a5c38] dark:text-[#3fb68e] font-semibold hover:underline"
                    >
                      Read &rarr;
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}

        {/* Footer Navigation */}
        <div className="mt-12 pt-6 border-t border-border flex flex-wrap items-center justify-between gap-4 text-xs font-semibold max-w-[680px] mx-auto">
          <Link to="/blog" className="text-[#0a5c38] dark:text-[#3fb68e] hover:underline font-sans">
            &larr; Back to All Blog Guides
          </Link>
          <Link to="/portals" className="text-[#0a5c38] dark:text-[#3fb68e] hover:underline font-sans">
            View 42 Monitored Portals &rarr;
          </Link>
        </div>

      </main>
      <Footer />
    </div>
  );
}
