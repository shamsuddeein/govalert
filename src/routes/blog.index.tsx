import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect, useMemo } from "react";
import { Nav, Footer } from "../components/layout";
import { blogPosts as fallbackPosts, BlogPost } from "../lib/blogData";
import { api } from "../lib/api";
import { safeFormatDateTime } from "../lib/formatDate";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/blog/")({
  component: BlogIndexPage,
});

type CategoryFilter = "all" | "recruitment" | "tech";

export function getExcerpt(text: string, fallbackExcerpt: string): string {
  if (fallbackExcerpt && fallbackExcerpt.trim()) return fallbackExcerpt;
  if (!text) return "";
  // Strip markdown headings, code blocks, bold/italics
  const clean = text
    .replace(/```[\s\S]*?```/g, "")
    .replace(/^#+\s+/gm, "")
    .replace(/\*\*/g, "")
    .replace(/`/g, "")
    .replace(/\n+/g, " ")
    .trim();
  
  // Extract first two sentences
  const sentences = clean.match(/[^.!?]+[.!?]+/g);
  if (sentences && sentences.length >= 2) {
    return (sentences[0] + " " + sentences[1]).trim();
  }
  return clean.slice(0, 160) + "...";
}

function BlogIndexPage() {
  const [posts, setPosts] = useState<BlogPost[]>(fallbackPosts);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<CategoryFilter>("all");

  useEffect(() => {
    async function loadPosts() {
      try {
        const res = await api.getBlogPosts();
        if (res && res.results && res.results.length > 0) {
          const mapped: BlogPost[] = res.results.map((p: any) => ({
            id: p.id,
            slug: p.slug,
            title: p.title,
            excerpt: p.excerpt || getExcerpt(p.body || p.content || "", ""),
            date: safeFormatDateTime(p.published_date || p.created_at, "24 July 2026"),
            readTime: p.read_time || (p.reading_time ? `${p.reading_time} min read` : "5 min read"),
            reading_time: p.reading_time || 5,
            author: p.author || "Shamsuddeen Yusuf",
            category: (p.category || "recruitment").toLowerCase().includes("tech") ? "tech" : "recruitment",
            category_display: (p.category || "").toLowerCase().includes("tech") ? "Tech Guides" : "Recruitment Guides",
            content: p.body || p.content || "",
            meta_description: p.meta_description,
          }));
          setPosts(mapped);
        }
      } catch (e) {
        // Fallback to static articles
      } finally {
        setLoading(false);
      }
    }
    loadPosts();
  }, []);

  const filteredPosts = useMemo(() => {
    if (activeCategory === "all") return posts;
    return posts.filter((p) => {
      const cat = (p.category || "").toLowerCase();
      if (activeCategory === "recruitment") return cat === "recruitment" || cat.includes("scam") || cat.includes("verified");
      if (activeCategory === "tech") return cat === "tech" || cat.includes("tech");
      return true;
    });
  }, [posts, activeCategory]);

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
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between font-sans selection:bg-secondary/25">
      <SeoHead
        title="Recruitment Guides and Tech Tutorials — RecruitmentAlert Blog"
        description="Practical articles on spotting fake Nigerian recruitment portals and software development tutorials by Shamsuddeen Yusuf."
        canonicalUrl="/blog"
        jsonLd={[breadcrumbSchema]}
      />
      <Nav />
      <main id="main-content" tabIndex={-1} className="flex-1 mx-auto max-w-[1040px] w-full px-4 sm:px-6 py-12 space-y-10 outline-none">
        
        <div>
          <BackButton to="/" label="Back to Home" />
        </div>

        <div className="border-b border-border pb-8 space-y-4 text-left">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-[#0a5c38] dark:text-[#3fb68e] font-mono">
              Knowledge Hub & Developer Guides
            </span>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-primary mt-1">
              RecruitmentAlert Blog
            </h1>
          </div>
          <p className="text-sm sm:text-base text-muted-foreground max-w-2xl leading-relaxed">
            Practical guides on spotting recruitment scams, verifying federal portal addresses, and software engineering tutorials by Shamsuddeen Yusuf.
          </p>

          {/* Category Filter Tabs */}
          <div className="flex items-center gap-2 pt-4">
            <button
              onClick={() => setActiveCategory("all")}
              className={`px-4 py-2 text-xs font-bold rounded-[6px] transition-all cursor-pointer ${
                activeCategory === "all"
                  ? "bg-[#0a5c38] dark:bg-[#3fb68e] text-white shadow-xs"
                  : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground border border-border"
              }`}
            >
              All Articles ({posts.length})
            </button>
            <button
              onClick={() => setActiveCategory("recruitment")}
              className={`px-4 py-2 text-xs font-bold rounded-[6px] transition-all cursor-pointer ${
                activeCategory === "recruitment"
                  ? "bg-[#0a5c38] dark:bg-[#3fb68e] text-white shadow-xs"
                  : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground border border-border"
              }`}
            >
              Recruitment Guides
            </button>
            <button
              onClick={() => setActiveCategory("tech")}
              className={`px-4 py-2 text-xs font-bold rounded-[6px] transition-all cursor-pointer ${
                activeCategory === "tech"
                  ? "bg-[#0a5c38] dark:bg-[#3fb68e] text-white shadow-xs"
                  : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground border border-border"
              }`}
            >
              Tech Guides
            </button>
          </div>
        </div>

        {/* Articles Grid */}
        {filteredPosts.length === 0 ? (
          <div className="text-center py-16 bg-card rounded-[8px] border border-border">
            <p className="text-sm text-muted-foreground">No articles found in this category.</p>
          </div>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-2 items-stretch">
            {filteredPosts.map((post) => {
              const isTech = (post.category || "").toLowerCase().includes("tech");
              const categoryTag = isTech ? "Tech Guides" : "Recruitment Guides";

              return (
                <article
                  key={post.slug}
                  className="group flex flex-col justify-between rounded-[8px] border border-border bg-card p-6 interactive-card hover:border-[#0a5c38]/50 dark:hover:border-[#3fb68e]/50"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider ${
                          isTech
                            ? "bg-purple-100 dark:bg-purple-950/50 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800"
                            : "bg-[#0a5c38]/10 dark:bg-[#3fb68e]/10 text-[#0a5c38] dark:text-[#3fb68e] border border-[#0a5c38]/20 dark:border-[#3fb68e]/20"
                        }`}
                      >
                        {categoryTag}
                      </span>
                      <span className="font-mono text-muted-foreground text-[11px]">
                        {post.readTime || `${post.reading_time || 5} min read`}
                      </span>
                    </div>

                    <h2 className="text-lg font-bold text-foreground leading-snug group-hover:text-primary transition-colors">
                      <Link to="/blog/$slug" params={{ slug: post.slug }}>
                        {post.title}
                      </Link>
                    </h2>

                    <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                      {post.excerpt || getExcerpt(post.content || post.body || "", "")}
                    </p>
                  </div>

                  <div className="mt-6 pt-4 border-t border-border/50 flex items-center justify-between text-xs">
                    <span className="text-muted-foreground font-mono text-[11px]">{post.date}</span>
                    <Link
                      to="/blog/$slug"
                      params={{ slug: post.slug }}
                      className="text-[#0a5c38] dark:text-[#3fb68e] font-semibold hover:underline flex items-center gap-1"
                    >
                      <span>Read article</span>
                      <span>&rarr;</span>
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        )}

        <div className="pt-4 border-t border-border text-xs text-muted-foreground">
          Spot a suspicious portal?{" "}
          <Link to="/portals" className="text-[#0a5c38] dark:text-[#3fb68e] font-semibold hover:underline">
            Check the 42 monitored portals directory &rarr;
          </Link>
        </div>

      </main>
      <Footer />
    </div>
  );
}
