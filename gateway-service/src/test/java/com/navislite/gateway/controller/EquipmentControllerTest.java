package com.navislite.gateway.controller;

import com.navislite.gateway.entity.*;
import com.navislite.gateway.repository.EquipmentRepository;
import com.navislite.gateway.repository.WorkInstructionRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(EquipmentController.class)
class EquipmentControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private EquipmentRepository equipmentRepository;

    @MockBean
    private WorkInstructionRepository workInstructionRepository;

    @Test
    void listEquipmentReturnsSeededPool() throws Exception {
        Equipment rtg = new Equipment("RTG-01", EquipmentType.RTG, EquipmentStatus.IDLE);
        rtg.setId(1L);
        when(equipmentRepository.findAll()).thenReturn(List.of(rtg));

        mockMvc.perform(get("/api/equipment"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].name").value("RTG-01"))
                .andExpect(jsonPath("$[0].status").value("IDLE"));
    }

    @Test
    void listWorkInstructionsIncludesEquipmentNameLookup() throws Exception {
        Equipment rtg = new Equipment("RTG-01", EquipmentType.RTG, EquipmentStatus.WORKING);
        rtg.setId(1L);

        WorkInstruction wi = new WorkInstruction();
        wi.setId(1L);
        wi.setContainerId("ABCD1234567");
        wi.setTaskType(TaskType.YARD_PLACEMENT);
        wi.setStatus(WorkInstructionStatus.WORKING);
        wi.setEquipmentId(1L);

        when(equipmentRepository.findAll()).thenReturn(List.of(rtg));
        when(workInstructionRepository.findAllByOrderByCreatedAtDesc()).thenReturn(List.of(wi));

        mockMvc.perform(get("/api/work-instructions"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].containerId").value("ABCD1234567"))
                .andExpect(jsonPath("$[0].equipmentName").value("RTG-01"));
    }
}
