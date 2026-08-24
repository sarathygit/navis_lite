package com.navislite.gateway.dto;

/**
 * Outbound payload sent to the Python Expert Decking Engine
 * (POST {decking-engine}/api/release-slot).
 */
public class ReleaseSlotRequest {

    private String containerId;

    public ReleaseSlotRequest() {
    }

    public ReleaseSlotRequest(String containerId) {
        this.containerId = containerId;
    }

    public String getContainerId() {
        return containerId;
    }

    public void setContainerId(String containerId) {
        this.containerId = containerId;
    }
}
