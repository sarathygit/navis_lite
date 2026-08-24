"""Central configuration and business-rule constants for the Expert Decking Engine."""

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
