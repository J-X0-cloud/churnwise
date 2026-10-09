"""Failed-payment recovery: decline classification, the smart-retry schedule and full dunning plans.

The retry schedule depends on why a charge failed. Hard declines (the card itself has to change) skip
retries and go straight to a card-update request; "insufficient funds" is retried just after common
paydays; everything else backs off over a week. Around the retries, a dunning plan schedules reminder
emails, an in-app banner, an escalation for high-value accounts, the access pause and the final
write-off at the end of the recovery window.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Literal

MAX_ATTEMPTS = 4

#: Declines where retrying the same card cannot succeed.
HARD_DECLINES: frozenset[str] = frozenset(
    {"expired_card", "lost_card", "stolen_card", "incorrect_number", "authentication_required"}
)
#: Days to wait before each retry, by attempt number (1-based).
SOFT_SCHEDULE: tuple[int, ...] = (1, 3, 5, 7)
#: Insufficient funds recover best just after common paydays.
PAYDAYS: tuple[int, ...] = (1, 15)
#: Hour of day (UTC) payday retries run at.
PAYDAY_RETRY_HOUR = 14

_DECLINE_LABELS: dict[str, str] = {
    "insufficient_funds": "Insufficient funds",
    "expired_card": "Expired card",
    "generic_decline": "Generic decline",
    "do_not_honor": "Do not honor",
    "lost_card": "Card reported lost",
    "stolen_card": "Card reported stolen",
    "authentication_required": "Authentication required",
    "processing_error": "Processing error",
    "incorrect_number": "Incorrect card number",
    "card_velocity_exceeded": "Card limit exceeded",
    "try_again_later": "Try again later",
}


class DeclineCategory(StrEnum):
    #: The card must be replaced.
    HARD = "hard"
    #: The bank wants the cardholder to authenticate (3-D Secure).
    AUTHENTICATION = "authentication"
    #: Not enough money right now; time retries to paydays.
    FUNDS = "funds"
    #: Temporary or unexplained; back off and retry.
    SOFT = "soft"


def decline_category(code: str) -> DeclineCategory:
    if code == "authentication_required":
        return DeclineCategory.AUTHENTICATION
    if code in HARD_DECLINES:
        return DeclineCategory.HARD
    if code in {"insufficient_funds", "card_velocity_exceeded"}:
        return DeclineCategory.FUNDS
    return DeclineCategory.SOFT


def decline_label(code: str) -> str:
    """Human label for a processor decline code; unknown codes are prettified."""
    return _DECLINE_LABELS.get(code, code.replace("_", " ").strip().capitalize() or "Unknown")


# ------------------------------------------------------------------ retry policy


@dataclass(frozen=True, slots=True)
class RetryDecision:
    action: Literal["retry", "request_card_update", "give_up"]
    at: datetime | None = None


def _as_utc(moment: datetime) -> datetime:
    return moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment.astimezone(UTC)


def next_payday(after: datetime) -> datetime:
    """The next 1st or 15th strictly after ``after`` (UTC), at the payday retry hour."""
    day = _as_utc(after)
    for _ in range(31):
        day += timedelta(days=1)
        if day.day in PAYDAYS:
            break
    return day.replace(hour=PAYDAY_RETRY_HOUR, minute=0, second=0, microsecond=0)


def next_retry(
    decline_code: str, attempt: int, failed_at: datetime, max_attempts: int = MAX_ATTEMPTS
) -> RetryDecision:
    """When to try a failed charge again, given the decline code and which attempt just failed (1-based)."""
    if attempt < 1:
        raise ValueError("attempt numbers start at 1")
    if decline_code in HARD_DECLINES:
        return RetryDecision("request_card_update")
    if attempt >= max_attempts:
        return RetryDecision("give_up")
    if decline_code == "insufficient_funds":
        return RetryDecision("retry", next_payday(failed_at))
    wait = SOFT_SCHEDULE[min(attempt, len(SOFT_SCHEDULE)) - 1]
    return RetryDecision("retry", _as_utc(failed_at) + timedelta(days=wait))


# ------------------------------------------------------------------ dunning plans


class StepKind(StrEnum):
    RETRY = "retry"
    CARD_UPDATE_REQUEST = "card_update_request"
    AUTHENTICATION_REQUEST = "authentication_request"
    EMAIL = "email"
    IN_APP_BANNER = "in_app_banner"
    CS_ESCALATION = "cs_escalation"
    PAUSE_ACCESS = "pause_access"
    WRITE_OFF = "write_off"


@dataclass(frozen=True, slots=True)
class Reminder:
    day: int
    template: str
    subject: str


DEFAULT_REMINDERS: tuple[Reminder, ...] = (
    Reminder(1, "payment_failed", "Quick heads-up about your payment"),
    Reminder(3, "update_card", "Update your card in 10 seconds"),
    Reminder(7, "needs_attention", "Your account needs attention"),
    Reminder(14, "final_notice", "Final notice before your plan pauses"),
)


@dataclass(frozen=True, slots=True)
class DunningPolicy:
    max_attempts: int = MAX_ATTEMPTS
    reminders: tuple[Reminder, ...] = DEFAULT_REMINDERS
    banner_day: int | None = 6
    #: Days after the first failure at which access is paused (None keeps access on).
    pause_after_days: int | None = 21
    #: A payment still failing after this many days is lost to involuntary churn.
    recovery_window_days: int = 30
    #: Invoices at or above this amount copy the account's CS owner on the final notice.
    high_value_threshold: float = 1000.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.recovery_window_days < 1:
            raise ValueError("the recovery window must be at least one day")
        days = [r.day for r in self.reminders]
        if days != sorted(days) or len(set(days)) != len(days):
            raise ValueError("reminders must be on distinct, increasing days")
        for day in (*days, self.banner_day, self.pause_after_days):
            if day is not None and not 0 < day < self.recovery_window_days:
                raise ValueError("every step must fall inside the recovery window")


DEFAULT_POLICY = DunningPolicy()


@dataclass(frozen=True, slots=True)
class DunningStep:
    at: datetime
    kind: StepKind
    description: str
    attempt: int | None = None
    template: str | None = None


@dataclass(frozen=True, slots=True)
class DunningPlan:
    decline_code: str
    category: DeclineCategory
    amount: float
    first_failed_at: datetime
    closes_at: datetime
    steps: tuple[DunningStep, ...] = field(default_factory=tuple)

    @property
    def retries(self) -> int:
        return sum(1 for s in self.steps if s.kind is StepKind.RETRY)

    def due(self, now: datetime) -> list[DunningStep]:
        """Steps whose time has come."""
        now = _as_utc(now)
        return [s for s in self.steps if s.at <= now]

    def upcoming(self, now: datetime) -> list[DunningStep]:
        now = _as_utc(now)
        return [s for s in self.steps if s.at > now]

    def next_step(self, now: datetime) -> DunningStep | None:
        upcoming = self.upcoming(now)
        return upcoming[0] if upcoming else None


_STEP_ORDER = {kind: i for i, kind in enumerate(StepKind)}


def plan_dunning(
    first_failed_at: datetime,
    decline_code: str,
    amount: float,
    policy: DunningPolicy = DEFAULT_POLICY,
) -> DunningPlan:
    """Every recovery step for a payment that keeps failing, from its first failure to the write-off.

    The plan assumes each retry fails; in practice the sequence stops the moment a payment succeeds.
    """
    if amount <= 0:
        raise ValueError("the failed amount must be positive")
    start = _as_utc(first_failed_at)
    closes_at = start + timedelta(days=policy.recovery_window_days)
    category = decline_category(decline_code)
    steps: list[DunningStep] = []

    if category is DeclineCategory.AUTHENTICATION:
        steps.append(
            DunningStep(start, StepKind.AUTHENTICATION_REQUEST, "Send a 3-D Secure authentication link")
        )
    elif category is DeclineCategory.HARD:
        steps.append(DunningStep(start, StepKind.CARD_UPDATE_REQUEST, "Send a one-click card-update link"))
    else:
        attempt, failed_at = 1, start
        while True:
            decision = next_retry(decline_code, attempt, failed_at, policy.max_attempts)
            if decision.action != "retry" or decision.at is None or decision.at >= closes_at:
                break
            attempt += 1
            failed_at = decision.at
            reason = "after payday" if category is DeclineCategory.FUNDS else "after back-off"
            steps.append(
                DunningStep(failed_at, StepKind.RETRY, f"Retry #{attempt - 1} {reason}", attempt=attempt)
            )

    for reminder in policy.reminders:
        steps.append(
            DunningStep(
                start + timedelta(days=reminder.day),
                StepKind.EMAIL,
                reminder.subject,
                template=reminder.template,
            )
        )
    if policy.banner_day is not None:
        steps.append(
            DunningStep(
                start + timedelta(days=policy.banner_day),
                StepKind.IN_APP_BANNER,
                "Show the payment banner to account admins",
            )
        )
    if amount >= policy.high_value_threshold and policy.reminders:
        steps.append(
            DunningStep(
                start + timedelta(days=policy.reminders[-1].day),
                StepKind.CS_ESCALATION,
                "Copy the account's CS owner on the final notice",
            )
        )
    if policy.pause_after_days is not None:
        steps.append(
            DunningStep(
                start + timedelta(days=policy.pause_after_days),
                StepKind.PAUSE_ACCESS,
                "Pause access until the payment goes through",
            )
        )
    steps.append(DunningStep(closes_at, StepKind.WRITE_OFF, "Count the invoice as lost to involuntary churn"))
    steps.sort(key=lambda s: (s.at, _STEP_ORDER[s.kind]))

    return DunningPlan(
        decline_code=decline_code,
        category=category,
        amount=amount,
        first_failed_at=start,
        closes_at=closes_at,
        steps=tuple(steps),
    )
