package com.navislite.gateway.dto;

/**
 * Inbound payload received from the Python decking engine's vessel module
 * (POST {decking-engine}/api/vessel/load).
 */
public class VesselLoadResponse {

    private boolean loaded;
    private Integer bay;
    private Integer row;
    private Integer tier;
    private boolean stabilityWarning;
    private String warningMessage;
    private Double totalDeckWeight;
    private String reason;

    public boolean isLoaded() {
        return loaded;
    }

    public void setLoaded(boolean loaded) {
        this.loaded = loaded;
    }

    public Integer getBay() {
        return bay;
    }

    public void setBay(Integer bay) {
        this.bay = bay;
    }

    public Integer getRow() {
        return row;
    }

    public void setRow(Integer row) {
        this.row = row;
    }

    public Integer getTier() {
        return tier;
    }

    public void setTier(Integer tier) {
        this.tier = tier;
    }

    public boolean isStabilityWarning() {
        return stabilityWarning;
    }

    public void setStabilityWarning(boolean stabilityWarning) {
        this.stabilityWarning = stabilityWarning;
    }

    public String getWarningMessage() {
        return warningMessage;
    }

    public void setWarningMessage(String warningMessage) {
        this.warningMessage = warningMessage;
    }

    public Double getTotalDeckWeight() {
        return totalDeckWeight;
    }

    public void setTotalDeckWeight(Double totalDeckWeight) {
        this.totalDeckWeight = totalDeckWeight;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }
}
