import { useState } from "react";
import { checkInContainer } from "../api/gatewayClient";

const initialState = { containerId: "", weightKg: "", reefer: false, destination: "" };

const slot = (block, row, bay, tier) => `${block}-R${row}-B${bay}-T${tier}`;

export default function CheckInForm({ onCheckedIn }) {
  const [form, setForm] = useState(initialState);
  const [error, setError] = useState(null);
  // A rejected container comes back as a normal 201, not an HTTP error — the
  // yard simply had nowhere legal to put it. Hold onto the engine's advice.
  const [rejection, setRejection] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setRejection(null);
    setSubmitting(true);
    try {
      const result = await checkInContainer({
        containerId: form.containerId.trim().toUpperCase(),
        weightKg: Number(form.weightKg),
        reefer: form.reefer,
        destination: form.destination || null,
      });
      if (result.status === "REJECTED") {
        setRejection(result);
      } else {
        setForm(initialState);
      }
      onCheckedIn?.();
    } catch (err) {
      setError(err.details?.join("; ") || err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="checkin-form" onSubmit={handleSubmit}>
      <input
        className="mono"
        placeholder="ABCD1234567"
        value={form.containerId}
        maxLength={11}
        onChange={(e) => setForm({ ...form, containerId: e.target.value })}
        required
      />
      <input
        type="number"
        placeholder="Weight (kg)"
        value={form.weightKg}
        min="1"
        step="1"
        onChange={(e) => setForm({ ...form, weightKg: e.target.value })}
        required
      />
      <label className="checkbox-label">
        <input
          type="checkbox"
          checked={form.reefer}
          onChange={(e) => setForm({ ...form, reefer: e.target.checked })}
        />
        Reefer
      </label>
      <input
        placeholder="Destination (optional)"
        value={form.destination}
        onChange={(e) => setForm({ ...form, destination: e.target.value })}
      />
      <button type="submit" disabled={submitting}>
        {submitting ? "Checking in…" : "Gate Check-In"}
      </button>
      {error && <span className="form-error">{error}</span>}
      {rejection && <RejectionAdvice result={rejection} onDismiss={() => setRejection(null)} />}
    </form>
  );
}

/**
 * Shown when the yard had no legal slot. If the engine found a housekeeping move
 * that would open one, we spell it out — the operator decides whether to make it.
 */
function RejectionAdvice({ result, onDismiss }) {
  const s = result.suggestion;
  return (
    <div className="rejection-advice">
      <div className="rejection-advice-head">
        <strong>{result.containerId} rejected</strong>
        <button type="button" className="link-button" onClick={onDismiss}>
          dismiss
        </button>
      </div>
      {s ? (
        <>
          <p className="rejection-advice-reason">{s.reason}</p>
          <ol className="rejection-advice-steps">
            <li>
              Move <span className="mono">{s.moveContainerId}</span> from{" "}
              <span className="mono">{slot(s.fromBlock, s.fromRow, s.fromBay, s.fromTier)}</span> to{" "}
              <span className="mono">{slot(s.toBlock, s.toRow, s.toBay, s.toTier)}</span>
            </li>
            <li>
              Then place <span className="mono">{result.containerId}</span> at{" "}
              <span className="mono">
                {slot(s.thenPlaceAtBlock, s.thenPlaceAtRow, s.thenPlaceAtBay, s.thenPlaceAtTier)}
              </span>
            </li>
          </ol>
          <p className="rejection-advice-note">
            Advisory only — no container has been moved. Re-submit the check-in once the
            move is done.
          </p>
        </>
      ) : (
        <p className="rejection-advice-reason">
          No single housekeeping move would free a suitable slot. The yard needs a
          departure before this container can be decked.
        </p>
      )}
    </div>
  );
}
