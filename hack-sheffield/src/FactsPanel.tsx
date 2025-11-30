import { useEffect, useState } from "react";

export default function FactsPanel({ username }: { username: string }) {
  const [facts, setFacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFacts = async () => {
    if (!username) return setFacts([]);
    setLoading(true);
    setError(null);
    try {
      const backend = (import.meta.env && import.meta.env.VITE_API_URL) || "http://localhost:8000";
      const res = await fetch(`${backend}/api/facts?username=${encodeURIComponent(username)}`);
      const j = await res.json();
      if (j.ok) setFacts(j.data || []);
      else setError(j.error || "Unknown error");
    } catch (err: any) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFacts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [username]);

  const deleteFact = async (id: string) => {
    try {
      const backend = (import.meta.env && import.meta.env.VITE_API_URL) || "http://localhost:8000";
      const res = await fetch(`${backend}/api/facts/${id}`, { method: "DELETE" });
      const j = await res.json();
      if (j.ok) {
        setFacts((f) => f.filter((x) => x.id !== id));
      } else {
        setError(j.error || "Delete failed");
      }
    } catch (e: any) {
      setError(String(e));
    }
  };

  const renderFact = (f: any) => (
    <div key={f.id} className="flex items-start justify-between gap-3 p-3 border rounded-lg mb-2 bg-white/80">
      <div className="flex-1">
        <div className="text-xs text-gray-500">{f.fact_type}</div>
        <div className="font-semibold text-gray-800">{f.value}</div>
        {f.normalized_value && <div className="text-xs text-gray-400">Normalized: {f.normalized_value}</div>}
      </div>
      <div className="flex flex-col items-end gap-2">
        <div className="text-xs text-gray-400">{new Date(f.created_at).toLocaleString()}</div>
        <div className="flex gap-2">
          <button
            className="px-2 py-1 text-xs bg-red-500 hover:bg-red-600 text-white rounded-full"
            onClick={() => deleteFact(f.id)}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );

  if (!username) return <div className="text-sm text-gray-500">Sign in to view your saved memories.</div>;

  return (
    <div>
      {loading && <div className="text-sm text-gray-500">Loading…</div>}
      {error && <div className="text-sm text-red-500">Error: {error}</div>}

      {facts.length === 0 && !loading && <div className="text-sm text-gray-500">No saved facts found.</div>}

      <div className="mt-2">
        {facts.map((f) => renderFact(f))}
      </div>
    </div>
  );
}
