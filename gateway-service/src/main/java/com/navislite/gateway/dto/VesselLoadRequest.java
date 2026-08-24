package com.navislite.gateway.dto;

/**
 * Outbound payload sent to the Python decking engine's vessel module
 * (POST {decking-engine}/api/vessel/load).
 */
public class VesselLoadRequest {

    private String containerId;
    private Double weightKg;
    private Integer bay;
    private Integer row;
    private Integer tier;

    public VesselLoadRequest() {
    }

    public VesselLoadRequest(String containerId, Double weightKg, Integer bay, Integer row, Integer tier) {
        this.containerId = containerId;
        this.weightKg = weightKg;
        this.bay = bay;
        this.row = row;
        this.tier = tier;
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
}
