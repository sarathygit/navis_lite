package com.navislite.gateway.validation;

import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;

import java.util.regex.Pattern;

public class IsoContainerIdValidator implements ConstraintValidator<IsoContainerId, String> {

    private static final Pattern ISO_6346_PATTERN = Pattern.compile("^[A-Z]{4}\\d{7}$");

    @Override
    public boolean isValid(String containerId, ConstraintValidatorContext context) {
        if (containerId == null) {
            return false;
        }
        return ISO_6346_PATTERN.matcher(containerId).matches();
    }
}
