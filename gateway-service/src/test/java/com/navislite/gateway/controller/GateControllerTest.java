package com.navislite.gateway.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.navislite.gateway.dto.CheckInRequest;
import com.navislite.gateway.dto.CheckOutRequest;
import com.navislite.gateway.dto.HoldRequest;
import com.navislite.gateway.dto.LoadToVesselRequest;
import com.navislite.gateway.entity.GateStatus;
import com.navislite.gateway.entity.GateTransaction;
import com.navislite.gateway.entity.HoldType;
import com.navislite.gateway.exception.ActiveHoldException;
import com.navislite.gateway.exception.InvalidGateStatusException;
import com.navislite.gateway.exception.SlotBlockedException;
import com.navislite.gateway.exception.TransactionNotFoundException;
import com.navislite.gateway.exception.VesselLoadRejectedException;
import com.navislite.gateway.service.GateService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(GateController.class)
class GateControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private GateService gateService;

    @Test
    void checkInRejectsMalformedIsoContainerId() throws Exception {
        CheckInRequest request = new CheckInRequest();
        request.setContainerId("BAD-ID");
        request.setWeightKg(15000.0);
        request.setReefer(false);

        mockMvc.perform(post("/api/gate/check-in")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void checkInRejectsNegativeWeight() throws Exception {
        CheckInRequest request = new CheckInRequest();
        request.setContainerId("ABCD1234567");
        request.setWeightKg(-5.0);
        request.setReefer(false);

        mockMvc.perform(post("/api/gate/check-in")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void checkInAcceptsValidRequestAndReturns201() throws Exception {
        CheckInRequest request = new CheckInRequest();
        request.setContainerId("ABCD1234567");
        request.setWeightKg(15000.0);
        request.setReefer(false);
        request.setDestination("Block-A");

        GateTransaction saved = new GateTransaction();
        saved.setId(1L);
        saved.setContainerId("ABCD1234567");
        saved.setWeightKg(15000.0);
        saved.setReefer(false);
        saved.setDestination("Block-A");
        saved.setStatus(GateStatus.DECKED);
        saved.setAssignedBlock("Block-A");
        saved.setAssignedTier(3);

        when(gateService.checkIn(any(CheckInRequest.class))).thenReturn(saved);

        mockMvc.perform(post("/api/gate/check-in")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.containerId").value("ABCD1234567"))
                .andExpect(jsonPath("$.status").value("DECKED"))
                .andExpect(jsonPath("$.assignedBlock").value("Block-A"));
    }

    @Test
    void healthRouteIsAvailable() throws Exception {
        mockMvc.perform(get("/api/gate/health"))
                .andExpect(status().isOk());
    }

    @Test
    void checkOutRejectsMalformedIsoContainerId() throws Exception {
        CheckOutRequest request = new CheckOutRequest();
        request.setContainerId("BAD-ID");

        mockMvc.perform(post("/api/gate/check-out")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void checkOutSucceedsAndReturnsDepartedStatus() throws Exception {
        CheckOutRequest request = new CheckOutRequest();
        request.setContainerId("ABCD1234567");

        GateTransaction departed = new GateTransaction();
        departed.setId(1L);
        departed.setContainerId("ABCD1234567");
        departed.setWeightKg(15000.0);
        departed.setReefer(false);
        departed.setStatus(GateStatus.DEPARTED);
        departed.setAssignedBlock("A");
        departed.setAssignedTier(3);

        when(gateService.checkOut(eq("ABCD1234567"))).thenReturn(departed);

        mockMvc.perform(post("/api/gate/check-out")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("DEPARTED"));
    }

    @Test
    void checkOutReturns404WhenTransactionUnknown() throws Exception {
        CheckOutRequest request = new CheckOutRequest();
        request.setContainerId("ABCD1234567");

        when(gateService.checkOut(eq("ABCD1234567")))
                .thenThrow(new TransactionNotFoundException("ABCD1234567"));

        mockMvc.perform(post("/api/gate/check-out")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isNotFound());
    }

    @Test
    void checkOutReturns409WhenNotCurrentlyDecked() throws Exception {
        CheckOutRequest request = new CheckOutRequest();
        request.setContainerId("ABCD1234567");

        when(gateService.checkOut(eq("ABCD1234567")))
                .thenThrow(new InvalidGateStatusException("ABCD1234567", GateStatus.DEPARTED, GateStatus.DECKED));

        mockMvc.perform(post("/api/gate/check-out")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isConflict());
    }

    @Test
    void checkOutReturns409WhenSlotBlockedByStackedContainers() throws Exception {
        CheckOutRequest request = new CheckOutRequest();
        request.setContainerId("ABCD1234567");

        when(gateService.checkOut(eq("ABCD1234567")))
                .thenThrow(new SlotBlockedException("buried under 1 container", List.of("WXYZ7654321")));

        mockMvc.perform(post("/api/gate/check-out")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isConflict());
    }

    @Test
    void checkOutReturns409WhenActiveHoldBlocksIt() throws Exception {
        CheckOutRequest request = new CheckOutRequest();
        request.setContainerId("ABCD1234567");

        when(gateService.checkOut(eq("ABCD1234567")))
                .thenThrow(new ActiveHoldException("ABCD1234567", HoldType.CUSTOMS_HOLD, "Pending inspection"));

        mockMvc.perform(post("/api/gate/check-out")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isConflict());
    }

    @Test
    void applyHoldReturnsUpdatedTransactionWithHoldType() throws Exception {
        HoldRequest request = new HoldRequest();
        request.setHoldType(HoldType.DAMAGE_HOLD);
        request.setReason("Visible structural damage");

        GateTransaction held = new GateTransaction();
        held.setId(1L);
        held.setContainerId("ABCD1234567");
        held.setWeightKg(15000.0);
        held.setReefer(false);
        held.setStatus(GateStatus.DECKED);
        held.setHoldType(HoldType.DAMAGE_HOLD);
        held.setHoldReason("Visible structural damage");

        when(gateService.applyHold(eq("ABCD1234567"), eq(HoldType.DAMAGE_HOLD), eq("Visible structural damage")))
                .thenReturn(held);

        mockMvc.perform(post("/api/gate/ABCD1234567/hold")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.holdType").value("DAMAGE_HOLD"));
    }

    @Test
    void clearHoldReturnsUpdatedTransactionWithoutHold() throws Exception {
        GateTransaction cleared = new GateTransaction();
        cleared.setId(1L);
        cleared.setContainerId("ABCD1234567");
        cleared.setWeightKg(15000.0);
        cleared.setReefer(false);
        cleared.setStatus(GateStatus.DECKED);

        when(gateService.clearHold(eq("ABCD1234567"))).thenReturn(cleared);

        mockMvc.perform(delete("/api/gate/ABCD1234567/hold"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.holdType").doesNotExist());
    }

    @Test
    void loadToVesselSucceedsAndReturnsLoadedStatus() throws Exception {
        LoadToVesselRequest request = new LoadToVesselRequest();
        request.setContainerId("ABCD1234567");
        request.setBay(2);
        request.setRow(1);
        request.setTier(3);

        GateTransaction loaded = new GateTransaction();
        loaded.setId(1L);
        loaded.setContainerId("ABCD1234567");
        loaded.setWeightKg(15000.0);
        loaded.setReefer(false);
        loaded.setStatus(GateStatus.LOADED);
        loaded.setVesselBay(2);
        loaded.setVesselRow(1);
        loaded.setVesselTier(3);

        when(gateService.loadToVessel(eq("ABCD1234567"), eq(2), eq(1), eq(3))).thenReturn(loaded);

        mockMvc.perform(post("/api/gate/load-to-vessel")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("LOADED"))
                .andExpect(jsonPath("$.vesselBay").value(2));
    }

    @Test
    void trainingDataExposesRawRecordsIncludingUnfinishedAndUnplacedOnes() throws Exception {
        GateTransaction completed = new GateTransaction();
        completed.setContainerId("AAAA1111111");
        completed.setWeightKg(26000.0);
        completed.setReefer(false);
        completed.setStatus(GateStatus.DEPARTED);
        completed.setAssignedTier(1);
        completed.setDepartureTime(java.time.LocalDateTime.now());

        GateTransaction stillInYard = new GateTransaction();
        stillInYard.setContainerId("BBBB2222222");
        stillInYard.setWeightKg(5000.0);
        stillInYard.setReefer(false);
        stillInYard.setStatus(GateStatus.DECKED);
        stillInYard.setAssignedTier(3);

        GateTransaction neverPlaced = new GateTransaction();
        neverPlaced.setContainerId("CCCC3333333");
        neverPlaced.setWeightKg(4000.0);
        neverPlaced.setReefer(false);
        neverPlaced.setStatus(GateStatus.REJECTED);

        when(gateService.listTransactions()).thenReturn(List.of(completed, stillInYard, neverPlaced));

        mockMvc.perform(get("/api/gate/training-data"))
                .andExpect(status().isOk())
                // all three are handed over unfiltered - cleaning is the engine's job
                .andExpect(jsonPath("$.length()").value(3))
                .andExpect(jsonPath("$[0].departureTime").isNotEmpty())
                .andExpect(jsonPath("$[1].departureTime").doesNotExist())
                .andExpect(jsonPath("$[2].assignedTier").doesNotExist());
    }

    @Test
    void loadToVesselReturns409WhenVesselEngineRejectsThePlacement() throws Exception {
        LoadToVesselRequest request = new LoadToVesselRequest();
        request.setContainerId("ABCD1234567");
        request.setBay(2);
        request.setRow(1);
        request.setTier(3);

        when(gateService.loadToVessel(eq("ABCD1234567"), eq(2), eq(1), eq(3)))
                .thenThrow(new VesselLoadRejectedException("Vessel slot already occupied"));

        mockMvc.perform(post("/api/gate/load-to-vessel")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isConflict());
    }
}
