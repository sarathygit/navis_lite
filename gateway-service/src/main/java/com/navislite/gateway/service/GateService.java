package com.navislite.gateway.service;

import com.navislite.gateway.dto.CheckInOutcome;
import com.navislite.gateway.dto.CheckInRequest;
import com.navislite.gateway.dto.RelocationSuggestion;
import com.navislite.gateway.dto.DeckingRequest;
import com.navislite.gateway.dto.DeckingResponse;
import com.navislite.gateway.dto.ReleaseSlotRequest;
import com.navislite.gateway.dto.ReleaseSlotResponse;
import com.navislite.gateway.dto.RestoreSlotRequest;
import com.navislite.gateway.dto.RestoreSlotResponse;
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
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class GateService {

    private static final Logger log = LoggerFactory.getLogger(GateService.class);

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

    /**
     * States in which a container is still physically the terminal's problem.
     * Anything else (REJECTED, DEPARTED, LOADED) is a finished visit.
     */
    private static final List<GateStatus> ACTIVE_STATUSES =
            List.of(GateStatus.PENDING, GateStatus.DECKED, GateStatus.HELD);

    private GateTransaction requireActive(String containerId) {
        return repository
                .findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(containerId, ACTIVE_STATUSES)
                .orElseThrow(() -> new TransactionNotFoundException(containerId));
    }

    @Transactional
    public CheckInOutcome checkIn(CheckInRequest request) {
        // Only an in-progress visit blocks a new one. A container that was rejected,
        // has departed, or has sailed is free to be presented at the gate again.
        repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(
                        request.getContainerId(), ACTIVE_STATUSES)
                .ifPresent(existing -> {
                    throw new DuplicateContainerException(request.getContainerId(), existing.getStatus());
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
            return CheckInOutcome.placed(repository.save(tx));
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
            return CheckInOutcome.placed(tx);
        }

        return new CheckInOutcome(tx, decking.getSuggestion());
    }

    @Transactional
    public GateTransaction checkOut(String containerId) {
        GateTransaction tx = requireActive(containerId);

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
        // requireActive already excludes finished visits, so a departed or loaded
        // container surfaces as "not currently in the terminal" rather than reaching here.
        GateTransaction tx = requireActive(containerId);

        tx.setHoldType(holdType);
        tx.setHoldReason(reason);
        return repository.save(tx);
    }

    @Transactional
    public GateTransaction clearHold(String containerId) {
        GateTransaction tx = requireActive(containerId);

        tx.setHoldType(null);
        tx.setHoldReason(null);
        return repository.save(tx);
    }

    @Transactional
    public GateTransaction loadToVessel(String containerId, Integer bay, Integer row, Integer tier) {
        GateTransaction tx = requireActive(containerId);

        if (tx.getStatus() != GateStatus.DECKED) {
            throw new InvalidGateStatusException(containerId, tx.getStatus(), GateStatus.DECKED);
        }

        if (tx.getHoldType() != null) {
            throw new ActiveHoldException(containerId, tx.getHoldType(), tx.getHoldReason());
        }

        // Captured before the release: this is where the container goes back if the
        // vessel turns it down.
        YardSlot previousSlot = new YardSlot(tx.getAssignedBlock(), tx.getAssignedRow(),
                tx.getAssignedBay(), tx.getAssignedTier());

        ReleaseSlotResponse release = deckingClient.releaseSlot(new ReleaseSlotRequest(containerId));

        if (!release.isReleased()) {
            List<String> blocking = release.getBlockingContainerIds() != null
                    ? release.getBlockingContainerIds()
                    : List.of();
            throw new SlotBlockedException(release.getReason(), blocking);
        }

        // The yard slot is now free but the container is not yet on the vessel. If the
        // vessel refuses it, rolling back this transaction restores the ledger row but not
        // the decking engine's grid — it is a separate service with its own state. Without
        // compensation the container would exist in neither grid while the ledger still
        // called it DECKED, and the operator would see it vanish from the yard map.
        // So a refusal puts it back in the exact slot it came from before the rollback.
        VesselLoadResponse vesselLoad;
        try {
            vesselLoad = vesselClient.loadContainer(
                    new VesselLoadRequest(containerId, tx.getWeightKg(), bay, row, tier)
            );
        } catch (RuntimeException ex) {
            restoreYardSlot(tx, previousSlot);
            throw ex;
        }

        if (!vesselLoad.isLoaded()) {
            restoreYardSlot(tx, previousSlot);
            throw new VesselLoadRejectedException(vesselLoad.getReason());
        }

        tx.setStatus(GateStatus.LOADED);
        tx.setVesselBay(bay);
        tx.setVesselRow(row);
        tx.setVesselTier(tier);
        return repository.save(tx);
    }

    /** Where a container sat before it was lifted, so a refused load can undo the lift. */
    private record YardSlot(String block, Integer row, Integer bay, Integer tier) {
        boolean isComplete() {
            return block != null && row != null && bay != null && tier != null;
        }
    }

    private void restoreYardSlot(GateTransaction tx, YardSlot slot) {
        if (!slot.isComplete()) {
            log.error("Cannot restore {} to the yard: its recorded slot is incomplete ({}). "
                            + "The ledger still shows it DECKED; run POST /api/state/resync to rebuild the grid.",
                    tx.getContainerId(), slot);
            return;
        }

        RestoreSlotResponse restored = deckingClient.restoreSlot(new RestoreSlotRequest(
                tx.getContainerId(), tx.getWeightKg(), tx.getReefer(), tx.getDwellTimeEstimate(),
                slot.block(), slot.row(), slot.bay(), slot.tier()
        ));

        if (!restored.isRestored()) {
            log.error("Vessel load for {} was refused and the yard slot could not be restored: {}. "
                            + "The ledger still shows it DECKED; run POST /api/state/resync to rebuild the grid.",
                    tx.getContainerId(), restored.getReason());
        }
    }

    public List<GateTransaction> listTransactions() {
        return repository.findAllByOrderByCheckInTimeDesc();
    }
}
