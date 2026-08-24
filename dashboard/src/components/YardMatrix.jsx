const TIERS = [5, 4, 3, 2, 1];

function slotColor(slot) {
  if (!slot.occupied) return "#30363d"; // gray - empty
  if (slot.reefer) return "#39c5cf"; // cyan/blue - active reefer
  return "#3fb950"; // green - occupied dry
}

function slotTooltip(slot, hold) {
  if (!slot.occupied) {
    return `${slot.block}-${String(slot.row).padStart(2, "0")}-${String(slot.bay).padStart(2, "0")} tier ${slot.tier}\nEMPTY`;
  }
  const lines = [
    `${slot.block}-${String(slot.row).padStart(2, "0")}-${String(slot.bay).padStart(2, "0")} tier ${slot.tier}`,
    `Container: ${slot.containerId}`,
    `Weight: ${slot.weightKg?.toLocaleString()} kg`,
    `Est. dwell: ${slot.dwellTimeEstimate?.toFixed(1)} days`,
    slot.reefer ? "Type: REEFER (powered)" : "Type: DRY",
  ];
  if (slot.penaltyFlag) {
    lines.push(`Rehandle Risk: ${slot.penaltyFlag} (${slot.shuffleRiskScore}%)`);
  }
  if (hold) {
    lines.push(`HOLD: ${hold.holdType.replace(/_/g, " ")}${hold.holdReason ? ` — ${hold.holdReason}` : ""}`);
  }
  return lines.join("\n");
}

function Stack({ slots, holdsByContainerId }) {
  const byTier = Object.fromEntries(slots.map((s) => [s.tier, s]));
  return (
    <div className="stack">
      {TIERS.map((tier) => {
        const slot = byTier[tier];
        if (!slot) return <div key={tier} className="stack-cell stack-cell-void" />;
        const hold = slot.containerId ? holdsByContainerId[slot.containerId] : null;
        return (
          <div
            key={tier}
            className={`stack-cell ${hold ? "stack-cell-held" : ""}`}
            style={{ backgroundColor: slotColor(slot) }}
            title={slotTooltip(slot, hold)}
          />
        );
      })}
    </div>
  );
}

function Block({ name, slots, powered, holdsByContainerId }) {
  const stacks = {};
  for (const slot of slots) {
    const key = `${slot.row}-${slot.bay}`;
    if (!stacks[key]) stacks[key] = [];
    stacks[key].push(slot);
  }
  const stackKeys = Object.keys(stacks).sort((a, b) => {
    const [ar, ab] = a.split("-").map(Number);
    const [br, bb] = b.split("-").map(Number);
    return ar - br || ab - bb;
  });

  return (
    <div className={`yard-block ${powered ? "yard-block-powered" : ""}`}>
      <div className="yard-block-title">
        Block-{name} {powered && <span className="powered-tag">POWERED</span>}
      </div>
      <div className="yard-block-grid">
        {stackKeys.map((key) => (
          <Stack key={key} slots={stacks[key]} holdsByContainerId={holdsByContainerId} />
        ))}
      </div>
    </div>
  );
}

export default function YardMatrix({ slots, holdsByContainerId = {} }) {
  const byBlock = {};
  for (const slot of slots) {
    if (!byBlock[slot.block]) byBlock[slot.block] = [];
    byBlock[slot.block].push(slot);
  }
  const blockNames = Object.keys(byBlock).sort();

  return (
    <section className="panel yard-panel">
      <header className="panel-header">
        <h2>Digital Twin Yard Matrix</h2>
        <div className="legend">
          <span><i className="legend-swatch" style={{ backgroundColor: "#30363d" }} /> Empty</span>
          <span><i className="legend-swatch" style={{ backgroundColor: "#3fb950" }} /> Dry</span>
          <span><i className="legend-swatch" style={{ backgroundColor: "#39c5cf" }} /> Reefer</span>
          <span><i className="legend-swatch legend-swatch-held" /> Hold</span>
        </div>
      </header>
      <div className="yard-grid">
        {blockNames.map((name) => (
          <Block key={name} name={name} slots={byBlock[name]} powered={name === "R"} holdsByContainerId={holdsByContainerId} />
        ))}
      </div>
    </section>
  );
}
