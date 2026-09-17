package com.navislite.gateway.repository;

import com.navislite.gateway.entity.GateStatus;
import com.navislite.gateway.entity.GateTransaction;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Collection;
import java.util.List;
import java.util.Optional;

public interface GateTransactionRepository extends JpaRepository<GateTransaction, Long> {

    /**
     * The container's current visit, if it is still in the terminal.
     *
     * A container may appear many times in the ledger — once per visit — but only
     * the most recent one can be active. Terminal states (REJECTED, DEPARTED,
     * LOADED) are finished visits and must not be returned here, otherwise a
     * returning container could never be checked in again.
     */
    Optional<GateTransaction> findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(
            String containerId, Collection<GateStatus> statuses);

    List<GateTransaction> findAllByOrderByCheckInTimeDesc();
}
