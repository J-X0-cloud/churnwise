"use client";

import { useEffect } from "react";

/** Shown when a page cannot reach the engine (or anything else fails while rendering). */
export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="section" id="main">
      <div className="wrap">
        <span className="eyebrow">Something went wrong</span>
        <h1>The revenue numbers are unavailable right now.</h1>
        <p className="lead">
          The metrics service didn&apos;t answer. If you&apos;re running Churnwise locally, start the engine
          with <code>pnpm engine:dev</code> and check that <code>API_URL</code> points at it.
        </p>
        <button type="button" className="btn" onClick={reset}>
          Try again
        </button>
      </div>
    </main>
  );
}
