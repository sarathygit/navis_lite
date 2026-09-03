from app.services.training_data import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    generate_synthetic_training_data,
    wrangle,
)


def record(
    container_id="ABCD1234567",
    weight=15000.0,
    reefer=False,
    tier=3,
    status="DEPARTED",
    check_in="2026-01-01T00:00:00",
    departure="2026-01-04T00:00:00",
):
    return {
        "containerId": container_id,
        "weightKg": weight,
        "reefer": reefer,
        "assignedTier": tier,
        "status": status,
        "checkInTime": check_in,
        "departureTime": departure,
    }


def test_wrangle_empty_history_returns_empty_frame():
    frame, report = wrangle([])
    assert frame.empty
    assert report["raw_records"] == 0
    assert report["usable_rows"] == 0


def test_wrangle_computes_dwell_days_from_timestamps():
    frame, report = wrangle([record(check_in="2026-01-01T00:00:00", departure="2026-01-04T12:00:00")])
    assert report["usable_rows"] == 1
    assert frame[TARGET_COLUMN].iloc[0] == 3.5


def test_wrangle_drops_containers_that_never_received_a_slot():
    # REJECTED containers have no tier, so there is no placement to learn from
    frame, report = wrangle([record(tier=None, status="REJECTED", departure=None)])
    assert report["dropped_no_slot"] == 1
    assert frame.empty


def test_wrangle_excludes_right_censored_containers_still_in_yard():
    rows = [
        record(container_id="AAAA1111111", departure="2026-01-03T00:00:00"),
        record(container_id="BBBB2222222", status="DECKED", departure=None),
        record(container_id="CCCC3333333", status="DECKED", departure=None),
    ]
    frame, report = wrangle(rows)

    assert report["censored_still_in_yard"] == 2
    assert report["usable_rows"] == 1
    assert report["censoring_rate"] == round(2 / 3, 3)
    # the censored containers must not appear in the training target
    assert len(frame) == 1


def test_wrangle_reports_censoring_rate_so_survivorship_bias_is_visible():
    rows = [record(container_id=f"AAAA{i:07d}", status="DECKED", departure=None) for i in range(9)]
    rows.append(record(container_id="ZZZZ9999999"))
    _, report = wrangle(rows)
    # 90% of placed containers are still in the yard - a heavily biased sample
    assert report["censoring_rate"] == 0.9


def test_wrangle_drops_non_positive_dwell_from_clock_skew():
    frame, report = wrangle(
        [record(check_in="2026-01-05T00:00:00", departure="2026-01-01T00:00:00")]
    )
    assert report["dropped_implausible_dwell"] == 1
    assert frame.empty


def test_wrangle_drops_implausibly_long_dwell():
    frame, report = wrangle(
        [record(check_in="2020-01-01T00:00:00", departure="2026-01-01T00:00:00")]
    )
    assert report["dropped_implausible_dwell"] == 1
    assert frame.empty


def test_wrangle_drops_unparseable_timestamps():
    frame, report = wrangle([record(check_in="not-a-date")])
    assert report["dropped_bad_timestamps"] == 1
    assert frame.empty


def test_wrangle_engineers_is_heavy_from_the_weight_threshold():
    frame, _ = wrangle(
        [
            record(container_id="AAAA1111111", weight=25000.0),
            record(container_id="BBBB2222222", weight=5000.0),
        ]
    )
    assert sorted(frame["is_heavy"].tolist()) == [0, 1]


def test_wrangle_output_has_exactly_the_modelling_columns():
    frame, _ = wrangle([record()])
    assert list(frame.columns) == FEATURE_COLUMNS + [TARGET_COLUMN]


def test_wrangle_handles_a_realistic_mixed_batch():
    rows = [
        record(container_id="AAAA1111111", weight=26000.0, tier=1),                      # usable
        record(container_id="BBBB2222222", weight=4000.0, tier=4),                       # usable
        record(container_id="CCCC3333333", status="DECKED", departure=None),             # censored
        record(container_id="DDDD4444444", tier=None, status="REJECTED", departure=None),  # no slot
        record(container_id="EEEE5555555", check_in="garbage"),                          # bad timestamp
    ]
    frame, report = wrangle(rows)

    assert report["raw_records"] == 5
    assert report["dropped_no_slot"] == 1
    assert report["censored_still_in_yard"] == 1
    assert report["dropped_bad_timestamps"] == 1
    assert report["usable_rows"] == 2
    assert len(frame) == 2


def test_synthetic_corpus_is_wellformed_and_reproducible():
    a = generate_synthetic_training_data(n_samples=200, seed=7)
    b = generate_synthetic_training_data(n_samples=200, seed=7)

    assert list(a.columns) == FEATURE_COLUMNS + [TARGET_COLUMN]
    assert len(a) == 200
    assert (a[TARGET_COLUMN] > 0).all()
    assert a.equals(b)
