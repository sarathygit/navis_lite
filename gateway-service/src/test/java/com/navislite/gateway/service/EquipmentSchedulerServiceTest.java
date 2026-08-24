package com.navislite.gateway.service;

import com.navislite.gateway.entity.*;
import com.navislite.gateway.repository.EquipmentRepository;
import com.navislite.gateway.repository.WorkInstructionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class EquipmentSchedulerServiceTest {

    private EquipmentRepository equipmentRepository;
    private WorkInstructionRepository workInstructionRepository;
    private EquipmentSchedulerService scheduler;

    @BeforeEach
    void setUp() {
        equipmentRepository = mock(EquipmentRepository.class);
        workInstructionRepository = mock(WorkInstructionRepository.class);
        scheduler = new EquipmentSchedulerService(equipmentRepository, workInstructionRepository);

        when(equipmentRepository.save(any(Equipment.class))).thenAnswer(inv -> inv.getArgument(0));
        when(workInstructionRepository.save(any(WorkInstruction.class))).thenAnswer(inv -> inv.getArgument(0));
    }

    private Equipment idleEquipment(long id) {
        Equipment equipment = new Equipment("RTG-0" + id, EquipmentType.RTG, EquipmentStatus.IDLE);
        equipment.setId(id);
        return equipment;
    }

    private WorkInstruction pendingWorkInstruction(String containerId) {
        WorkInstruction wi = new WorkInstruction();
        wi.setId(1L);
        wi.setContainerId(containerId);
        wi.setTaskType(TaskType.YARD_PLACEMENT);
        wi.setStatus(WorkInstructionStatus.PENDING);
        return wi;
    }

    @Test
    void tickAssignsPendingWorkInstructionToIdleEquipment() {
        Equipment equipment = idleEquipment(1);
        WorkInstruction wi = pendingWorkInstruction("ABCD1234567");

        when(workInstructionRepository.findByStatusOrderByCreatedAtAsc(WorkInstructionStatus.PENDING))
                .thenReturn(new ArrayList<>(List.of(wi)));
        when(workInstructionRepository.findByStatusOrderByCreatedAtAsc(WorkInstructionStatus.WORKING))
                .thenReturn(List.of());
        when(equipmentRepository.findByStatus(EquipmentStatus.IDLE)).thenReturn(List.of(equipment));

        scheduler.tick();

        assertEquals(WorkInstructionStatus.WORKING, wi.getStatus());
        assertEquals(1L, wi.getEquipmentId());
        assertNotNull(wi.getStartedAt());
        assertEquals(EquipmentStatus.WORKING, equipment.getStatus());
    }

    @Test
    void tickLeavesWorkInstructionPendingWhenNoEquipmentIsIdle() {
        WorkInstruction wi = pendingWorkInstruction("ABCD1234567");

        when(workInstructionRepository.findByStatusOrderByCreatedAtAsc(WorkInstructionStatus.PENDING))
                .thenReturn(new ArrayList<>(List.of(wi)));
        when(workInstructionRepository.findByStatusOrderByCreatedAtAsc(WorkInstructionStatus.WORKING))
                .thenReturn(List.of());
        when(equipmentRepository.findByStatus(EquipmentStatus.IDLE)).thenReturn(List.of());

        scheduler.tick();

        assertEquals(WorkInstructionStatus.PENDING, wi.getStatus());
        assertNull(wi.getEquipmentId());
    }

    @Test
    void tickCompletesWorkInstructionOnceSimulatedDurationHasElapsed() {
        Equipment equipment = idleEquipment(1);
        equipment.setStatus(EquipmentStatus.WORKING);

        WorkInstruction wi = new WorkInstruction();
        wi.setId(2L);
        wi.setContainerId("ABCD1234567");
        wi.setTaskType(TaskType.YARD_PLACEMENT);
        wi.setStatus(WorkInstructionStatus.WORKING);
        wi.setEquipmentId(1L);
        wi.setStartedAt(LocalDateTime.now().minusSeconds(30)); // well past the 8s simulated duration

        when(workInstructionRepository.findByStatusOrderByCreatedAtAsc(WorkInstructionStatus.PENDING))
                .thenReturn(List.of());
        when(workInstructionRepository.findByStatusOrderByCreatedAtAsc(WorkInstructionStatus.WORKING))
                .thenReturn(List.of(wi));
        when(equipmentRepository.findById(1L)).thenReturn(Optional.of(equipment));

        scheduler.tick();

        assertEquals(WorkInstructionStatus.COMPLETED, wi.getStatus());
        assertNotNull(wi.getCompletedAt());
        assertEquals(EquipmentStatus.IDLE, equipment.getStatus());
    }

    @Test
    void tickDoesNotCompleteWorkInstructionBeforeSimulatedDurationElapses() {
        WorkInstruction wi = new WorkInstruction();
        wi.setId(2L);
        wi.setContainerId("ABCD1234567");
        wi.setTaskType(TaskType.YARD_PLACEMENT);
        wi.setStatus(WorkInstructionStatus.WORKING);
        wi.setEquipmentId(1L);
        wi.setStartedAt(LocalDateTime.now()); // just started

        when(workInstructionRepository.findByStatusOrderByCreatedAtAsc(WorkInstructionStatus.PENDING))
                .thenReturn(List.of());
        when(workInstructionRepository.findByStatusOrderByCreatedAtAsc(WorkInstructionStatus.WORKING))
                .thenReturn(List.of(wi));

        scheduler.tick();

        assertEquals(WorkInstructionStatus.WORKING, wi.getStatus());
        assertNull(wi.getCompletedAt());
        verify(equipmentRepository, never()).findById(any());
    }
}
