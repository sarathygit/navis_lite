package com.navislite.gateway.dto;

import com.navislite.gateway.entity.Equipment;
import com.navislite.gateway.entity.EquipmentStatus;
import com.navislite.gateway.entity.EquipmentType;

public class EquipmentResponse {

    private Long id;
    private String name;
    private EquipmentType type;
    private EquipmentStatus status;

    public static EquipmentResponse fromEntity(Equipment equipment) {
        EquipmentResponse dto = new EquipmentResponse();
        dto.id = equipment.getId();
        dto.name = equipment.getName();
        dto.type = equipment.getType();
        dto.status = equipment.getStatus();
        return dto;
    }

    public Long getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public EquipmentType getType() {
        return type;
    }

    public EquipmentStatus getStatus() {
        return status;
    }
}
