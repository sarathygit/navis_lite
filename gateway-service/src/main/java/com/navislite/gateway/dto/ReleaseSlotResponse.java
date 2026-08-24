package com.navislite.gateway.dto;

import java.util.List;

/**
 * Inbound payload received from the Python Expert Decking Engine
 * (POST {decking-engine}/api/release-slot).
 */
public class ReleaseSlotResponse {

    private boolean released;
    private String block;
    private Integer row;
    private Integer bay;
    private Integer tier;
    private List<String> blockingContainerIds;
    private String reason;

    public boolean isReleased() {
        return released;
    }

    public void setReleased(boolean released) {
        this.released = released;
    }

    public String getBlock() {
        return block;
    }

    public void setBlock(String block) {
        this.block = block;
    }

    public Integer getRow() {
        return row;
    }

    public void setRow(Integer row) {
        this.row = row;
    }

    public Integer getBay() {
        return bay;
    }

    public void setBay(Integer bay) {
        this.bay = bay;
    }

    public Integer getTier() {
        return tier;
    }

    public void setTier(Integer tier) {
        this.tier = tier;
    }

    public List<String> getBlockingContainerIds() {
        return blockingContainerIds;
    }

    public void setBlockingContainerIds(List<String> blockingContainerIds) {
        this.blockingContainerIds = blockingContainerIds;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }
}
