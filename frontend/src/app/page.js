"use client";

import { useEffect, useState } from "react";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadPosts() {
      try {
        const response = await fetch(`${apiBaseUrl}/api/posts`);

        if (!response.ok) {
          setPosts([]);
          return;
        }

        setPosts(await response.json());
      } catch {
        setPosts([]);
      } finally {
        setLoading(false);
      }
    }

    loadPosts();
  }, []);

  return (
    <main className="page-shell">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Medium-inspired publishing platform</p>
          <h1>Goptant Blog ships with the full content stack.</h1>
          <p className="hero-text">
            FastAPI powers the API, Next.js renders the reading experience,
            PostgreSQL stores posts, and Celery with Redis handles async work.
          </p>
          <div className="stack-list">
            <span>FastAPI</span>
            <span>Next.js</span>
            <span>PostgreSQL</span>
            <span>Redis</span>
            <span>Celery</span>
            <span>Docker</span>
            <span>GitHub Actions</span>
          </div>
        </div>
      </section>

      <section className="content-grid">
        <article className="panel">
          <h2>Recent posts</h2>
          {posts.length ? (
            <div className="post-list">
              {posts.map((post) => (
                <div className="post-card" key={post.id}>
                  <p className="post-meta">
                    {post.author} ·{" "}
                    {new Date(post.published_at).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })}
                  </p>
                  <h3>{post.title}</h3>
                  <p>{post.summary}</p>
                </div>
              ))}
            </div>
          ) : loading ? (
            <p className="empty-state">Loading posts from the FastAPI backend...</p>
          ) : (
            <p className="empty-state">
              API data will appear here once the backend is running.
            </p>
          )}
        </article>

        <aside className="panel">
          <h2>Included workflow</h2>
          <ul className="feature-list">
            <li>Docker Compose stack for local deployment</li>
            <li>FastAPI API with seeded blog data</li>
            <li>Celery worker and Redis-backed task queue</li>
            <li>PostgreSQL persistence for posts</li>
            <li>GitHub Actions CI for backend, frontend, and Docker config</li>
          </ul>
        </aside>
      </section>
    </main>
  );
}
