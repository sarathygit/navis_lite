package com.navislite.gateway.exception;

public class TransactionNotFoundException extends RuntimeException {

    public TransactionNotFoundException(String containerId) {
        super("No gate transaction found for container " + containerId);
    }
}
