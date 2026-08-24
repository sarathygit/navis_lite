const EQUIPMENT_STATUS_COLORS = {
  IDLE: "#8b949e",
  WORKING: "#3fb950",
};

const WI_STATUS_COLORS = {
  PENDING: "#d9a441",
  WORKING: "#3fb950",
  COMPLETED: "#8b949e",
};

export default function EquipmentPanel({ open, onClose, equipment, workInstructions }) {
  if (!open) return null;

  return (
    <div className="equipment-drawer-backdrop" onClick={onClose}>
      <aside className="equipment-drawer" onClick={(e) => e.stopPropagation()}>
        <header className="equipment-drawer-header">
          <h2>Equipment Control Center</h2>
          <button className="dismiss-btn" onClick={onClose}>×</button>
        </header>

        <div className="equipment-strip">
          {equipment.map((eq) => (
            <div key={eq.id} className="equipment-card">
              <div className="equipment-card-name">{eq.name}</div>
              <div className="equipment-card-type">{eq.type.replace(/_/g, " ")}</div>
              <span className="badge" style={{ backgroundColor: EQUIPMENT_STATUS_COLORS[eq.status] }}>
                {eq.status}
              </span>
            </div>
          ))}
        </div>

        <div className="table-scroll">
          <table className="ledger-table">
            <thead>
              <tr>
                <th>Container ID</th>
                <th>Task</th>
                <th>Equipment</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {workInstructions.length === 0 && (
                <tr>
                  <td colSpan={5} className="empty-row">No work instructions yet</td>
                </tr>
              )}
              {workInstructions.map((wi) => (
                <tr key={wi.id}>
                  <td className="mono">{wi.containerId}</td>
                  <td>{wi.taskType.replace(/_/g, " ")}</td>
                  <td>{wi.equipmentName ?? "-"}</td>
                  <td>
                    <span className="badge" style={{ backgroundColor: WI_STATUS_COLORS[wi.status] }}>
                      {wi.status}
                    </span>
                  </td>
                  <td className="mono">{wi.createdAt ? new Date(wi.createdAt).toLocaleTimeString() : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </aside>
    </div>
  );
}
