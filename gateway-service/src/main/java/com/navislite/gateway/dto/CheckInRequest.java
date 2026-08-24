package com.navislite.gateway.dto;

import com.navislite.gateway.validation.IsoContainerId;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

import java.time.LocalDateTime;

public class CheckInRequest {

    @IsoContainerId
    private String containerId;

    @NotNull
    @Positive
    private Double weightKg;

    @NotNull
    private Boolean reefer;

    private String destination;

    private LocalDateTime vesselCutoffTime;

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

    public LocalDateTime getVesselCutoffTime() {
        return vesselCutoffTime;
    }

    public void setVesselCutoffTime(LocalDateTime vesselCutoffTime) {
        this.vesselCutoffTime = vesselCutoffTime;
    }
}
