package com.navislite.gateway.controller;

import com.navislite.gateway.service.EdiBaplieExportService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(ManifestController.class)
class ManifestControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private EdiBaplieExportService ediBaplieExportService;

    @Test
    void exportEdiReturnsDownloadableManifest() throws Exception {
        when(ediBaplieExportService.export()).thenReturn(
                "UNH+1+BAPLIE:D:99B:UN'\nBGM+785+20260101120000+9'\nUNT+2+1'\n"
        );

        mockMvc.perform(get("/api/manifest/export-edi"))
                .andExpect(status().isOk())
                .andExpect(header().string("Content-Disposition", org.hamcrest.Matchers.containsString("attachment")))
                .andExpect(header().string("Content-Disposition", org.hamcrest.Matchers.containsString(".edi")))
                .andExpect(content().string(org.hamcrest.Matchers.containsString("UNH+1+BAPLIE")));
    }
}
