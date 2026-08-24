package com.navislite.gateway.validation;

import jakarta.validation.Constraint;
import jakarta.validation.Payload;

import java.lang.annotation.*;

/**
 * Enforces ISO 6346 container ID format: 4 uppercase letters followed by 7 digits
 * (e.g. ABCD1234567). Does not verify the ISO 6346 check-digit, only the shape.
 */
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = IsoContainerIdValidator.class)
@Documented
public @interface IsoContainerId {

    String message() default "containerId must match ISO 6346 format: 4 uppercase letters followed by 7 digits (e.g. ABCD1234567)";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}
