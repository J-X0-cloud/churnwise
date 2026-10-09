"""Event store: workspaces, raw billing events, customers, MRR movements and failed payments.

Revision ID: 0001
Revises:
Create Date: 2026-10-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

billing_source = sa.Enum(
    "stripe", "chargebee", "recurly", "braintree", "paddle", "app_store", "custom", name="billing_source"
)
movement_type = sa.Enum("new", "expansion", "reactivation", "contraction", "churn", name="movement_type")
failed_payment_status = sa.Enum("open", "recovered", "lost", name="failed_payment_status")


def _ts(name: str, nullable: bool = False, **kwargs: object) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable, **kwargs)


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        _ts("created_at", server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_workspaces"),
        sa.UniqueConstraint("slug", name="uq_workspaces_slug"),
    )
    op.create_table(
        "billing_events",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("workspace_id", sa.String(40), nullable=False),
        sa.Column("source", billing_source, nullable=False),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("type", sa.String(64), nullable=False),
        _ts("occurred_at"),
        sa.Column("payload", sa.JSON(), nullable=False),
        _ts("received_at", server_default=sa.func.now()),
        _ts("processed_at", nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_billing_events"),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_billing_events_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("workspace_id", "external_id", name="uq_billing_events_workspace_external"),
    )
    op.create_index("ix_billing_events_workspace_occurred", "billing_events", ["workspace_id", "occurred_at"])

    op.create_table(
        "customers",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("workspace_id", sa.String(40), nullable=False),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("plan", sa.String(120), nullable=True),
        sa.Column("mrr", sa.Float(), nullable=False),
        _ts("first_paid_at", nullable=True),
        _ts("churned_at", nullable=True),
        _ts("updated_at", server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_customers"),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_customers_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("workspace_id", "external_id", name="uq_customers_workspace_external"),
    )

    op.create_table(
        "mrr_movements",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("workspace_id", sa.String(40), nullable=False),
        sa.Column("customer_id", sa.String(40), nullable=False),
        sa.Column("event_id", sa.String(40), nullable=False),
        sa.Column("type", movement_type, nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("mrr_before", sa.Float(), nullable=False),
        sa.Column("mrr_after", sa.Float(), nullable=False),
        _ts("occurred_at"),
        sa.PrimaryKeyConstraint("id", name="pk_mrr_movements"),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_mrr_movements_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name="fk_mrr_movements_customer_id_customers",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["billing_events.id"],
            name="fk_mrr_movements_event_id_billing_events",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("amount >= 0", name="ck_mrr_movements_amount_positive"),
    )
    op.create_index("ix_mrr_movements_workspace_occurred", "mrr_movements", ["workspace_id", "occurred_at"])
    op.create_index("ix_mrr_movements_customer_occurred", "mrr_movements", ["customer_id", "occurred_at"])

    op.create_table(
        "failed_payments",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("workspace_id", sa.String(40), nullable=False),
        sa.Column("customer_id", sa.String(40), nullable=False),
        sa.Column("invoice_external_id", sa.String(200), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("decline_code", sa.String(80), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("status", failed_payment_status, nullable=False),
        _ts("failed_at"),
        _ts("next_retry_at", nullable=True),
        _ts("recovered_at", nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_failed_payments"),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_failed_payments_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name="fk_failed_payments_customer_id_customers",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "workspace_id", "invoice_external_id", name="uq_failed_payments_workspace_invoice"
        ),
    )
    op.create_index("ix_failed_payments_workspace_status", "failed_payments", ["workspace_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_failed_payments_workspace_status", table_name="failed_payments")
    op.drop_table("failed_payments")
    op.drop_index("ix_mrr_movements_customer_occurred", table_name="mrr_movements")
    op.drop_index("ix_mrr_movements_workspace_occurred", table_name="mrr_movements")
    op.drop_table("mrr_movements")
    op.drop_table("customers")
    op.drop_index("ix_billing_events_workspace_occurred", table_name="billing_events")
    op.drop_table("billing_events")
    op.drop_table("workspaces")
    bind = op.get_bind()
    for enum in (failed_payment_status, movement_type, billing_source):
        enum.drop(bind, checkfirst=True)
