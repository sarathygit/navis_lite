package com.navislite.gateway.controller;

import com.navislite.gateway.service.EdiBaplieExportService;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@RestController
@RequestMapping("/api/manifest")
public class ManifestController {

    private static final DateTimeFormatter FILENAME_TIMESTAMP = DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss");

    private final EdiBaplieExportService ediBaplieExportService;

    public ManifestController(EdiBaplieExportService ediBaplieExportService) {
        this.ediBaplieExportService = ediBaplieExportService;
    }

    @GetMapping("/export-edi")
    public ResponseEntity<String> exportEdi() {
        String manifest = ediBaplieExportService.export();
        String filename = "baplie_manifest_" + LocalDateTime.now().format(FILENAME_TIMESTAMP) + ".edi";

        ContentDisposition contentDisposition = ContentDisposition.attachment()
                .filename(filename)
                .build();

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, contentDisposition.toString())
                .contentType(MediaType.TEXT_PLAIN)
                .body(manifest);
    }
}
