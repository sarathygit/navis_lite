package com.navislite.gateway.service;

import com.navislite.gateway.dto.CheckInRequest;
import com.navislite.gateway.dto.DeckingRequest;
import com.navislite.gateway.dto.DeckingResponse;
import com.navislite.gateway.dto.ReleaseSlotRequest;
import com.navislite.gateway.dto.ReleaseSlotResponse;
import com.navislite.gateway.dto.VesselLoadRequest;
import com.navislite.gateway.dto.VesselLoadResponse;
import com.navislite.gateway.entity.GateStatus;
import com.navislite.gateway.entity.GateTransaction;
import com.navislite.gateway.entity.HoldType;
import com.navislite.gateway.entity.TaskType;
import com.navislite.gateway.exception.ActiveHoldException;
import com.navislite.gateway.exception.DuplicateContainerException;
import com.navislite.gateway.exception.InvalidGateStatusException;
import com.navislite.gateway.exception.SlotBlockedException;
import com.navislite.gateway.exception.TransactionNotFoundException;
import com.navislite.gateway.exception.VesselLoadRejectedException;
import com.navislite.gateway.repository.GateTransactionRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class GateService {

    private final GateTransactionRepository repository;
    private final DeckingClient deckingClient;
    private final EquipmentDispatchService equipmentDispatchService;
    private final VesselClient vesselClient;

    public GateService(GateTransactionRepository repository, DeckingClient deckingClient,
                        EquipmentDispatchService equipmentDispatchService, VesselClient vesselClient) {
        this.repository = repository;
        this.deckingClient = deckingClient;
        this.equipmentDispatchService = equipmentDispatchService;
        this.vesselClient = vesselClient;
    }

    @Transactional
    public GateTransaction checkIn(CheckInRequest request) {
        repository.findByContainerId(request.getContainerId()).ifPresent(existing -> {
            throw new DuplicateContainerException(request.getContainerId());
        });

        GateTransaction tx = new GateTransaction();
        tx.setContainerId(request.getContainerId());
        tx.setWeightKg(request.getWeightKg());
        tx.setReefer(request.getReefer());
        tx.setDestination(request.getDestination());
        tx.setVesselCutoffTime(request.getVesselCutoffTime());
        tx.setStatus(GateStatus.PENDING);

        if (request.getVesselCutoffTime() != null && request.getVesselCutoffTime().isBefore(LocalDateTime.now())) {
            tx.setHoldType(HoldType.VESSEL_CUTOFF_EXPIRED);
            tx.setHoldReason("Vessel cutoff " + request.getVesselCutoffTime() + " has already passed");
            tx.setStatus(GateStatus.HELD);
            return repository.save(tx);
        }

        tx = repository.save(tx);

        DeckingResponse decking = deckingClient.requestSlot(new DeckingRequest(
                tx.getContainerId(), tx.getWeightKg(), tx.getReefer(), tx.getDestination()
        ));

        if (decking.isPlaced()) {
            tx.setAssignedBlock(decking.getBlock());
            tx.setAssignedRow(decking.getRow());
            tx.setAssignedBay(decking.getBay());
            tx.setAssignedTier(decking.getTier());
            tx.setDwellTimeEstimate(decking.getDwellTimeEstimate());
            tx.setShuffleRiskScore(decking.getShuffleRiskScore());
            tx.setPenaltyFlag(decking.getPenaltyFlag());
            tx.setStatus(GateStatus.DECKED);
        } else {
            tx.setStatus(GateStatus.REJECTED);
        }

        tx = repository.save(tx);

        if (tx.getStatus() == GateStatus.DECKED) {
            equipmentDispatchService.createWorkInstruction(tx.getContainerId(), TaskType.YARD_PLACEMENT);
        }

        return tx;
    }

    @Transactional
    public GateTransaction checkOut(String containerId) {
        GateTransaction tx = repository.findByContainerId(containerId)
                .orElseThrow(() -> new TransactionNotFoundException(containerId));

        if (tx.getStatus() != GateStatus.DECKED) {
            throw new InvalidGateStatusException(containerId, tx.getStatus(), GateStatus.DECKED);
        }

        if (tx.getHoldType() != null) {
            throw new ActiveHoldException(containerId, tx.getHoldType(), tx.getHoldReason());
        }

        ReleaseSlotResponse release = deckingClient.releaseSlot(new ReleaseSlotRequest(containerId));

        if (!release.isReleased()) {
            List<String> blocking = release.getBlockingContainerIds() != null
                    ? release.getBlockingContainerIds()
                    : List.of();
            throw new SlotBlockedException(release.getReason(), blocking);
        }

        tx.setStatus(GateStatus.DEPARTED);
        tx.setDepartureTime(LocalDateTime.now());
        tx = repository.save(tx);

        equipmentDispatchService.createWorkInstruction(containerId, TaskType.YARD_RETRIEVAL);

        return tx;
    }

    @Transactional
    public GateTransaction applyHold(String containerId, HoldType holdType, String reason) {
        GateTransaction tx = repository.findByContainerId(containerId)
                .orElseThrow(() -> new TransactionNotFoundException(containerId));

        if (tx.getStatus() == GateStatus.DEPARTED || tx.getStatus() == GateStatus.LOADED) {
            throw new InvalidGateStatusException(containerId, tx.getStatus(), GateStatus.DECKED);
        }

        tx.setHoldType(holdType);
        tx.setHoldReason(reason);
        return repository.save(tx);
    }

    @Transactional
    public GateTransaction clearHold(String containerId) {
        GateTransaction tx = repository.findByContainerId(containerId)
                .orElseThrow(() -> new TransactionNotFoundException(containerId));

        tx.setHoldType(null);
        tx.setHoldReason(null);
        return repository.save(tx);
    }

    @Transactional
    public GateTransaction loadToVessel(String containerId, Integer bay, Integer row, Integer tier) {
        GateTransaction tx = repository.findByContainerId(containerId)
                .orElseThrow(() -> new TransactionNotFoundException(containerId));

        if (tx.getStatus() != GateStatus.DECKED) {
            throw new InvalidGateStatusException(containerId, tx.getStatus(), GateStatus.DECKED);
        }

        if (tx.getHoldType() != null) {
            throw new ActiveHoldException(containerId, tx.getHoldType(), tx.getHoldReason());
        }

        ReleaseSlotResponse release = deckingClient.releaseSlot(new ReleaseSlotRequest(containerId));

        if (!release.isReleased()) {
            List<String> blocking = release.getBlockingContainerIds() != null
                    ? release.getBlockingContainerIds()
                    : List.of();
            throw new SlotBlockedException(release.getReason(), blocking);
        }

        // NOTE: the yard slot above has already been released. If the vessel placement below
        // is rejected (e.g. someone else took the slot), we do not attempt to re-place the
        // container back in the yard — that would need a second decking call with no guarantee
        // of landing in the same spot. This is a known limitation, same category as the existing
        // yard-state-is-memory-only gap, not a distributed-transaction guarantee this MVP makes.
        VesselLoadResponse vesselLoad = vesselClient.loadContainer(
                new VesselLoadRequest(containerId, tx.getWeightKg(), bay, row, tier)
        );

        if (!vesselLoad.isLoaded()) {
            throw new VesselLoadRejectedException(vesselLoad.getReason());
        }

        tx.setStatus(GateStatus.LOADED);
        tx.setVesselBay(bay);
        tx.setVesselRow(row);
        tx.setVesselTier(tier);
        return repository.save(tx);
    }

    public List<GateTransaction> listTransactions() {
        return repository.findAllByOrderByCheckInTimeDesc();
    }
}
