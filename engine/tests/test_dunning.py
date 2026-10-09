from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from churnwise.domain.dunning import (
    DEFAULT_POLICY,
    DeclineCategory,
    DunningPolicy,
    Reminder,
    StepKind,
    decline_category,
    decline_label,
    next_payday,
    next_retry,
    plan_dunning,
)

T0 = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)


def _iso(dt: datetime | None) -> str | None:
    return None if dt is None else dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def test_retry_policy_matches_typescript(golden):
    cases = [
        ("insufficient_funds", 1, datetime(2026, 9, 24, 12, tzinfo=UTC)),
        ("generic_decline", 2, datetime(2026, 1, 30, 23, tzinfo=UTC)),
        ("insufficient_funds", 2, datetime(2026, 9, 15, 1, tzinfo=UTC)),
        ("insufficient_funds", 1, datetime(2026, 1, 31, 12, tzinfo=UTC)),
    ]
    for (code, attempt, failed_at), want in zip(cases, golden["retry"], strict=True):
        decision = next_retry(code, attempt, failed_at)
        assert decision.action == want["action"]
        assert _iso(decision.at) == want["at"]


@pytest.mark.parametrize(
    "code", ["expired_card", "lost_card", "stolen_card", "incorrect_number", "authentication_required"]
)
def test_hard_declines_skip_retries(code):
    assert next_retry(code, 1, T0).action == "request_card_update"


def test_soft_declines_back_off_then_give_up():
    assert next_retry("do_not_honor", 1, T0).at == T0 + timedelta(days=1)
    assert next_retry("do_not_honor", 2, T0).at == T0 + timedelta(days=3)
    assert next_retry("do_not_honor", 3, T0).at == T0 + timedelta(days=5)
    assert next_retry("do_not_honor", 4, T0).action == "give_up"
    assert next_retry("insufficient_funds", 4, T0).action == "give_up"


def test_payday_handles_month_ends_and_naive_times():
    assert next_payday(datetime(2026, 1, 31, 23, 59)) == datetime(2026, 2, 1, 14, tzinfo=UTC)
    assert next_payday(datetime(2026, 2, 1, 9, tzinfo=UTC)) == datetime(2026, 2, 15, 14, tzinfo=UTC)
    assert next_payday(datetime(2026, 12, 20, tzinfo=UTC)) == datetime(2027, 1, 1, 14, tzinfo=UTC)


def test_retry_attempt_numbers_start_at_one():
    with pytest.raises(ValueError):
        next_retry("generic_decline", 0, T0)


@pytest.mark.parametrize(
    ("code", "category", "label"),
    [
        ("insufficient_funds", DeclineCategory.FUNDS, "Insufficient funds"),
        ("expired_card", DeclineCategory.HARD, "Expired card"),
        ("authentication_required", DeclineCategory.AUTHENTICATION, "Authentication required"),
        ("do_not_honor", DeclineCategory.SOFT, "Do not honor"),
        ("lost_card", DeclineCategory.HARD, "Card reported lost"),
        ("weird_new_code", DeclineCategory.SOFT, "Weird new code"),
    ],
)
def test_decline_classification(code, category, label):
    assert decline_category(code) is category
    assert decline_label(code) == label


def test_plan_for_a_soft_decline_retries_and_runs_the_full_sequence():
    plan = plan_dunning(T0, "generic_decline", 349)
    kinds = [s.kind for s in plan.steps]
    assert plan.retries == 3
    retries = [s for s in plan.steps if s.kind is StepKind.RETRY]
    assert [s.at - T0 for s in retries] == [timedelta(days=d) for d in (1, 4, 9)]
    assert [s.attempt for s in retries] == [2, 3, 4]
    assert kinds.count(StepKind.EMAIL) == 4
    assert StepKind.IN_APP_BANNER in kinds
    assert StepKind.CS_ESCALATION not in kinds  # below the high-value threshold
    assert plan.steps[-1].kind is StepKind.WRITE_OFF
    assert plan.closes_at == T0 + timedelta(days=30)
    assert [s.at for s in plan.steps] == sorted(s.at for s in plan.steps)


def test_plan_for_insufficient_funds_waits_for_paydays():
    plan = plan_dunning(T0, "insufficient_funds", 2380)
    retries = [s.at for s in plan.steps if s.kind is StepKind.RETRY]
    assert retries == [datetime(2026, 10, 1, 14, tzinfo=UTC), datetime(2026, 10, 15, 14, tzinfo=UTC)]
    # High-value invoices copy the CS owner on the final notice.
    escalation = next(s for s in plan.steps if s.kind is StepKind.CS_ESCALATION)
    final = next(s for s in plan.steps if s.template == "final_notice")
    assert escalation.at == final.at


@pytest.mark.parametrize(
    ("code", "first_kind"),
    [
        ("expired_card", StepKind.CARD_UPDATE_REQUEST),
        ("authentication_required", StepKind.AUTHENTICATION_REQUEST),
    ],
)
def test_plan_for_hard_declines_asks_the_customer_first(code, first_kind):
    plan = plan_dunning(T0, code, 698)
    assert plan.steps[0].kind is first_kind
    assert plan.steps[0].at == T0
    assert plan.retries == 0


def test_due_upcoming_and_next_step():
    plan = plan_dunning(T0, "generic_decline", 99)
    now = T0 + timedelta(days=3, hours=1)
    due = plan.due(now)
    assert {s.kind for s in due} == {StepKind.RETRY, StepKind.EMAIL}
    assert len(due) + len(plan.upcoming(now)) == len(plan.steps)
    assert plan.next_step(now) == plan.upcoming(now)[0]
    assert plan.next_step(T0 + timedelta(days=60)) is None


def test_custom_policy_without_pause_or_banner():
    policy = DunningPolicy(
        reminders=(Reminder(2, "first", "First"),),
        banner_day=None,
        pause_after_days=None,
        recovery_window_days=8,
    )
    plan = plan_dunning(T0, "do_not_honor", 50, policy)
    kinds = {s.kind for s in plan.steps}
    assert StepKind.PAUSE_ACCESS not in kinds and StepKind.IN_APP_BANNER not in kinds
    assert all(s.at <= plan.closes_at for s in plan.steps)
    # Back-off retries land on days 1, 4 and 9; the last falls outside an eight-day window.
    assert plan.retries == 2


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_attempts": 0},
        {"recovery_window_days": 0},
        {"reminders": (Reminder(3, "a", "A"), Reminder(1, "b", "B"))},
        {"banner_day": 45},
    ],
)
def test_policy_validation(kwargs):
    with pytest.raises(ValueError):
        DunningPolicy(**kwargs)


def test_plan_rejects_non_positive_amounts():
    with pytest.raises(ValueError):
        plan_dunning(T0, "generic_decline", 0)
    assert DEFAULT_POLICY.max_attempts == 4
