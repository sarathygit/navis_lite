package com.navislite.gateway.service;

import com.navislite.gateway.entity.GateStatus;
import com.navislite.gateway.entity.GateTransaction;
import com.navislite.gateway.repository.GateTransactionRepository;
import org.springframework.stereotype.Service;

import java.time.format.DateTimeFormatter;
import java.util.List;

/**
 * Generates a UN/EDIFACT BAPLIE-style (Bayplan/Stowage Plan) manifest for
 * every container currently DECKED in the yard. This is a plausible, readable
 * segment structure (UNH/BGM/LOC/EQD/UNT with real EDIFACT separators), not a
 * certified/spec-compliant EDI interchange — that level of standards
 * conformance is a much larger effort than this MVP calls for.
 */
@Service
public class EdiBaplieExportService {

    private static final DateTimeFormatter MANIFEST_ID_FORMAT = DateTimeFormatter.ofPattern("yyyyMMddHHmmss");

    private final GateTransactionRepository repository;

    public EdiBaplieExportService(GateTransactionRepository repository) {
        this.repository = repository;
    }

    public String export() {
        List<GateTransaction> decked = repository.findAll().stream()
                .filter(tx -> tx.getStatus() == GateStatus.DECKED)
                .toList();

        String manifestId = java.time.LocalDateTime.now().format(MANIFEST_ID_FORMAT);
        List<String> segments = new java.util.ArrayList<>();

        segments.add("UNH+1+BAPLIE:D:99B:UN'");
        segments.add("BGM+785+" + manifestId + "+9'");
        segments.add("LOC+147+NAVISLITE'");
        segments.add("NAD+CA+NAVISLITE'");

        for (GateTransaction tx : decked) {
            String coordinate = tx.getAssignedBlock()
                    + zeroPad(tx.getAssignedRow())
                    + zeroPad(tx.getAssignedBay())
                    + ":" + tx.getAssignedTier();
            segments.add("LOC+11+" + coordinate + "'");
            segments.add("EQD+CN+" + tx.getContainerId() + "+45G1+++5'");
        }

        segments.add("UNT+" + (segments.size() + 1) + "+1'");

        return String.join("\n", segments) + "\n";
    }

    private String zeroPad(Integer value) {
        if (value == null) {
            return "00";
        }
        return value < 10 ? "0" + value : String.valueOf(value);
    }
}
