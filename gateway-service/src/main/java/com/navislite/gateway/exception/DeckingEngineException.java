package com.navislite.gateway.exception;

public class DeckingEngineException extends RuntimeException {

    public DeckingEngineException(String message, Throwable cause) {
        super(message, cause);
    }

    public DeckingEngineException(String message) {
        super(message);
    }
}
