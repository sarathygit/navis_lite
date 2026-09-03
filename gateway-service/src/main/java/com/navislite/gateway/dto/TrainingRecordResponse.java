package com.navislite.gateway.dto;

import com.navislite.gateway.entity.GateStatus;
import com.navislite.gateway.entity.GateTransaction;

import java.time.LocalDateTime;

/**
 * Raw, unfiltered transaction record served to the decking engine for model
 * training. Deliberately does NOT pre-clean the data: still-in-yard containers
 * (null departureTime) and containers that never got a slot (null assignedTier)
 * are included as-is, so the decking engine can do its own wrangling and
 * censoring decisions rather than having them silently made here.
 */
public class TrainingRecordResponse {

    private String containerId;
    private Double weightKg;
    private Boolean reefer;
    private Integer assignedTier;
    private GateStatus status;
    private LocalDateTime checkInTime;
    private LocalDateTime departureTime;

    public static TrainingRecordResponse fromEntity(GateTransaction tx) {
        TrainingRecordResponse dto = new TrainingRecordResponse();
        dto.containerId = tx.getContainerId();
        dto.weightKg = tx.getWeightKg();
        dto.reefer = tx.getReefer();
        dto.assignedTier = tx.getAssignedTier();
        dto.status = tx.getStatus();
        dto.checkInTime = tx.getCheckInTime();
        dto.departureTime = tx.getDepartureTime();
        return dto;
    }

    public String getContainerId() {
        return containerId;
    }

    public Double getWeightKg() {
        return weightKg;
    }

    public Boolean getReefer() {
        return reefer;
    }

    public Integer getAssignedTier() {
        return assignedTier;
    }

    public GateStatus getStatus() {
        return status;
    }

    public LocalDateTime getCheckInTime() {
        return checkInTime;
    }

    public LocalDateTime getDepartureTime() {
        return departureTime;
    }
}
