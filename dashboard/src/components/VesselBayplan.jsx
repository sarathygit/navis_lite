const TIERS = [4, 3, 2, 1];

function slotColor(slot) {
  if (!slot.occupied) return "#30363d"; // gray - empty
  return slot.upperDeck ? "#a371f7" : "#3fb950"; // purple - upper deck, green - lower deck
}

function slotTooltip(slot) {
  if (!slot.occupied) {
    return `Bay ${slot.bay} Row ${slot.row} Tier ${slot.tier}\nEMPTY${slot.upperDeck ? " (upper deck)" : ""}`;
  }
  return [
    `Bay ${slot.bay} Row ${slot.row} Tier ${slot.tier}${slot.upperDeck ? " (upper deck)" : ""}`,
    `Container: ${slot.containerId}`,
    `Weight: ${slot.weightKg?.toLocaleString()} kg`,
  ].join("\n");
}

function Stack({ slots }) {
  const byTier = Object.fromEntries(slots.map((s) => [s.tier, s]));
  return (
    <div className="stack">
      {TIERS.map((tier) => {
        const slot = byTier[tier];
        if (!slot) return <div key={tier} className="stack-cell stack-cell-void" />;
        return (
          <div
            key={tier}
            className="stack-cell"
            style={{ backgroundColor: slotColor(slot) }}
            title={slotTooltip(slot)}
          />
        );
      })}
    </div>
  );
}

function Bay({ bay, slots }) {
  const stacks = {};
  for (const slot of slots) {
    if (!stacks[slot.row]) stacks[slot.row] = [];
    stacks[slot.row].push(slot);
  }
  const rows = Object.keys(stacks).sort((a, b) => Number(a) - Number(b));

  return (
    <div className="yard-block">
      <div className="yard-block-title">Bay {bay}</div>
      <div className="yard-block-grid">
        {rows.map((row) => (
          <Stack key={row} slots={stacks[row]} />
        ))}
      </div>
    </div>
  );
}

export default function VesselBayplan({ slots, stability }) {
  const byBay = {};
  for (const slot of slots) {
    if (!byBay[slot.bay]) byBay[slot.bay] = [];
    byBay[slot.bay].push(slot);
  }
  const bayNumbers = Object.keys(byBay).sort((a, b) => Number(a) - Number(b));

  return (
    <section className="panel yard-panel">
      <header className="panel-header">
        <h2>Vessel Bayplan View</h2>
        <div className="legend">
          <span><i className="legend-swatch" style={{ backgroundColor: "#30363d" }} /> Empty</span>
          <span><i className="legend-swatch" style={{ backgroundColor: "#3fb950" }} /> Lower Deck</span>
          <span><i className="legend-swatch" style={{ backgroundColor: "#a371f7" }} /> Upper Deck</span>
        </div>
      </header>
      {stability && (
        <div className={`vessel-stability-summary ${stability.violations.length > 0 ? "vessel-stability-warning" : ""}`}>
          Total deck weight: {stability.totalDeckWeight?.toLocaleString()} kg
          {stability.violations.length > 0 && (
            <span> — {stability.violations.length} stability violation(s): heavy cargo on upper deck</span>
          )}
        </div>
      )}
      <div className="yard-grid">
        {bayNumbers.map((bay) => (
          <Bay key={bay} bay={bay} slots={byBay[bay]} />
        ))}
      </div>
    </section>
  );
}
