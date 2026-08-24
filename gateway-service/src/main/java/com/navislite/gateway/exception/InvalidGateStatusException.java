package com.navislite.gateway.exception;

import com.navislite.gateway.entity.GateStatus;

public class InvalidGateStatusException extends RuntimeException {

    public InvalidGateStatusException(String containerId, GateStatus actual, GateStatus required) {
        super("Container " + containerId + " is " + actual + ", expected " + required);
    }
}
