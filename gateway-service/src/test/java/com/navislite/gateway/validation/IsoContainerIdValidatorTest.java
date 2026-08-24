package com.navislite.gateway.validation;

import jakarta.validation.ConstraintValidatorContext;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;

class IsoContainerIdValidatorTest {

    private IsoContainerIdValidator validator;
    private ConstraintValidatorContext context;

    @BeforeEach
    void setUp() {
        validator = new IsoContainerIdValidator();
        context = mock(ConstraintValidatorContext.class);
    }

    @ParameterizedTest
    @ValueSource(strings = {"ABCD1234567", "MSKU9070323", "TCLU0123456"})
    void acceptsValidIso6346Ids(String containerId) {
        assertTrue(validator.isValid(containerId, context));
    }

    @ParameterizedTest
    @CsvSource({
            "abcd1234567",   // lowercase letters
            "ABC1234567",    // only 3 letters
            "ABCDE1234567",  // 5 letters
            "ABCD123456",    // only 6 digits
            "ABCD12345678",  // 8 digits
            "ABCD123456X",   // trailing non-digit
            "'',",           // empty string
    })
    void rejectsMalformedIds(String containerId) {
        assertFalse(validator.isValid(containerId, context));
    }

    @Test
    void rejectsNull() {
        assertFalse(validator.isValid(null, context));
    }
}
