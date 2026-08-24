import { useCallback, useEffect, useState } from "react";
import OperationalLedger from "./components/OperationalLedger";
import YardMatrix from "./components/YardMatrix";
import VesselBayplan from "./components/VesselBayplan";
import AlertTicker from "./components/AlertTicker";
import CheckInForm from "./components/CheckInForm";
import EquipmentPanel from "./components/EquipmentPanel";
import { downloadEdiManifest, fetchEquipment, fetchTransactions, fetchWorkInstructions } from "./api/gatewayClient";
import { fetchAlerts, fetchEfficiencyIndex, fetchVesselStability, fetchVesselState, fetchYardState } from "./api/deckingClient";

const POLL_INTERVAL_MS = 4000;

function efficiencyColor(value) {
  if (value >= 80) return "#3fb950";
  if (value >= 50) return "#d9a441";
  return "#e5534b";
}

export default function App() {
  const [transactions, setTransactions] = useState([]);
  const [yardSlots, setYardSlots] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [efficiencyIndex, setEfficiencyIndex] = useState(null);
  const [exportError, setExportError] = useState(null);
  const [equipment, setEquipment] = useState([]);
  const [workInstructions, setWorkInstructions] = useState([]);
  const [equipmentPanelOpen, setEquipmentPanelOpen] = useState(false);
  const [vesselSlots, setVesselSlots] = useState([]);
  const [vesselStability, setVesselStability] = useState(null);
  const [rightPanelTab, setRightPanelTab] = useState("yard");

  const refreshLedger = useCallback(() => {
    fetchTransactions().then(setTransactions).catch(() => {});
  }, []);

  const refreshYard = useCallback(() => {
    fetchYardState().then(setYardSlots).catch(() => {});
  }, []);

  const refreshAlerts = useCallback(() => {
    fetchAlerts(0).then(setAlerts).catch(() => {});
  }, []);

  const refreshEfficiencyIndex = useCallback(() => {
    fetchEfficiencyIndex().then(setEfficiencyIndex).catch(() => {});
  }, []);

  const refreshEquipment = useCallback(() => {
    fetchEquipment().then(setEquipment).catch(() => {});
  }, []);

  const refreshWorkInstructions = useCallback(() => {
    fetchWorkInstructions().then(setWorkInstructions).catch(() => {});
  }, []);

  const refreshVessel = useCallback(() => {
    fetchVesselState().then(setVesselSlots).catch(() => {});
    fetchVesselStability().then(setVesselStability).catch(() => {});
  }, []);

  useEffect(() => {
    refreshLedger();
    refreshYard();
    refreshAlerts();
    refreshEfficiencyIndex();
    refreshEquipment();
    refreshWorkInstructions();
    refreshVessel();

    const ledgerTimer = setInterval(refreshLedger, POLL_INTERVAL_MS);
    const yardTimer = setInterval(refreshYard, POLL_INTERVAL_MS);
    const alertTimer = setInterval(refreshAlerts, POLL_INTERVAL_MS / 2);
    const efficiencyTimer = setInterval(refreshEfficiencyIndex, POLL_INTERVAL_MS);
    const equipmentTimer = setInterval(refreshEquipment, POLL_INTERVAL_MS);
    const workInstructionsTimer = setInterval(refreshWorkInstructions, POLL_INTERVAL_MS);
    const vesselTimer = setInterval(refreshVessel, POLL_INTERVAL_MS);

    return () => {
      clearInterval(ledgerTimer);
      clearInterval(yardTimer);
      clearInterval(alertTimer);
      clearInterval(efficiencyTimer);
      clearInterval(equipmentTimer);
      clearInterval(workInstructionsTimer);
      clearInterval(vesselTimer);
    };
  }, [refreshLedger, refreshYard, refreshAlerts, refreshEfficiencyIndex, refreshEquipment, refreshWorkInstructions, refreshVessel]);

  function handleTransactionChanged() {
    refreshLedger();
    refreshYard();
    refreshEfficiencyIndex();
    refreshWorkInstructions();
    refreshVessel();
  }

  async function handleExportEdi() {
    setExportError(null);
    try {
      await downloadEdiManifest();
    } catch (err) {
      setExportError(err.message);
    }
  }

  const holdsByContainerId = Object.fromEntries(
    transactions.filter((tx) => tx.holdType).map((tx) => [tx.containerId, tx])
  );

  return (
    <div className="app-shell">
      <header className="app-title-bar">
        <h1>NAVIS-LITE // Yard &amp; Gate Control</h1>
        {efficiencyIndex && (
          <div className="efficiency-index" style={{ color: efficiencyColor(efficiencyIndex.efficiencyIndex) }}>
            Terminal Shuffle Efficiency Index: {efficiencyIndex.efficiencyIndex}%
          </div>
        )}
        <CheckInForm onCheckedIn={handleTransactionChanged} />
        <button className="export-edi-btn" onClick={handleExportEdi}>
          Export EDI Manifest (.edi)
        </button>
        <button className="export-edi-btn" onClick={() => setEquipmentPanelOpen(true)}>
          Equipment Control Center
        </button>
        {exportError && <span className="form-error">{exportError}</span>}
      </header>
      <main className="app-body">
        <OperationalLedger transactions={transactions} onChanged={handleTransactionChanged} />
        <div className="right-panel-container">
          <div className="panel-tabs">
            <button
              className={`panel-tab-btn ${rightPanelTab === "yard" ? "active" : ""}`}
              onClick={() => setRightPanelTab("yard")}
            >
              Digital Twin Yard Matrix
            </button>
            <button
              className={`panel-tab-btn ${rightPanelTab === "vessel" ? "active" : ""}`}
              onClick={() => setRightPanelTab("vessel")}
            >
              Vessel Bayplan View
            </button>
          </div>
          {rightPanelTab === "yard" ? (
            <YardMatrix slots={yardSlots} holdsByContainerId={holdsByContainerId} />
          ) : (
            <VesselBayplan slots={vesselSlots} stability={vesselStability} />
          )}
        </div>
      </main>
      <AlertTicker alerts={alerts} />
      <EquipmentPanel
        open={equipmentPanelOpen}
        onClose={() => setEquipmentPanelOpen(false)}
        equipment={equipment}
        workInstructions={workInstructions}
      />
    </div>
  );
}
