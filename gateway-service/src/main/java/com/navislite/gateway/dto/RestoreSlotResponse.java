package com.navislite.gateway.dto;

public class RestoreSlotResponse {

    private boolean restored;
    private String reason;

    public boolean isRestored() { return restored; }
    public void setRestored(boolean restored) { this.restored = restored; }
    public String getReason() { return reason; }
    public void setReason(String reason) { this.reason = reason; }
}
