package com.navislite.gateway.exception;

import com.navislite.gateway.entity.HoldType;

public class ActiveHoldException extends RuntimeException {

    public ActiveHoldException(String containerId, HoldType holdType, String holdReason) {
        super("Container " + containerId + " has an active " + holdType
                + (holdReason != null && !holdReason.isBlank() ? " (" + holdReason + ")" : ""));
    }
}
