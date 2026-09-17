package com.navislite.gateway.dto;

/**
 * Inbound payload received from the Python Expert Decking Engine
 * (POST {decking-engine}/api/predict-decking).
 */
public class DeckingResponse {

    private String block;
    private Integer row;
    private Integer bay;
    private Integer tier;
    private Double dwellTimeEstimate;
    private Double shuffleRiskScore;
    private String penaltyFlag;
    private boolean placed;
    private String reason;
    private RelocationSuggestion suggestion;

    public String getBlock() {
        return block;
    }

    public void setBlock(String block) {
        this.block = block;
    }

    public Integer getRow() {
        return row;
    }

    public void setRow(Integer row) {
        this.row = row;
    }

    public Integer getBay() {
        return bay;
    }

    public void setBay(Integer bay) {
        this.bay = bay;
    }

    public Integer getTier() {
        return tier;
    }

    public void setTier(Integer tier) {
        this.tier = tier;
    }

    public Double getDwellTimeEstimate() {
        return dwellTimeEstimate;
    }

    public void setDwellTimeEstimate(Double dwellTimeEstimate) {
        this.dwellTimeEstimate = dwellTimeEstimate;
    }

    public Double getShuffleRiskScore() {
        return shuffleRiskScore;
    }

    public void setShuffleRiskScore(Double shuffleRiskScore) {
        this.shuffleRiskScore = shuffleRiskScore;
    }

    public String getPenaltyFlag() {
        return penaltyFlag;
    }

    public void setPenaltyFlag(String penaltyFlag) {
        this.penaltyFlag = penaltyFlag;
    }

    public boolean isPlaced() {
        return placed;
    }

    public void setPlaced(boolean placed) {
        this.placed = placed;
    }

    public RelocationSuggestion getSuggestion() {
        return suggestion;
    }

    public void setSuggestion(RelocationSuggestion suggestion) {
        this.suggestion = suggestion;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }
}
