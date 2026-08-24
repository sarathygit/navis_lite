package com.navislite.gateway.config;

import com.navislite.gateway.entity.Equipment;
import com.navislite.gateway.entity.EquipmentStatus;
import com.navislite.gateway.entity.EquipmentType;
import com.navislite.gateway.repository.EquipmentRepository;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * Seeds a fixed pool of virtual yard equipment on startup, once. Idempotent —
 * only inserts if the table is empty, so it's safe across container restarts
 * against a persisted MySQL volume.
 */
@Component
public class EquipmentSeeder implements ApplicationRunner {

    private final EquipmentRepository equipmentRepository;

    public EquipmentSeeder(EquipmentRepository equipmentRepository) {
        this.equipmentRepository = equipmentRepository;
    }

    @Override
    public void run(ApplicationArguments args) {
        if (equipmentRepository.count() > 0) {
            return;
        }

        equipmentRepository.saveAll(List.of(
                new Equipment("RTG-01", EquipmentType.RTG, EquipmentStatus.IDLE),
                new Equipment("RTG-02", EquipmentType.RTG, EquipmentStatus.IDLE),
                new Equipment("SC-01", EquipmentType.STRADDLE_CARRIER, EquipmentStatus.IDLE),
                new Equipment("SC-02", EquipmentType.STRADDLE_CARRIER, EquipmentStatus.IDLE)
        ));
    }
}
