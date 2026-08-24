package com.navislite.gateway.exception;

public class DuplicateContainerException extends RuntimeException {

    public DuplicateContainerException(String containerId) {
        super("Container " + containerId + " already has an active gate transaction");
    }
}
