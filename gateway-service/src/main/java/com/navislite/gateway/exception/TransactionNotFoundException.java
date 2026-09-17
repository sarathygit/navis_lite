package com.navislite.gateway.exception;

public class TransactionNotFoundException extends RuntimeException {

    public TransactionNotFoundException(String containerId) {
        super("No container " + containerId + " is currently in the terminal. It may have"
                + " already departed, been loaded, or never been checked in.");
    }
}
