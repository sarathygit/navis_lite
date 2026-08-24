package com.navislite.gateway.repository;

import com.navislite.gateway.entity.WorkInstruction;
import com.navislite.gateway.entity.WorkInstructionStatus;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface WorkInstructionRepository extends JpaRepository<WorkInstruction, Long> {

    List<WorkInstruction> findByStatusOrderByCreatedAtAsc(WorkInstructionStatus status);

    List<WorkInstruction> findAllByOrderByCreatedAtDesc();
}
