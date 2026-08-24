package com.navislite.gateway.service;

import com.navislite.gateway.entity.Equipment;
import com.navislite.gateway.entity.EquipmentStatus;
import com.navislite.gateway.entity.WorkInstruction;
import com.navislite.gateway.entity.WorkInstructionStatus;
import com.navislite.gateway.repository.EquipmentRepository;
import com.navislite.gateway.repository.WorkInstructionRepository;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Iterator;
import java.util.List;

/**
 * Simulates a crane floor: dispatches PENDING work instructions to IDLE
 * equipment, then auto-completes WORKING instructions after a fixed simulated
 * duration, freeing their equipment back to IDLE. Mirrors the background
 * reefer-telemetry thread pattern already used in the Python decking engine —
 * this is the Java-side equivalent of a live simulation loop.
 */
@Service
public class EquipmentSchedulerService {

    private static final long SIMULATED_JOB_DURATION_SECONDS = 8;

    private final EquipmentRepository equipmentRepository;
    private final WorkInstructionRepository workInstructionRepository;

    public EquipmentSchedulerService(EquipmentRepository equipmentRepository,
                                      WorkInstructionRepository workInstructionRepository) {
        this.equipmentRepository = equipmentRepository;
        this.workInstructionRepository = workInstructionRepository;
    }

    @Scheduled(fixedRate = 3000)
    public void scheduledTick() {
        tick();
    }

    @Transactional
    public void tick() {
        assignPendingWorkToIdleEquipment();
        completeFinishedWork();
    }

    private void assignPendingWorkToIdleEquipment() {
        List<WorkInstruction> pending = workInstructionRepository.findByStatusOrderByCreatedAtAsc(WorkInstructionStatus.PENDING);
        if (pending.isEmpty()) {
            return;
        }

        Iterator<Equipment> idleEquipment = equipmentRepository.findByStatus(EquipmentStatus.IDLE).iterator();

        for (WorkInstruction wi : pending) {
            if (!idleEquipment.hasNext()) {
                break;
            }
            Equipment equipment = idleEquipment.next();

            wi.setEquipmentId(equipment.getId());
            wi.setStatus(WorkInstructionStatus.WORKING);
            wi.setStartedAt(LocalDateTime.now());
            workInstructionRepository.save(wi);

            equipment.setStatus(EquipmentStatus.WORKING);
            equipmentRepository.save(equipment);
        }
    }

    private void completeFinishedWork() {
        LocalDateTime cutoff = LocalDateTime.now().minusSeconds(SIMULATED_JOB_DURATION_SECONDS);
        List<WorkInstruction> working = workInstructionRepository.findByStatusOrderByCreatedAtAsc(WorkInstructionStatus.WORKING);

        for (WorkInstruction wi : working) {
            if (wi.getStartedAt() == null || wi.getStartedAt().isAfter(cutoff)) {
                continue;
            }

            wi.setStatus(WorkInstructionStatus.COMPLETED);
            wi.setCompletedAt(LocalDateTime.now());
            workInstructionRepository.save(wi);

            if (wi.getEquipmentId() != null) {
                equipmentRepository.findById(wi.getEquipmentId()).ifPresent(equipment -> {
                    equipment.setStatus(EquipmentStatus.IDLE);
                    equipmentRepository.save(equipment);
                });
            }
        }
    }
}
