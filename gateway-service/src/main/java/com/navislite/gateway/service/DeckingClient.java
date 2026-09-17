package com.navislite.gateway.service;

import com.navislite.gateway.dto.DeckingRequest;
import com.navislite.gateway.dto.DeckingResponse;
import com.navislite.gateway.dto.ReleaseSlotRequest;
import com.navislite.gateway.dto.ReleaseSlotResponse;
import com.navislite.gateway.dto.RestoreSlotRequest;
import com.navislite.gateway.dto.RestoreSlotResponse;
import com.navislite.gateway.exception.DeckingEngineException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

@Component
public class DeckingClient {

    private final RestTemplate restTemplate;
    private final String baseUrl;
    private final String predictPath;
    private final String releasePath;
    private final String restorePath;

    public DeckingClient(RestTemplate restTemplate,
                          @Value("${navislite.decking-engine.base-url}") String baseUrl,
                          @Value("${navislite.decking-engine.predict-path}") String predictPath,
                          @Value("${navislite.decking-engine.release-path}") String releasePath,
                          @Value("${navislite.decking-engine.restore-path}") String restorePath) {
        this.restTemplate = restTemplate;
        this.baseUrl = baseUrl;
        this.predictPath = predictPath;
        this.releasePath = releasePath;
        this.restorePath = restorePath;
    }

    public DeckingResponse requestSlot(DeckingRequest request) {
        try {
            DeckingResponse response = restTemplate.postForObject(baseUrl + predictPath, request, DeckingResponse.class);
            if (response == null) {
                throw new DeckingEngineException("Decking engine returned an empty response");
            }
            return response;
        } catch (RestClientException ex) {
            throw new DeckingEngineException("Failed to reach decking engine at " + baseUrl + predictPath, ex);
        }
    }

    public ReleaseSlotResponse releaseSlot(ReleaseSlotRequest request) {
        try {
            ReleaseSlotResponse response = restTemplate.postForObject(baseUrl + releasePath, request, ReleaseSlotResponse.class);
            if (response == null) {
                throw new DeckingEngineException("Decking engine returned an empty response");
            }
            return response;
        } catch (RestClientException ex) {
            throw new DeckingEngineException("Failed to reach decking engine at " + baseUrl + releasePath, ex);
        }
    }

    /**
     * Puts a container back where it was after a vessel load was refused.
     * Never throws: this runs while the caller is already handling a failure,
     * and a compensation that throws would mask the original cause.
     */
    public RestoreSlotResponse restoreSlot(RestoreSlotRequest request) {
        try {
            RestoreSlotResponse response =
                    restTemplate.postForObject(baseUrl + restorePath, request, RestoreSlotResponse.class);
            if (response != null) {
                return response;
            }
        } catch (RestClientException ex) {
            // fall through to the failed response below
        }
        RestoreSlotResponse failed = new RestoreSlotResponse();
        failed.setRestored(false);
        failed.setReason("Decking engine unreachable at " + baseUrl + restorePath);
        return failed;
    }
}
