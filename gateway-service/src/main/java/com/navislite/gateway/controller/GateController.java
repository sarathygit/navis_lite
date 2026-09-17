package com.navislite.gateway.controller;

import com.navislite.gateway.dto.CheckInOutcome;
import com.navislite.gateway.dto.CheckInRequest;
import com.navislite.gateway.dto.CheckInResponse;
import com.navislite.gateway.dto.CheckOutRequest;
import com.navislite.gateway.dto.HoldRequest;
import com.navislite.gateway.dto.LoadToVesselRequest;
import com.navislite.gateway.dto.TrainingRecordResponse;
import com.navislite.gateway.entity.GateTransaction;
import com.navislite.gateway.service.GateService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/gate")
public class GateController {

    private final GateService gateService;

    public GateController(GateService gateService) {
        this.gateService = gateService;
    }

    @PostMapping("/check-in")
    public ResponseEntity<CheckInResponse> checkIn(@Valid @RequestBody CheckInRequest request) {
        CheckInOutcome outcome = gateService.checkIn(request);
        CheckInResponse body = CheckInResponse.fromEntity(outcome.transaction());
        body.setSuggestion(outcome.suggestion());
        return ResponseEntity.status(HttpStatus.CREATED).body(body);
    }

    @PostMapping("/check-out")
    public ResponseEntity<CheckInResponse> checkOut(@Valid @RequestBody CheckOutRequest request) {
        GateTransaction tx = gateService.checkOut(request.getContainerId());
        return ResponseEntity.ok(CheckInResponse.fromEntity(tx));
    }

    @PostMapping("/{containerId}/hold")
    public ResponseEntity<CheckInResponse> applyHold(@PathVariable String containerId,
                                                       @Valid @RequestBody HoldRequest request) {
        GateTransaction tx = gateService.applyHold(containerId, request.getHoldType(), request.getReason());
        return ResponseEntity.ok(CheckInResponse.fromEntity(tx));
    }

    @DeleteMapping("/{containerId}/hold")
    public ResponseEntity<CheckInResponse> clearHold(@PathVariable String containerId) {
        GateTransaction tx = gateService.clearHold(containerId);
        return ResponseEntity.ok(CheckInResponse.fromEntity(tx));
    }

    @PostMapping("/load-to-vessel")
    public ResponseEntity<CheckInResponse> loadToVessel(@Valid @RequestBody LoadToVesselRequest request) {
        GateTransaction tx = gateService.loadToVessel(request.getContainerId(), request.getBay(),
                request.getRow(), request.getTier());
        return ResponseEntity.ok(CheckInResponse.fromEntity(tx));
    }

    @GetMapping("/transactions")
    public ResponseEntity<List<CheckInResponse>> listTransactions() {
        List<CheckInResponse> body = gateService.listTransactions().stream()
                .map(CheckInResponse::fromEntity)
                .toList();
        return ResponseEntity.ok(body);
    }

    /**
     * Raw transaction history for model training. Consumed by the decking engine,
     * which does its own cleaning, censoring and feature engineering.
     */
    @GetMapping("/training-data")
    public ResponseEntity<List<TrainingRecordResponse>> trainingData() {
        List<TrainingRecordResponse> body = gateService.listTransactions().stream()
                .map(TrainingRecordResponse::fromEntity)
                .toList();
        return ResponseEntity.ok(body);
    }

    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("OK");
    }
}
