package com.navislite.gateway.dto;

/**
 * Outbound payload sent to the Python Expert Decking Engine
 * (POST {decking-engine}/api/predict-decking).
 */
public class DeckingRequest {

    private String containerId;
    private Double weightKg;
    private Boolean reefer;
    private String destination;

    public DeckingRequest() {
    }

    public DeckingRequest(String containerId, Double weightKg, Boolean reefer, String destination) {
        this.containerId = containerId;
        this.weightKg = weightKg;
        this.reefer = reefer;
        this.destination = destination;
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
}
