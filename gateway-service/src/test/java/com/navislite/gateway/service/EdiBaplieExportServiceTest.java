package com.navislite.gateway.service;

import com.navislite.gateway.entity.GateStatus;
import com.navislite.gateway.entity.GateTransaction;
import com.navislite.gateway.repository.GateTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class EdiBaplieExportServiceTest {

    private GateTransactionRepository repository;
    private EdiBaplieExportService exportService;

    @BeforeEach
    void setUp() {
        repository = mock(GateTransactionRepository.class);
        exportService = new EdiBaplieExportService(repository);
    }

    private GateTransaction decked(String containerId, String block, int row, int bay, int tier) {
        GateTransaction tx = new GateTransaction();
        tx.setContainerId(containerId);
        tx.setWeightKg(15000.0);
        tx.setReefer(false);
        tx.setStatus(GateStatus.DECKED);
        tx.setAssignedBlock(block);
        tx.setAssignedRow(row);
        tx.setAssignedBay(bay);
        tx.setAssignedTier(tier);
        return tx;
    }

    @Test
    void exportIncludesEnvelopeSegmentsAndOneEqdPerDeckedContainer() {
        GateTransaction rejected = new GateTransaction();
        rejected.setContainerId("ZZZZ0000000");
        rejected.setWeightKg(1.0);
        rejected.setReefer(false);
        rejected.setStatus(GateStatus.REJECTED);

        when(repository.findAll()).thenReturn(List.of(
                decked("ABCD1234567", "A", 1, 2, 3),
                decked("MSKU9070323", "R", 2, 1, 1),
                rejected
        ));

        String manifest = exportService.export();

        assertTrue(manifest.startsWith("UNH+1+BAPLIE:D:99B:UN'"));
        assertTrue(manifest.contains("BGM+785+"));
        assertTrue(manifest.contains("LOC+147+NAVISLITE'"));
        assertTrue(manifest.contains("NAD+CA+NAVISLITE'"));
        assertTrue(manifest.contains("LOC+11+A0102:3'"));
        assertTrue(manifest.contains("EQD+CN+ABCD1234567+45G1+++5'"));
        assertTrue(manifest.contains("LOC+11+R0201:1'"));
        assertTrue(manifest.contains("EQD+CN+MSKU9070323+45G1+++5'"));
        assertTrue(manifest.trim().endsWith("'"));
        assertFalse(manifest.contains("ZZZZ0000000"), "rejected containers have no yard coordinate and must be excluded");

        long eqdCount = manifest.lines().filter(line -> line.startsWith("EQD+")).count();
        assertEquals(2, eqdCount);
    }

    @Test
    void exportWithNoDeckedContainersStillProducesAValidEnvelope() {
        when(repository.findAll()).thenReturn(List.of());

        String manifest = exportService.export();

        assertTrue(manifest.contains("UNH+1+BAPLIE:D:99B:UN'"));
        assertTrue(manifest.contains("UNT+"));
        assertFalse(manifest.contains("EQD+"));
    }
}
