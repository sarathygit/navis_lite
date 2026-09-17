package com.navislite.gateway.dto;

import com.navislite.gateway.entity.GateStatus;
import com.navislite.gateway.entity.GateTransaction;
import com.navislite.gateway.entity.HoldType;

import java.time.LocalDateTime;

public class CheckInResponse {

    private Long id;
    private String containerId;
    private Double weightKg;
    private Boolean reefer;
    private String destination;
    private GateStatus status;
    private String assignedBlock;
    private Integer assignedRow;
    private Integer assignedBay;
    private Integer assignedTier;
    private Double dwellTimeEstimate;
    private Double shuffleRiskScore;
    private String penaltyFlag;
    private LocalDateTime checkInTime;
    private LocalDateTime departureTime;
    private HoldType holdType;
    private String holdReason;
    private LocalDateTime vesselCutoffTime;
    private Integer vesselBay;
    private Integer vesselRow;
    private Integer vesselTier;
    private RelocationSuggestion suggestion;

    public static CheckInResponse fromEntity(GateTransaction tx) {
        CheckInResponse dto = new CheckInResponse();
        dto.id = tx.getId();
        dto.containerId = tx.getContainerId();
        dto.weightKg = tx.getWeightKg();
        dto.reefer = tx.getReefer();
        dto.destination = tx.getDestination();
        dto.status = tx.getStatus();
        dto.assignedBlock = tx.getAssignedBlock();
        dto.assignedRow = tx.getAssignedRow();
        dto.assignedBay = tx.getAssignedBay();
        dto.assignedTier = tx.getAssignedTier();
        dto.dwellTimeEstimate = tx.getDwellTimeEstimate();
        dto.shuffleRiskScore = tx.getShuffleRiskScore();
        dto.penaltyFlag = tx.getPenaltyFlag();
        dto.checkInTime = tx.getCheckInTime();
        dto.departureTime = tx.getDepartureTime();
        dto.holdType = tx.getHoldType();
        dto.holdReason = tx.getHoldReason();
        dto.vesselCutoffTime = tx.getVesselCutoffTime();
        dto.vesselBay = tx.getVesselBay();
        dto.vesselRow = tx.getVesselRow();
        dto.vesselTier = tx.getVesselTier();
        return dto;
    }

    public Long getId() {
        return id;
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

    public String getDestination() {
        return destination;
    }

    public GateStatus getStatus() {
        return status;
    }

    public String getAssignedBlock() {
        return assignedBlock;
    }

    public Integer getAssignedRow() {
        return assignedRow;
    }

    public Integer getAssignedBay() {
        return assignedBay;
    }

    public Integer getAssignedTier() {
        return assignedTier;
    }

    public Double getDwellTimeEstimate() {
        return dwellTimeEstimate;
    }

    public Double getShuffleRiskScore() {
        return shuffleRiskScore;
    }

    public String getPenaltyFlag() {
        return penaltyFlag;
    }

    public LocalDateTime getCheckInTime() {
        return checkInTime;
    }

    public LocalDateTime getDepartureTime() {
        return departureTime;
    }

    public HoldType getHoldType() {
        return holdType;
    }

    public String getHoldReason() {
        return holdReason;
    }

    public LocalDateTime getVesselCutoffTime() {
        return vesselCutoffTime;
    }

    public Integer getVesselBay() {
        return vesselBay;
    }

    public Integer getVesselRow() {
        return vesselRow;
    }

    public Integer getVesselTier() {
        return vesselTier;
    }

    public RelocationSuggestion getSuggestion() {
        return suggestion;
    }

    public void setSuggestion(RelocationSuggestion suggestion) {
        this.suggestion = suggestion;
    }
}
