package com.navislite.gateway.dto;

/**
 * Asks the decking engine to put a container back in the slot it was just
 * lifted from, after a vessel load was refused.
 */
public class RestoreSlotRequest {

    private String containerId;
    private Double weightKg;
    private Boolean reefer;
    private Double dwellTimeEstimate;
    private String block;
    private Integer row;
    private Integer bay;
    private Integer tier;

    public RestoreSlotRequest() {
    }

    public RestoreSlotRequest(String containerId, Double weightKg, Boolean reefer, Double dwellTimeEstimate,
                               String block, Integer row, Integer bay, Integer tier) {
        this.containerId = containerId;
        this.weightKg = weightKg;
        this.reefer = reefer;
        this.dwellTimeEstimate = dwellTimeEstimate;
        this.block = block;
        this.row = row;
        this.bay = bay;
        this.tier = tier;
    }

    public String getContainerId() { return containerId; }
    public void setContainerId(String v) { this.containerId = v; }
    public Double getWeightKg() { return weightKg; }
    public void setWeightKg(Double v) { this.weightKg = v; }
    public Boolean getReefer() { return reefer; }
    public void setReefer(Boolean v) { this.reefer = v; }
    public Double getDwellTimeEstimate() { return dwellTimeEstimate; }
    public void setDwellTimeEstimate(Double v) { this.dwellTimeEstimate = v; }
    public String getBlock() { return block; }
    public void setBlock(String v) { this.block = v; }
    public Integer getRow() { return row; }
    public void setRow(Integer v) { this.row = v; }
    public Integer getBay() { return bay; }
    public void setBay(Integer v) { this.bay = v; }
    public Integer getTier() { return tier; }
    public void setTier(Integer v) { this.tier = v; }
}
