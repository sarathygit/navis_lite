package com.navislite.gateway.dto;

import com.navislite.gateway.entity.TaskType;
import com.navislite.gateway.entity.WorkInstruction;
import com.navislite.gateway.entity.WorkInstructionStatus;

import java.time.LocalDateTime;

public class WorkInstructionResponse {

    private Long id;
    private String containerId;
    private Long equipmentId;
    private String equipmentName;
    private TaskType taskType;
    private WorkInstructionStatus status;
    private LocalDateTime createdAt;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;

    public static WorkInstructionResponse fromEntity(WorkInstruction wi, String equipmentName) {
        WorkInstructionResponse dto = new WorkInstructionResponse();
        dto.id = wi.getId();
        dto.containerId = wi.getContainerId();
        dto.equipmentId = wi.getEquipmentId();
        dto.equipmentName = equipmentName;
        dto.taskType = wi.getTaskType();
        dto.status = wi.getStatus();
        dto.createdAt = wi.getCreatedAt();
        dto.startedAt = wi.getStartedAt();
        dto.completedAt = wi.getCompletedAt();
        return dto;
    }

    public Long getId() {
        return id;
    }

    public String getContainerId() {
        return containerId;
    }

    public Long getEquipmentId() {
        return equipmentId;
    }

    public String getEquipmentName() {
        return equipmentName;
    }

    public TaskType getTaskType() {
        return taskType;
    }

    public WorkInstructionStatus getStatus() {
        return status;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public LocalDateTime getStartedAt() {
        return startedAt;
    }

    public LocalDateTime getCompletedAt() {
        return completedAt;
    }
}
