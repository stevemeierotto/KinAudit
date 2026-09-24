import { useEffect, useState } from "react";
import { fetchHealth, fetchHealthReady, getApiBaseUrl } from "./api/health.js";

export default function App() {
  const [health, setHealth] = useState(null);
  const [ready, setReady] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [healthResult, readyResult] = await Promise.all([
          fetchHealth(),
          fetchHealthReady(),
        ]);
        if (!cancelled) {
          setHealth(healthResult);
          setReady(readyResult);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", margin: "2rem", maxWidth: "40rem" }}>
      <h1>KinAudit</h1>
      <p>Phase A foundation — backend connectivity check.</p>
      <p>
        API base URL: <code>{getApiBaseUrl()}</code>
      </p>

      {loading && <p>Checking backend health…</p>}

      {error && (
        <p style={{ color: "#a40000" }}>
          Failed to reach backend: {error}
        </p>
      )}

      {!loading && !error && (
        <section>
          <h2>Liveness (`/health`)</h2>
          <pre>{JSON.stringify(health, null, 2)}</pre>

          <h2>Readiness (`/health/ready`)</h2>
          <p>HTTP status: {ready?.statusCode}</p>
          <pre>{JSON.stringify(ready?.body, null, 2)}</pre>
        </section>
      )}
    </main>
  );
}
