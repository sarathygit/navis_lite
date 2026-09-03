"""Central configuration and business-rule constants for the Expert Decking Engine."""

import os

# Weight-tier policy: heavy cargo is structurally restricted to the lowest tiers.
HEAVY_WEIGHT_THRESHOLD_KG = 20_000.0
HEAVY_ALLOWED_TIERS = (1, 2)
LIGHT_ALLOWED_TIERS = (3, 4, 5)
MAX_TIER = 5

# Yard layout: standard dry blocks + one isolated powered reefer block.
STANDARD_BLOCKS = ["A", "B", "C"]
REEFER_BLOCK = "R"
STANDARD_BLOCK_ROWS = 4
STANDARD_BLOCK_BAYS = 5
REEFER_BLOCK_ROWS = 3
REEFER_BLOCK_BAYS = 4

# Reefer telemetry simulation.
TELEMETRY_INTERVAL_SECONDS = 5
REEFER_TEMP_SETPOINT_C = -18.0
REEFER_TEMP_TOLERANCE_C = 3.0
REEFER_TEMP_CRITICAL_C = -10.0
REEFER_HUMIDITY_SETPOINT_PCT = 60.0
REEFER_HUMIDITY_TOLERANCE_PCT = 10.0
POWER_LOSS_PROBABILITY = 0.015
MAX_ALERTS_RETAINED = 200

# Shuffle Risk & Rehandle Penalty Engine: the raw day-delta from compute_shuffle_risk
# is normalized to a 0-100% score against this ceiling (a delta at or beyond this many
# days is treated as maximum rehandle risk).
MAX_REHANDLE_DELTA_DAYS = 10.0
REHANDLE_PENALTY_HIGH_THRESHOLD = 66.0
REHANDLE_PENALTY_MEDIUM_THRESHOLD = 33.0

# Vessel Stowage Planning: a single fixed docked vessel with its own Bay x Row x Tier
# grid, distinct from the yard. Tiers at or above VESSEL_UPPER_DECK_MIN_TIER are
# "upper deck" — a heavy container (reusing HEAVY_WEIGHT_THRESHOLD_KG) placed there
# triggers a stability warning.
VESSEL_BAYS = 6
VESSEL_ROWS = 4
VESSEL_TIERS = 4
VESSEL_UPPER_DECK_MIN_TIER = 3

# Dwell-time model: training data acquisition and evaluation.
# The gateway owns transaction history, so the engine fetches it over HTTP
# rather than opening its own database connection.
GATEWAY_URL = os.getenv("GATEWAY_SERVICE_URL", "http://gateway-service:8080")
GATEWAY_TIMEOUT_SECONDS = 5.0

# Below this many usable historical rows, the model falls back to the synthetic
# corpus — a terminal on day one has nothing to learn from yet.
MIN_TRAINING_ROWS = 30

# A dwell longer than this is treated as a data fault (clock skew, bad import)
# rather than a real observation.
MAX_PLAUSIBLE_DWELL_DAYS = 365.0

# Evaluation settings.
TEST_SET_FRACTION = 0.2
CROSS_VALIDATION_FOLDS = 5
MODEL_RANDOM_STATE = 7

# If observed dwell times vary by less than this, there is effectively nothing to
# predict and the error metrics collapse toward zero. Reported as a warning so a
# meaningless "beats the baseline" result is not mistaken for a good model —
# typically seen on a demo terminal where containers are checked straight back out.
DEGENERATE_TARGET_STD_DAYS = 0.01
