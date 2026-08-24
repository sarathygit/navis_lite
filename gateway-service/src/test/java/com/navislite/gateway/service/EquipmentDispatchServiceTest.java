package com.navislite.gateway.service;

import com.navislite.gateway.entity.TaskType;
import com.navislite.gateway.entity.WorkInstruction;
import com.navislite.gateway.entity.WorkInstructionStatus;
import com.navislite.gateway.repository.WorkInstructionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class EquipmentDispatchServiceTest {

    private WorkInstructionRepository repository;
    private EquipmentDispatchService dispatchService;

    @BeforeEach
    void setUp() {
        repository = mock(WorkInstructionRepository.class);
        dispatchService = new EquipmentDispatchService(repository);
        when(repository.save(any(WorkInstruction.class))).thenAnswer(inv -> inv.getArgument(0));
    }

    @Test
    void createWorkInstructionStartsAsPendingWithNoEquipmentAssigned() {
        WorkInstruction wi = dispatchService.createWorkInstruction("ABCD1234567", TaskType.YARD_PLACEMENT);

        assertEquals("ABCD1234567", wi.getContainerId());
        assertEquals(TaskType.YARD_PLACEMENT, wi.getTaskType());
        assertEquals(WorkInstructionStatus.PENDING, wi.getStatus());
        assertEquals(null, wi.getEquipmentId());
    }
}
