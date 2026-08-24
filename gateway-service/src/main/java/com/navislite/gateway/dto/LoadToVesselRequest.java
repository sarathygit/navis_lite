package com.navislite.gateway.dto;

import com.navislite.gateway.validation.IsoContainerId;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

public class LoadToVesselRequest {

    @IsoContainerId
    private String containerId;

    @NotNull
    @Min(1)
    private Integer bay;

    @NotNull
    @Min(1)
    private Integer row;

    @NotNull
    @Min(1)
    private Integer tier;

    public String getContainerId() {
        return containerId;
    }

    public void setContainerId(String containerId) {
        this.containerId = containerId;
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
