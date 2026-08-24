package com.navislite.gateway.service;

import com.navislite.gateway.entity.TaskType;
import com.navislite.gateway.entity.WorkInstruction;
import com.navislite.gateway.entity.WorkInstructionStatus;
import com.navislite.gateway.repository.WorkInstructionRepository;
import org.springframework.stereotype.Service;

@Service
public class EquipmentDispatchService {

    private final WorkInstructionRepository workInstructionRepository;

    public EquipmentDispatchService(WorkInstructionRepository workInstructionRepository) {
        this.workInstructionRepository = workInstructionRepository;
    }

    public WorkInstruction createWorkInstruction(String containerId, TaskType taskType) {
        WorkInstruction wi = new WorkInstruction();
        wi.setContainerId(containerId);
        wi.setTaskType(taskType);
        wi.setStatus(WorkInstructionStatus.PENDING);
        return workInstructionRepository.save(wi);
    }
}
