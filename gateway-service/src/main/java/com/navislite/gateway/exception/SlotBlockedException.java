package com.navislite.gateway.exception;

import java.util.List;

public class SlotBlockedException extends RuntimeException {

    private final List<String> blockingContainerIds;

    public SlotBlockedException(String message, List<String> blockingContainerIds) {
        super(message);
        this.blockingContainerIds = blockingContainerIds;
    }

    public List<String> getBlockingContainerIds() {
        return blockingContainerIds;
    }
}
