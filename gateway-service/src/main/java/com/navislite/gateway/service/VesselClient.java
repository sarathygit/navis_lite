package com.navislite.gateway.service;

import com.navislite.gateway.dto.VesselLoadRequest;
import com.navislite.gateway.dto.VesselLoadResponse;
import com.navislite.gateway.exception.DeckingEngineException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

@Component
public class VesselClient {

    private final RestTemplate restTemplate;
    private final String baseUrl;
    private final String loadPath;

    public VesselClient(RestTemplate restTemplate,
                         @Value("${navislite.decking-engine.base-url}") String baseUrl,
                         @Value("${navislite.decking-engine.vessel-load-path}") String loadPath) {
        this.restTemplate = restTemplate;
        this.baseUrl = baseUrl;
        this.loadPath = loadPath;
    }

    public VesselLoadResponse loadContainer(VesselLoadRequest request) {
        try {
            VesselLoadResponse response = restTemplate.postForObject(baseUrl + loadPath, request, VesselLoadResponse.class);
            if (response == null) {
                throw new DeckingEngineException("Decking engine returned an empty response");
            }
            return response;
        } catch (RestClientException ex) {
            throw new DeckingEngineException("Failed to reach decking engine at " + baseUrl + loadPath, ex);
        }
    }
}
