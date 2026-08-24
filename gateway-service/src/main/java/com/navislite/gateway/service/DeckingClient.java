package com.navislite.gateway.service;

import com.navislite.gateway.dto.DeckingRequest;
import com.navislite.gateway.dto.DeckingResponse;
import com.navislite.gateway.dto.ReleaseSlotRequest;
import com.navislite.gateway.dto.ReleaseSlotResponse;
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

    public DeckingClient(RestTemplate restTemplate,
                          @Value("${navislite.decking-engine.base-url}") String baseUrl,
                          @Value("${navislite.decking-engine.predict-path}") String predictPath,
                          @Value("${navislite.decking-engine.release-path}") String releasePath) {
        this.restTemplate = restTemplate;
        this.baseUrl = baseUrl;
        this.predictPath = predictPath;
        this.releasePath = releasePath;
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
}
