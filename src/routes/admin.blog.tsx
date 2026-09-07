import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import {
  FileText,
  Plus,
  Trash2,
  Edit,
  CheckCircle,
  Eye,
  EyeOff,
  AlertCircle,
  Loader2,
  Sparkles,
} from "lucide-react";
import { adminApi, AdminBlogPostRecord } from "../lib/adminApi";
import { safeFormatDateTime } from "../lib/formatDate";

export const Route = createFileRoute("/admin/blog")({
  component: AdminBlogManagementComponent,
});

function AdminBlogManagementComponent() {
  const [posts, setPosts] = useState<AdminBlogPostRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPost, setEditingPost] = useState<AdminBlogPostRecord | null>(null);
  const [formTitle, setFormTitle] = useState("");
  const [formSlug, setFormSlug] = useState("");
  const [formExcerpt, setFormExcerpt] = useState("");
  const [formContent, setFormContent] = useState("");
  const [formCategory, setFormCategory] = useState("Scam Prevention");
  const [formAuthor, setFormAuthor] = useState("Shamsuddeen Yusuf");
  const [formReadTime, setFormReadTime] = useState("5 min read");
  const [formIsPublished, setFormIsPublished] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const fetchPosts = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminApi.getBlogPosts();
      if (res && res.results) {
        setPosts(res.results);
      }
    } catch (err: any) {
      setError("Failed to load blog posts from API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  const openCreateModal = () => {
    setEditingPost(null);
    setFormTitle("");
    setFormSlug("");
    setFormExcerpt("");
    setFormContent("");
    setFormCategory("Scam Prevention");
    setFormAuthor("Shamsuddeen Yusuf");
    setFormReadTime("5 min read");
    setFormIsPublished(true);
    setIsModalOpen(true);
  };

  const openEditModal = (post: AdminBlogPostRecord) => {
    setEditingPost(post);
    setFormTitle(post.title);
    setFormSlug(post.slug);
    setFormExcerpt(post.excerpt);
    setFormContent(post.content);
    setFormCategory(post.category);
    setFormAuthor(post.author);
    setFormReadTime(post.read_time);
    setFormIsPublished(post.is_published);
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTitle.trim() || !formContent.trim()) {
      setError("Title and content markdown are required.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      if (editingPost) {
        await adminApi.updateBlogPost(editingPost.id, {
          title: formTitle.trim(),
          slug: formSlug.trim(),
          excerpt: formExcerpt.trim(),
          content: formContent.trim(),
          category: formCategory.trim(),
          author: formAuthor.trim(),
          read_time: formReadTime.trim(),
          is_published: formIsPublished,
        });
        setSuccessMessage("Blog post updated successfully!");
      } else {
        await adminApi.createBlogPost({
          title: formTitle.trim(),
          slug: formSlug.trim(),
          excerpt: formExcerpt.trim(),
          content: formContent.trim(),
          category: formCategory.trim(),
          author: formAuthor.trim(),
          read_time: formReadTime.trim(),
          is_published: formIsPublished,
        });
        setSuccessMessage("New blog post created successfully!");
      }

      setIsModalOpen(false);
      fetchPosts();
    } catch (err: any) {
      setError(err?.message || "Failed to save blog post.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this blog post?")) return;
    try {
      await adminApi.deleteBlogPost(id);
      setSuccessMessage("Blog post deleted.");
      fetchPosts();
    } catch (err: any) {
      setError("Failed to delete blog post.");
    }
  };

  const handleTogglePublish = async (post: AdminBlogPostRecord) => {
    try {
      await adminApi.updateBlogPost(post.id, {
        is_published: !post.is_published,
      });
      setSuccessMessage(`Post "${post.title}" ${!post.is_published ? "published" : "unpublished"}.`);
      fetchPosts();
    } catch (err: any) {
      setError("Failed to update status.");
    }
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <FileText className="size-5 text-[#0a5c38] dark:text-[#3fb68e]" />
            Scam Awareness Blog Posts
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Create, edit, and publish anti-scam guides and educational articles for Nigerian job seekers.
          </p>
        </div>

        <button
          onClick={openCreateModal}
          className="inline-flex items-center gap-2 bg-[#0a5c38] hover:bg-[#0f7a4a] text-white dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 dark:text-[#0c1015] px-4 py-2 rounded-[6px] text-xs font-semibold shadow-xs transition-colors cursor-pointer"
        >
          <Plus className="size-4" />
          Create New Article
        </button>
      </div>

      {/* Messages */}
      {successMessage && (
        <div className="p-3.5 rounded-[6px] bg-[#0a5c38]/10 text-[#0a5c38] dark:bg-[#3fb68e]/10 dark:text-[#3fb68e] border border-[#0a5c38]/30 text-xs font-semibold flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle className="size-4" />
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-xs underline font-bold cursor-pointer">
            Dismiss
          </button>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-[6px] bg-destructive/10 text-destructive border border-destructive/30 text-xs font-semibold flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="size-4" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-xs underline font-bold cursor-pointer">
            Dismiss
          </button>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="p-12 text-center border border-border bg-card rounded-[8px] space-y-3">
          <Loader2 className="size-6 animate-spin text-[#0a5c38] dark:text-[#3fb68e] mx-auto" />
          <p className="text-xs text-muted-foreground">Loading blog articles...</p>
        </div>
      ) : posts.length === 0 ? (
        <div className="p-12 text-center border border-border bg-card rounded-[8px] space-y-3">
          <FileText className="size-8 text-muted-foreground mx-auto" />
          <p className="text-sm font-semibold text-foreground">No blog posts found</p>
          <p className="text-xs text-muted-foreground">Click "Create New Article" to publish your first post.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-[8px] border border-border bg-card shadow-xs">
          <table className="w-full text-left border-collapse font-sans">
            <thead>
              <tr className="border-b border-border bg-muted/20 text-[11px] font-semibold text-muted-foreground uppercase font-mono tracking-wider">
                <th className="p-3.5">Article Title</th>
                <th className="p-3.5">Category</th>
                <th className="p-3.5">Author</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5">Created Date</th>
                <th className="p-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border text-xs">
              {posts.map((post) => (
                <tr key={post.id} className="hover:bg-muted/10 transition-colors">
                  <td className="p-3.5 font-semibold text-foreground max-w-[280px]">
                    <div className="truncate font-bold">{post.title}</div>
                    <div className="font-mono text-[11px] text-muted-foreground truncate">/blog/{post.slug}</div>
                  </td>
                  <td className="p-3.5">
                    <span className="bg-muted px-2 py-0.5 rounded text-[11px] font-medium text-foreground">
                      {post.category}
                    </span>
                  </td>
                  <td className="p-3.5 text-muted-foreground font-medium">{post.author}</td>
                  <td className="p-3.5">
                    <button
                      onClick={() => handleTogglePublish(post)}
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-[4px] text-[11px] font-bold font-mono uppercase cursor-pointer ${
                        post.is_published
                          ? "bg-[#15803D]/10 text-[#15803D] dark:bg-[#15803D]/20 dark:text-[#3fb68e]"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {post.is_published ? (
                        <>
                          <Eye className="size-3" /> Published
                        </>
                      ) : (
                        <>
                          <EyeOff className="size-3" /> Draft
                        </>
                      )}
                    </button>
                  </td>
                  <td className="p-3.5 font-mono text-muted-foreground">
                    {safeFormatDateTime(post.created_at, "Recent")}
                  </td>
                  <td className="p-3.5 text-right space-x-2">
                    <button
                      onClick={() => openEditModal(post)}
                      className="p-1.5 hover:bg-muted rounded text-foreground transition-colors cursor-pointer"
                      title="Edit article"
                    >
                      <Edit className="size-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(post.id)}
                      className="p-1.5 hover:bg-destructive/10 text-destructive rounded transition-colors cursor-pointer"
                      title="Delete article"
                    >
                      <Trash2 className="size-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal Form */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-[8px] w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 space-y-5 shadow-xl font-sans">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h2 className="text-base font-bold text-foreground">
                {editingPost ? "Edit Blog Article" : "Create New Blog Article"}
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-xs font-semibold text-muted-foreground hover:text-foreground cursor-pointer"
              >
                Close ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 text-xs font-sans">
              <div className="space-y-1">
                <label className="font-semibold text-foreground uppercase tracking-wider font-mono">Title</label>
                <input
                  type="text"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  placeholder="e.g. How to spot a fake NNPC recruitment..."
                  className="w-full p-2.5 bg-background border border-border rounded-[6px] text-sm text-foreground focus:outline-none focus:border-primary font-sans"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-foreground uppercase tracking-wider font-mono">URL Slug</label>
                  <input
                    type="text"
                    value={formSlug}
                    onChange={(e) => setFormSlug(e.target.value)}
                    placeholder="spot-fake-nnpc-recruitment"
                    className="w-full p-2.5 bg-background border border-border rounded-[6px] text-xs font-mono text-foreground focus:outline-none focus:border-primary"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground uppercase tracking-wider font-mono">Category</label>
                  <input
                    type="text"
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    placeholder="Scam Prevention"
                    className="w-full p-2.5 bg-background border border-border rounded-[6px] text-xs text-foreground focus:outline-none focus:border-primary font-sans"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-foreground uppercase tracking-wider font-mono">Author</label>
                  <input
                    type="text"
                    value={formAuthor}
                    onChange={(e) => setFormAuthor(e.target.value)}
                    placeholder="Shamsuddeen Yusuf"
                    className="w-full p-2.5 bg-background border border-border rounded-[6px] text-xs text-foreground focus:outline-none focus:border-primary font-sans"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground uppercase tracking-wider font-mono">Read Time</label>
                  <input
                    type="text"
                    value={formReadTime}
                    onChange={(e) => setFormReadTime(e.target.value)}
                    placeholder="5 min read"
                    className="w-full p-2.5 bg-background border border-border rounded-[6px] text-xs text-foreground focus:outline-none focus:border-primary font-sans"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-foreground uppercase tracking-wider font-mono">Short Excerpt</label>
                <textarea
                  rows={2}
                  value={formExcerpt}
                  onChange={(e) => setFormExcerpt(e.target.value)}
                  placeholder="Summary for search engines and social cards..."
                  className="w-full p-2.5 bg-background border border-border rounded-[6px] text-xs text-foreground focus:outline-none focus:border-primary font-sans"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-foreground uppercase tracking-wider font-mono">Article Content (Markdown supported)</label>
                <textarea
                  rows={10}
                  value={formContent}
                  onChange={(e) => setFormContent(e.target.value)}
                  placeholder="Write your article in Markdown..."
                  className="w-full p-2.5 bg-background border border-border rounded-[6px] text-xs font-mono text-foreground focus:outline-none focus:border-primary"
                  required
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="is_published"
                  checked={formIsPublished}
                  onChange={(e) => setFormIsPublished(e.target.checked)}
                  className="size-4 rounded accent-[#0a5c38]"
                />
                <label htmlFor="is_published" className="font-semibold text-foreground cursor-pointer font-sans">
                  Publish article immediately to public website (/blog)
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-[6px] border border-border bg-card text-xs font-semibold text-foreground hover:bg-muted cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-[6px] bg-[#0a5c38] hover:bg-[#0f7a4a] text-white dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 dark:text-[#0c1015] text-xs font-semibold flex items-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {submitting ? <Loader2 className="size-3.5 animate-spin" /> : null}
                  {editingPost ? "Save Changes" : "Create Post"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
