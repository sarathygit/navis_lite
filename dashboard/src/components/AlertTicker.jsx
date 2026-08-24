import { useEffect, useState } from "react";

export default function AlertTicker({ alerts }) {
  const [flash, setFlash] = useState(false);
  const latest = alerts.length > 0 ? alerts[alerts.length - 1] : null;

  useEffect(() => {
    if (!latest) return;
    setFlash(true);
    const timeout = setTimeout(() => setFlash(false), 900);
    return () => clearTimeout(timeout);
  }, [latest?.id]);

  return (
    <footer className={`alert-ticker ${flash ? "alert-ticker-flash" : ""} ${latest ? "alert-ticker-active" : ""}`}>
      {latest ? (
        <span className="mono">
          [{new Date(latest.timestamp).toLocaleTimeString()}] {latest.severity} — {latest.message}
        </span>
      ) : (
        <span className="mono">No active telemetry alerts</span>
      )}
      <span className="alert-count">{alerts.length} total alerts logged</span>
    </footer>
  );
}
