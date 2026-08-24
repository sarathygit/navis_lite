package com.navislite.gateway.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.List;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException ex) {
        List<String> details = ex.getBindingResult().getFieldErrors().stream()
                .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
                .toList();
        ErrorResponse body = new ErrorResponse(HttpStatus.BAD_REQUEST.value(), "Validation failed", details);
        return ResponseEntity.badRequest().body(body);
    }

    @ExceptionHandler(DuplicateContainerException.class)
    public ResponseEntity<ErrorResponse> handleDuplicate(DuplicateContainerException ex) {
        ErrorResponse body = new ErrorResponse(HttpStatus.CONFLICT.value(), "Duplicate container", List.of(ex.getMessage()));
        return ResponseEntity.status(HttpStatus.CONFLICT).body(body);
    }

    @ExceptionHandler(DeckingEngineException.class)
    public ResponseEntity<ErrorResponse> handleDeckingEngine(DeckingEngineException ex) {
        ErrorResponse body = new ErrorResponse(HttpStatus.BAD_GATEWAY.value(), "Decking engine unavailable", List.of(ex.getMessage()));
        return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(body);
    }

    @ExceptionHandler(TransactionNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(TransactionNotFoundException ex) {
        ErrorResponse body = new ErrorResponse(HttpStatus.NOT_FOUND.value(), "Transaction not found", List.of(ex.getMessage()));
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(body);
    }

    @ExceptionHandler(InvalidGateStatusException.class)
    public ResponseEntity<ErrorResponse> handleInvalidStatus(InvalidGateStatusException ex) {
        ErrorResponse body = new ErrorResponse(HttpStatus.CONFLICT.value(), "Invalid gate status", List.of(ex.getMessage()));
        return ResponseEntity.status(HttpStatus.CONFLICT).body(body);
    }

    @ExceptionHandler(SlotBlockedException.class)
    public ResponseEntity<ErrorResponse> handleSlotBlocked(SlotBlockedException ex) {
        List<String> details = new java.util.ArrayList<>();
        details.add(ex.getMessage());
        details.addAll(ex.getBlockingContainerIds());
        ErrorResponse body = new ErrorResponse(HttpStatus.CONFLICT.value(), "Slot blocked", details);
        return ResponseEntity.status(HttpStatus.CONFLICT).body(body);
    }

    @ExceptionHandler(ActiveHoldException.class)
    public ResponseEntity<ErrorResponse> handleActiveHold(ActiveHoldException ex) {
        ErrorResponse body = new ErrorResponse(HttpStatus.CONFLICT.value(), "Active hold", List.of(ex.getMessage()));
        return ResponseEntity.status(HttpStatus.CONFLICT).body(body);
    }

    @ExceptionHandler(VesselLoadRejectedException.class)
    public ResponseEntity<ErrorResponse> handleVesselLoadRejected(VesselLoadRejectedException ex) {
        ErrorResponse body = new ErrorResponse(HttpStatus.CONFLICT.value(), "Vessel load rejected", List.of(ex.getMessage()));
        return ResponseEntity.status(HttpStatus.CONFLICT).body(body);
    }
}
