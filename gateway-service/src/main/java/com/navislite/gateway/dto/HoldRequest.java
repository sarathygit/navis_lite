package com.navislite.gateway.dto;

import com.navislite.gateway.entity.HoldType;
import jakarta.validation.constraints.NotNull;

public class HoldRequest {

    @NotNull
    private HoldType holdType;

    private String reason;

    public HoldType getHoldType() {
        return holdType;
    }

    public void setHoldType(HoldType holdType) {
        this.holdType = holdType;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }
}
