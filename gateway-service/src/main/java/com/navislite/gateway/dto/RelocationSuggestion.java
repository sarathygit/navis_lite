package com.navislite.gateway.dto;

/**
 * A housekeeping move proposed by the decking engine when an arriving container
 * has nowhere legal to go. The system proposes; a crane operator decides.
 */
public class RelocationSuggestion {

    private String moveContainerId;
    private String fromBlock;
    private Integer fromRow;
    private Integer fromBay;
    private Integer fromTier;
    private String toBlock;
    private Integer toRow;
    private Integer toBay;
    private Integer toTier;
    private String thenPlaceAtBlock;
    private Integer thenPlaceAtRow;
    private Integer thenPlaceAtBay;
    private Integer thenPlaceAtTier;
    private String reason;

    public String getMoveContainerId() { return moveContainerId; }
    public void setMoveContainerId(String v) { this.moveContainerId = v; }
    public String getFromBlock() { return fromBlock; }
    public void setFromBlock(String v) { this.fromBlock = v; }
    public Integer getFromRow() { return fromRow; }
    public void setFromRow(Integer v) { this.fromRow = v; }
    public Integer getFromBay() { return fromBay; }
    public void setFromBay(Integer v) { this.fromBay = v; }
    public Integer getFromTier() { return fromTier; }
    public void setFromTier(Integer v) { this.fromTier = v; }
    public String getToBlock() { return toBlock; }
    public void setToBlock(String v) { this.toBlock = v; }
    public Integer getToRow() { return toRow; }
    public void setToRow(Integer v) { this.toRow = v; }
    public Integer getToBay() { return toBay; }
    public void setToBay(Integer v) { this.toBay = v; }
    public Integer getToTier() { return toTier; }
    public void setToTier(Integer v) { this.toTier = v; }
    public String getThenPlaceAtBlock() { return thenPlaceAtBlock; }
    public void setThenPlaceAtBlock(String v) { this.thenPlaceAtBlock = v; }
    public Integer getThenPlaceAtRow() { return thenPlaceAtRow; }
    public void setThenPlaceAtRow(Integer v) { this.thenPlaceAtRow = v; }
    public Integer getThenPlaceAtBay() { return thenPlaceAtBay; }
    public void setThenPlaceAtBay(Integer v) { this.thenPlaceAtBay = v; }
    public Integer getThenPlaceAtTier() { return thenPlaceAtTier; }
    public void setThenPlaceAtTier(Integer v) { this.thenPlaceAtTier = v; }
    public String getReason() { return reason; }
    public void setReason(String v) { this.reason = v; }
}
