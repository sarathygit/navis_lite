package com.navislite.gateway.exception;

import com.navislite.gateway.entity.GateStatus;

public class DuplicateContainerException extends RuntimeException {

    public DuplicateContainerException(String containerId, GateStatus currentStatus) {
        super("Container " + containerId + " is already in the terminal (" + currentStatus
                + "). Check it out before presenting it at the gate again.");
    }
}
