package com.navislite.gateway.repository;

import com.navislite.gateway.entity.GateTransaction;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface GateTransactionRepository extends JpaRepository<GateTransaction, Long> {

    Optional<GateTransaction> findByContainerId(String containerId);

    List<GateTransaction> findAllByOrderByCheckInTimeDesc();
}
