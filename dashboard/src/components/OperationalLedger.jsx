import { useState } from "react";
import { applyHold, checkOutContainer, clearHold, loadToVessel } from "../api/gatewayClient";

const STATUS_COLORS = {
  PENDING: "#d9a441",
  DECKED: "#3fb950",
  REJECTED: "#e5534b",
  DEPARTED: "#8b949e",
  HELD: "#f0883e",
  LOADED: "#a371f7",
};

const PENALTY_COLORS = {
  HIGH: "#e5534b",
  MEDIUM: "#d9a441",
  LOW: "#3fb950",
};

const HOLD_TYPES = ["CUSTOMS_HOLD", "VESSEL_CUTOFF_EXPIRED", "DAMAGE_HOLD"];

// Vessel grid is 6 bays x 4 rows x 4 tiers (decking-engine/app/core/config.py).
// Surfacing the ceiling here keeps the form honest about what the engine accepts.
const VESSEL_COORDS = [
  { key: "bay", label: "Bay", max: 6 },
  { key: "row", label: "Row", max: 4 },
  { key: "tier", label: "Tier", max: 4 },
];

export default function OperationalLedger({ transactions, onChanged }) {
  const [pendingId, setPendingId] = useState(null);
  const [error, setError] = useState(null);
  const [holdSelection, setHoldSelection] = useState({});
  const [vesselCoords, setVesselCoords] = useState({});

  async function handleCheckOut(containerId) {
    setPendingId(containerId);
    setError(null);
    try {
      await checkOutContainer(containerId);
      onChanged?.();
    } catch (err) {
      setError({ containerId, message: err.details?.join(" — ") || err.message });
    } finally {
      setPendingId(null);
    }
  }

  async function handleApplyHold(containerId) {
    const holdType = holdSelection[containerId] || HOLD_TYPES[0];
    setPendingId(containerId);
    setError(null);
    try {
      await applyHold(containerId, holdType, `${holdType.replace(/_/g, " ")} applied via dashboard`);
      onChanged?.();
    } catch (err) {
      setError({ containerId, message: err.details?.join(" — ") || err.message });
    } finally {
      setPendingId(null);
    }
  }

  async function handleClearHold(containerId) {
    setPendingId(containerId);
    setError(null);
    try {
      await clearHold(containerId);
      onChanged?.();
    } catch (err) {
      setError({ containerId, message: err.details?.join(" — ") || err.message });
    } finally {
      setPendingId(null);
    }
  }

  function updateVesselCoord(containerId, field, value) {
    setVesselCoords({
      ...vesselCoords,
      [containerId]: { ...(vesselCoords[containerId] || { bay: 1, row: 1, tier: 1 }), [field]: Number(value) },
    });
  }

  async function handleLoadToVessel(containerId) {
    const coords = vesselCoords[containerId] || { bay: 1, row: 1, tier: 1 };
    setPendingId(containerId);
    setError(null);
    try {
      await loadToVessel(containerId, coords.bay, coords.row, coords.tier);
      onChanged?.();
    } catch (err) {
      setError({ containerId, message: err.details?.join(" — ") || err.message });
    } finally {
      setPendingId(null);
    }
  }

  return (
    <section className="panel ledger-panel">
      <header className="panel-header">
        <h2>Operational Ledger</h2>
        <span className="panel-subtitle">{transactions.length} active transactions</span>
      </header>
      {error && (
        <div className="ledger-error">
          <strong>{error.containerId}</strong> action blocked: {error.message}
          <button className="dismiss-btn" onClick={() => setError(null)}>×</button>
        </div>
      )}
      <div className="table-scroll">
        <table className="ledger-table">
          <thead>
            <tr>
              <th>Container ID</th>
              <th>ISO</th>
              <th>Weight (kg)</th>
              <th>Reefer</th>
              <th>Status</th>
              <th>Risk</th>
              <th>Hold</th>
              <th>Block</th>
              <th>Tier</th>
              <th>Check-in</th>
              <th>Departure</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {transactions.length === 0 && (
              <tr>
                <td colSpan={12} className="empty-row">No gate transactions yet</td>
              </tr>
            )}
            {transactions.map((tx) => (
              <tr key={tx.id}>
                <td className="mono">{tx.containerId}</td>
                <td>
                  <span className="badge badge-iso">VALID</span>
                </td>
                <td>{tx.weightKg?.toLocaleString()}</td>
                <td>{tx.reefer ? "REEFER" : "DRY"}</td>
                <td>
                  <span className="badge" style={{ backgroundColor: STATUS_COLORS[tx.status] }}>
                    {tx.status}
                  </span>
                </td>
                <td>
                  {tx.penaltyFlag && (
                    <span
                      className="badge"
                      style={{ backgroundColor: PENALTY_COLORS[tx.penaltyFlag] }}
                      title={`Shuffle risk score: ${tx.shuffleRiskScore}%`}
                    >
                      {tx.penaltyFlag}
                    </span>
                  )}
                </td>
                <td>
                  {tx.holdType && (
                    <span className="badge badge-hold" title={tx.holdReason || ""}>
                      HOLD: {tx.holdType.replace(/_/g, " ")}
                    </span>
                  )}
                </td>
                <td>{tx.assignedBlock ?? "-"}</td>
                <td>{tx.assignedTier ?? "-"}</td>
                <td className="mono">{tx.checkInTime ? new Date(tx.checkInTime).toLocaleTimeString() : "-"}</td>
                <td className="mono">{tx.departureTime ? new Date(tx.departureTime).toLocaleTimeString() : "-"}</td>
                <td className="action-cell">
                  {tx.status === "DECKED" && !tx.holdType && (
                    <button
                      className="checkout-btn"
                      disabled={pendingId === tx.containerId}
                      onClick={() => handleCheckOut(tx.containerId)}
                    >
                      {pendingId === tx.containerId ? "…" : "Check Out"}
                    </button>
                  )}
                  {(tx.status === "DECKED" || tx.status === "HELD") && !tx.holdType && (
                    <span className="hold-control">
                      <select
                        value={holdSelection[tx.containerId] || HOLD_TYPES[0]}
                        onChange={(e) => setHoldSelection({ ...holdSelection, [tx.containerId]: e.target.value })}
                      >
                        {HOLD_TYPES.map((ht) => (
                          <option key={ht} value={ht}>{ht.replace(/_/g, " ")}</option>
                        ))}
                      </select>
                      <button
                        className="hold-btn"
                        disabled={pendingId === tx.containerId}
                        onClick={() => handleApplyHold(tx.containerId)}
                      >
                        Hold
                      </button>
                    </span>
                  )}
                  {tx.holdType && (
                    <button
                      className="clear-hold-btn"
                      disabled={pendingId === tx.containerId}
                      onClick={() => handleClearHold(tx.containerId)}
                    >
                      {pendingId === tx.containerId ? "…" : "Clear Hold"}
                    </button>
                  )}
                  {tx.status === "DECKED" && !tx.holdType && (
                    <span className="vessel-control">
                      <span className="vessel-coords">
                        <span className="vessel-coords-legend">Ship position</span>
                        <span className="vessel-fields">
                          {VESSEL_COORDS.map(({ key, label, max }) => (
                            <label key={key} className="coord-field">
                              <span className="coord-label">{label}</span>
                              <input
                                type="number"
                                min="1"
                                max={max}
                                title={`${label} (1–${max})`}
                                aria-label={`Vessel ${label.toLowerCase()} for ${tx.containerId}`}
                                value={vesselCoords[tx.containerId]?.[key] ?? 1}
                                onChange={(e) => updateVesselCoord(tx.containerId, key, e.target.value)}
                              />
                            </label>
                          ))}
                        </span>
                      </span>
                      <button
                        className="vessel-load-btn"
                        disabled={pendingId === tx.containerId}
                        onClick={() => handleLoadToVessel(tx.containerId)}
                      >
                        Load to Vessel
                      </button>
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
