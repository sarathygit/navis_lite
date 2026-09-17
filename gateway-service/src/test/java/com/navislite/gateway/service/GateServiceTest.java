package com.navislite.gateway.service;

import com.navislite.gateway.dto.CheckInRequest;
import com.navislite.gateway.dto.DeckingResponse;
import com.navislite.gateway.dto.ReleaseSlotResponse;
import com.navislite.gateway.dto.VesselLoadResponse;
import com.navislite.gateway.entity.GateStatus;
import com.navislite.gateway.entity.GateTransaction;
import com.navislite.gateway.entity.HoldType;
import com.navislite.gateway.entity.TaskType;
import com.navislite.gateway.exception.ActiveHoldException;
import com.navislite.gateway.exception.DuplicateContainerException;
import com.navislite.gateway.exception.VesselLoadRejectedException;
import com.navislite.gateway.repository.GateTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

class GateServiceTest {

    private GateTransactionRepository repository;
    private DeckingClient deckingClient;
    private EquipmentDispatchService equipmentDispatchService;
    private VesselClient vesselClient;
    private GateService gateService;

    @BeforeEach
    void setUp() {
        repository = mock(GateTransactionRepository.class);
        deckingClient = mock(DeckingClient.class);
        equipmentDispatchService = mock(EquipmentDispatchService.class);
        vesselClient = mock(VesselClient.class);
        gateService = new GateService(repository, deckingClient, equipmentDispatchService, vesselClient);

        // save() just echoes back whatever was passed in, like a real JPA save would for an
        // already-identified or freshly-built entity in these tests.
        when(repository.save(any(GateTransaction.class))).thenAnswer(inv -> inv.getArgument(0));
    }

    @Test
    void checkInWithExpiredVesselCutoffSetsHeldAndNeverCallsDeckingEngine() {
        when(repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(eq("ABCD1234567"), any()))
                .thenReturn(Optional.empty());

        CheckInRequest request = new CheckInRequest();
        request.setContainerId("ABCD1234567");
        request.setWeightKg(15000.0);
        request.setReefer(false);
        request.setVesselCutoffTime(LocalDateTime.now().minusHours(2));

        GateTransaction result = gateService.checkIn(request).transaction();

        assertEquals(GateStatus.HELD, result.getStatus());
        assertEquals(HoldType.VESSEL_CUTOFF_EXPIRED, result.getHoldType());
        verify(deckingClient, never()).requestSlot(any());
    }

    @Test
    void checkInWithFutureVesselCutoffProceedsNormally() {
        when(repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(eq("ABCD1234567"), any()))
                .thenReturn(Optional.empty());
        when(deckingClient.requestSlot(any())).thenReturn(deckedResponse());

        CheckInRequest request = new CheckInRequest();
        request.setContainerId("ABCD1234567");
        request.setWeightKg(15000.0);
        request.setReefer(false);
        request.setVesselCutoffTime(LocalDateTime.now().plusDays(3));

        GateTransaction result = gateService.checkIn(request).transaction();

        assertEquals(GateStatus.DECKED, result.getStatus());
        assertNull(result.getHoldType());
        verify(deckingClient, times(1)).requestSlot(any());
        verify(equipmentDispatchService, times(1)).createWorkInstruction("ABCD1234567", TaskType.YARD_PLACEMENT);
    }

    @Test
    void checkInRejectedByDeckingEngineNeverDispatchesAWorkInstruction() {
        when(repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(eq("ABCD1234567"), any()))
                .thenReturn(Optional.empty());
        DeckingResponse rejected = new DeckingResponse();
        rejected.setPlaced(false);
        rejected.setReason("Yard full");
        when(deckingClient.requestSlot(any())).thenReturn(rejected);

        CheckInRequest request = new CheckInRequest();
        request.setContainerId("ABCD1234567");
        request.setWeightKg(15000.0);
        request.setReefer(false);

        GateTransaction result = gateService.checkIn(request).transaction();

        assertEquals(GateStatus.REJECTED, result.getStatus());
        verify(equipmentDispatchService, never()).createWorkInstruction(any(), any());
    }

    @Test
    void aRejectedContainerCanBePresentedAtTheGateAgain() {
        // A container turned away for lack of a structural base never entered the
        // yard. When space frees up the truck comes back, and the gate must accept it.
        when(repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(eq("ABCD1234567"), any()))
                .thenReturn(Optional.empty());
        when(deckingClient.requestSlot(any())).thenReturn(deckedResponse());

        CheckInRequest retry = new CheckInRequest();
        retry.setContainerId("ABCD1234567");
        retry.setWeightKg(6200.0);
        retry.setReefer(false);

        GateTransaction result = gateService.checkIn(retry).transaction();

        assertEquals(GateStatus.DECKED, result.getStatus());
    }

    @Test
    void aDepartedContainerCanReturnToTheTerminalLater() {
        // Containers are reusable steel boxes - the same ID legitimately comes back.
        when(repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(eq("ABCD1234567"), any()))
                .thenReturn(Optional.empty());
        when(deckingClient.requestSlot(any())).thenReturn(deckedResponse());

        CheckInRequest secondVisit = new CheckInRequest();
        secondVisit.setContainerId("ABCD1234567");
        secondVisit.setWeightKg(24000.0);
        secondVisit.setReefer(false);

        assertEquals(GateStatus.DECKED, gateService.checkIn(secondVisit).transaction().getStatus());
    }

    @Test
    void aContainerStillInTheYardIsStillRejectedAsADuplicate() {
        when(repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(eq("ABCD1234567"), any()))
                .thenReturn(Optional.of(deckedTransaction()));

        CheckInRequest request = new CheckInRequest();
        request.setContainerId("ABCD1234567");
        request.setWeightKg(24000.0);
        request.setReefer(false);

        assertThrows(DuplicateContainerException.class, () -> gateService.checkIn(request));
        verify(deckingClient, never()).requestSlot(any());
    }

    @Test
    void onlyActiveVisitsAreConsideredWhenLookingUpAContainer() {
        // The duplicate guard must query by status, never by container id alone -
        // otherwise a finished visit would block the container forever.
        when(repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(eq("ABCD1234567"), any()))
                .thenReturn(Optional.empty());
        when(deckingClient.requestSlot(any())).thenReturn(deckedResponse());

        CheckInRequest request = new CheckInRequest();
        request.setContainerId("ABCD1234567");
        request.setWeightKg(24000.0);
        request.setReefer(false);
        gateService.checkIn(request);

        verify(repository).findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(
                eq("ABCD1234567"),
                argThat(statuses -> statuses.containsAll(
                        java.util.List.of(GateStatus.PENDING, GateStatus.DECKED, GateStatus.HELD))
                        && !statuses.contains(GateStatus.DEPARTED)
                        && !statuses.contains(GateStatus.REJECTED)
                        && !statuses.contains(GateStatus.LOADED)));
    }

    @Test
    void checkOutBlockedByActiveHoldThrowsActiveHoldException() {
        GateTransaction tx = deckedTransaction();
        tx.setHoldType(HoldType.CUSTOMS_HOLD);
        tx.setHoldReason("Pending customs inspection");
        when(repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(eq("ABCD1234567"), any()))
                .thenReturn(Optional.of(tx));

        assertThrows(ActiveHoldException.class, () -> gateService.checkOut("ABCD1234567"));
        verify(deckingClient, never()).releaseSlot(any());
    }

    @Test
    void checkOutSucceedsAfterHoldIsCleared() {
        GateTransaction tx = deckedTransaction();
        when(repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(eq("ABCD1234567"), any()))
                .thenReturn(Optional.of(tx));

        ReleaseSlotResponse released = new ReleaseSlotResponse();
        released.setReleased(true);
        when(deckingClient.releaseSlot(any())).thenReturn(released);

        GateTransaction result = gateService.checkOut("ABCD1234567");

        assertEquals(GateStatus.DEPARTED, result.getStatus());
        verify(equipmentDispatchService, times(1)).createWorkInstruction("ABCD1234567", TaskType.YARD_RETRIEVAL);
    }

    @Test
    void applyHoldThenCheckOutIsBlockedThenClearHoldAllowsCheckOut() {
        GateTransaction tx = deckedTransaction();
        when(repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(eq("ABCD1234567"), any()))
                .thenReturn(Optional.of(tx));

        GateTransaction held = gateService.applyHold("ABCD1234567", HoldType.DAMAGE_HOLD, "Structural damage reported");
        assertEquals(HoldType.DAMAGE_HOLD, held.getHoldType());
        assertEquals(GateStatus.DECKED, held.getStatus(), "a hold must not move an already-decked container");

        assertThrows(ActiveHoldException.class, () -> gateService.checkOut("ABCD1234567"));

        GateTransaction cleared = gateService.clearHold("ABCD1234567");
        assertNull(cleared.getHoldType());

        ReleaseSlotResponse released = new ReleaseSlotResponse();
        released.setReleased(true);
        when(deckingClient.releaseSlot(any())).thenReturn(released);

        GateTransaction result = gateService.checkOut("ABCD1234567");
        assertEquals(GateStatus.DEPARTED, result.getStatus());
    }

    @Test
    void loadToVesselSucceedsAndSetsStatusLoadedWithCoordinates() {
        GateTransaction tx = deckedTransaction();
        when(repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(eq("ABCD1234567"), any()))
                .thenReturn(Optional.of(tx));

        ReleaseSlotResponse released = new ReleaseSlotResponse();
        released.setReleased(true);
        when(deckingClient.releaseSlot(any())).thenReturn(released);

        VesselLoadResponse vesselLoaded = new VesselLoadResponse();
        vesselLoaded.setLoaded(true);
        vesselLoaded.setBay(2);
        vesselLoaded.setRow(1);
        vesselLoaded.setTier(3);
        when(vesselClient.loadContainer(any())).thenReturn(vesselLoaded);

        GateTransaction result = gateService.loadToVessel("ABCD1234567", 2, 1, 3);

        assertEquals(GateStatus.LOADED, result.getStatus());
        assertEquals(2, result.getVesselBay());
        assertEquals(1, result.getVesselRow());
        assertEquals(3, result.getVesselTier());
    }

    @Test
    void loadToVesselBlockedByActiveHoldNeverReachesTheYardOrVessel() {
        GateTransaction tx = deckedTransaction();
        tx.setHoldType(HoldType.CUSTOMS_HOLD);
        when(repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(eq("ABCD1234567"), any()))
                .thenReturn(Optional.of(tx));

        assertThrows(ActiveHoldException.class, () -> gateService.loadToVessel("ABCD1234567", 1, 1, 1));
        verify(deckingClient, never()).releaseSlot(any());
        verify(vesselClient, never()).loadContainer(any());
    }

    @Test
    void loadToVesselRejectsWhenNotCurrentlyDecked() {
        GateTransaction tx = deckedTransaction();
        tx.setStatus(GateStatus.PENDING);
        when(repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(eq("ABCD1234567"), any()))
                .thenReturn(Optional.of(tx));

        assertThrows(com.navislite.gateway.exception.InvalidGateStatusException.class,
                () -> gateService.loadToVessel("ABCD1234567", 1, 1, 1));
    }

    @Test
    void loadToVesselThrowsWhenVesselEngineRejectsThePlacement() {
        GateTransaction tx = deckedTransaction();
        when(repository.findFirstByContainerIdAndStatusInOrderByCheckInTimeDesc(eq("ABCD1234567"), any()))
                .thenReturn(Optional.of(tx));

        ReleaseSlotResponse released = new ReleaseSlotResponse();
        released.setReleased(true);
        when(deckingClient.releaseSlot(any())).thenReturn(released);

        VesselLoadResponse rejected = new VesselLoadResponse();
        rejected.setLoaded(false);
        rejected.setReason("Vessel slot already occupied");
        when(vesselClient.loadContainer(any())).thenReturn(rejected);

        assertThrows(VesselLoadRejectedException.class, () -> gateService.loadToVessel("ABCD1234567", 1, 1, 1));
    }

    private GateTransaction deckedTransaction() {
        GateTransaction tx = new GateTransaction();
        tx.setContainerId("ABCD1234567");
        tx.setWeightKg(15000.0);
        tx.setReefer(false);
        tx.setStatus(GateStatus.DECKED);
        tx.setAssignedBlock("A");
        tx.setAssignedTier(3);
        return tx;
    }

    private DeckingResponse deckedResponse() {
        DeckingResponse response = new DeckingResponse();
        response.setPlaced(true);
        response.setBlock("A");
        response.setTier(3);
        response.setDwellTimeEstimate(4.0);
        response.setShuffleRiskScore(0.0);
        return response;
    }
}
