package com.navislite.gateway.entity;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "gate_transactions")
public class GateTransaction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // Deliberately NOT unique. A container is a reusable steel box: it leaves the
    // terminal and comes back weeks later, and a container turned away at the gate
    // may be re-presented once space frees up. Each visit is its own row, so the
    // ledger keeps full history and the dwell model gets every completed visit as
    // a training example. Only one visit may be *active* at a time — enforced in
    // GateService.checkIn rather than by the schema.
    @Column(name = "container_id", nullable = false, length = 11)
    private String containerId;

    @Column(name = "weight_kg", nullable = false)
    private Double weightKg;

    @Column(name = "reefer", nullable = false)
    private Boolean reefer;

    @Column(name = "destination")
    private String destination;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, columnDefinition = "VARCHAR(20)")
    private GateStatus status;

    @Column(name = "assigned_block")
    private String assignedBlock;

    @Column(name = "assigned_row")
    private Integer assignedRow;

    @Column(name = "assigned_bay")
    private Integer assignedBay;

    @Column(name = "assigned_tier")
    private Integer assignedTier;

    @Column(name = "dwell_time_estimate")
    private Double dwellTimeEstimate;

    @Column(name = "shuffle_risk_score")
    private Double shuffleRiskScore;

    @Column(name = "penalty_flag", length = 10)
    private String penaltyFlag;

    @CreationTimestamp
    @Column(name = "check_in_time", updatable = false)
    private LocalDateTime checkInTime;

    @Column(name = "departure_time")
    private LocalDateTime departureTime;

    @Enumerated(EnumType.STRING)
    @Column(name = "hold_type", columnDefinition = "VARCHAR(30)")
    private HoldType holdType;

    @Column(name = "hold_reason")
    private String holdReason;

    @Column(name = "vessel_cutoff_time")
    private LocalDateTime vesselCutoffTime;

    @Column(name = "vessel_bay")
    private Integer vesselBay;

    @Column(name = "vessel_row")
    private Integer vesselRow;

    @Column(name = "vessel_tier")
    private Integer vesselTier;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    public GateTransaction() {
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getContainerId() {
        return containerId;
    }

    public void setContainerId(String containerId) {
        this.containerId = containerId;
    }

    public Double getWeightKg() {
        return weightKg;
    }

    public void setWeightKg(Double weightKg) {
        this.weightKg = weightKg;
    }

    public Boolean getReefer() {
        return reefer;
    }

    public void setReefer(Boolean reefer) {
        this.reefer = reefer;
    }

    public String getDestination() {
        return destination;
    }

    public void setDestination(String destination) {
        this.destination = destination;
    }

    public GateStatus getStatus() {
        return status;
    }

    public void setStatus(GateStatus status) {
        this.status = status;
    }

    public String getAssignedBlock() {
        return assignedBlock;
    }

    public void setAssignedBlock(String assignedBlock) {
        this.assignedBlock = assignedBlock;
    }

    public Integer getAssignedRow() {
        return assignedRow;
    }

    public void setAssignedRow(Integer assignedRow) {
        this.assignedRow = assignedRow;
    }

    public Integer getAssignedBay() {
        return assignedBay;
    }

    public void setAssignedBay(Integer assignedBay) {
        this.assignedBay = assignedBay;
    }

    public Integer getAssignedTier() {
        return assignedTier;
    }

    public void setAssignedTier(Integer assignedTier) {
        this.assignedTier = assignedTier;
    }

    public Double getDwellTimeEstimate() {
        return dwellTimeEstimate;
    }

    public void setDwellTimeEstimate(Double dwellTimeEstimate) {
        this.dwellTimeEstimate = dwellTimeEstimate;
    }

    public Double getShuffleRiskScore() {
        return shuffleRiskScore;
    }

    public void setShuffleRiskScore(Double shuffleRiskScore) {
        this.shuffleRiskScore = shuffleRiskScore;
    }

    public String getPenaltyFlag() {
        return penaltyFlag;
    }

    public void setPenaltyFlag(String penaltyFlag) {
        this.penaltyFlag = penaltyFlag;
    }

    public LocalDateTime getCheckInTime() {
        return checkInTime;
    }

    public LocalDateTime getDepartureTime() {
        return departureTime;
    }

    public void setDepartureTime(LocalDateTime departureTime) {
        this.departureTime = departureTime;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public HoldType getHoldType() {
        return holdType;
    }

    public void setHoldType(HoldType holdType) {
        this.holdType = holdType;
    }

    public String getHoldReason() {
        return holdReason;
    }

    public void setHoldReason(String holdReason) {
        this.holdReason = holdReason;
    }

    public LocalDateTime getVesselCutoffTime() {
        return vesselCutoffTime;
    }

    public void setVesselCutoffTime(LocalDateTime vesselCutoffTime) {
        this.vesselCutoffTime = vesselCutoffTime;
    }

    public Integer getVesselBay() {
        return vesselBay;
    }

    public void setVesselBay(Integer vesselBay) {
        this.vesselBay = vesselBay;
    }

    public Integer getVesselRow() {
        return vesselRow;
    }

    public void setVesselRow(Integer vesselRow) {
        this.vesselRow = vesselRow;
    }

    public Integer getVesselTier() {
        return vesselTier;
    }

    public void setVesselTier(Integer vesselTier) {
        this.vesselTier = vesselTier;
    }
}
