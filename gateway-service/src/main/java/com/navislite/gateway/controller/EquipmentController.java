package com.navislite.gateway.controller;

import com.navislite.gateway.dto.EquipmentResponse;
import com.navislite.gateway.dto.WorkInstructionResponse;
import com.navislite.gateway.entity.Equipment;
import com.navislite.gateway.repository.EquipmentRepository;
import com.navislite.gateway.repository.WorkInstructionRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public class EquipmentController {

    private final EquipmentRepository equipmentRepository;
    private final WorkInstructionRepository workInstructionRepository;

    public EquipmentController(EquipmentRepository equipmentRepository,
                                WorkInstructionRepository workInstructionRepository) {
        this.equipmentRepository = equipmentRepository;
        this.workInstructionRepository = workInstructionRepository;
    }

    @GetMapping("/equipment")
    public ResponseEntity<List<EquipmentResponse>> listEquipment() {
        List<EquipmentResponse> body = equipmentRepository.findAll().stream()
                .map(EquipmentResponse::fromEntity)
                .toList();
        return ResponseEntity.ok(body);
    }

    @GetMapping("/work-instructions")
    public ResponseEntity<List<WorkInstructionResponse>> listWorkInstructions() {
        Map<Long, String> equipmentNames = equipmentRepository.findAll().stream()
                .collect(Collectors.toMap(Equipment::getId, Equipment::getName));

        List<WorkInstructionResponse> body = workInstructionRepository.findAllByOrderByCreatedAtDesc().stream()
                .map(wi -> WorkInstructionResponse.fromEntity(wi, equipmentNames.get(wi.getEquipmentId())))
                .toList();
        return ResponseEntity.ok(body);
    }
}
