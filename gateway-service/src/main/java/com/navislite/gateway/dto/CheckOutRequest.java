package com.navislite.gateway.dto;

import com.navislite.gateway.validation.IsoContainerId;

public class CheckOutRequest {

    @IsoContainerId
    private String containerId;

    public String getContainerId() {
        return containerId;
    }

    public void setContainerId(String containerId) {
        this.containerId = containerId;
    }
}
