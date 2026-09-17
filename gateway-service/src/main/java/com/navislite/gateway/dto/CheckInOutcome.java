package com.navislite.gateway.dto;

import com.navislite.gateway.entity.GateTransaction;

/**
 * The result of a gate check-in: the persisted transaction, plus — only when the
 * container was rejected — advice on the housekeeping move that would make room.
 *
 * The suggestion is about the yard's current shape rather than a fact about this
 * container, so it is returned with the response instead of being stored on the row.
 */
public record CheckInOutcome(GateTransaction transaction, RelocationSuggestion suggestion) {

    public static CheckInOutcome placed(GateTransaction transaction) {
        return new CheckInOutcome(transaction, null);
    }
}
