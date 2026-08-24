package com.navislite.gateway.repository;

import com.navislite.gateway.entity.Equipment;
import com.navislite.gateway.entity.EquipmentStatus;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface EquipmentRepository extends JpaRepository<Equipment, Long> {

    List<Equipment> findByStatus(EquipmentStatus status);
}
