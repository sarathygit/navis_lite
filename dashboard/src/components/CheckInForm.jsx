import { useState } from "react";
import { checkInContainer } from "../api/gatewayClient";

const initialState = { containerId: "", weightKg: "", reefer: false, destination: "" };

export default function CheckInForm({ onCheckedIn }) {
  const [form, setForm] = useState(initialState);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await checkInContainer({
        containerId: form.containerId.trim().toUpperCase(),
        weightKg: Number(form.weightKg),
        reefer: form.reefer,
        destination: form.destination || null,
      });
      setForm(initialState);
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
    </form>
  );
}
