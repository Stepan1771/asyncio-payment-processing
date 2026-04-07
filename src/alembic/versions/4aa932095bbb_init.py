"""init

Revision ID: 4aa932095bbb
Revises: 
Create Date: 2026-04-07 12:41:04.837548

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4aa932095bbb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('outbox_events',
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('processed', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uid', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_outbox_events'))
    )
    op.create_index(op.f('ix_outbox_events_id'), 'outbox_events', ['id'], unique=False)
    op.create_index(op.f('ix_outbox_events_uid'), 'outbox_events', ['uid'], unique=True)

    op.create_table('payments',
    sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column('currency', sa.Enum('RUB', 'USD', 'EUR', name='currency_enum'), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('metadata', sa.JSON(), nullable=True),
    sa.Column('status', sa.Enum('pending', 'succeeded', 'failed', name='payment_status_enum'), server_default='pending', nullable=False),
    sa.Column('idempotency_key', sa.String(length=255), nullable=False),
    sa.Column('webhook_url', sa.String(length=2048), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uid', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_payments'))
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_idempotency_key'), 'payments', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_payments_uid'), 'payments', ['uid'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_payments_uid'), table_name='payments')
    op.drop_index(op.f('ix_payments_idempotency_key'), table_name='payments')
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')

    op.drop_index(op.f('ix_outbox_events_uid'), table_name='outbox_events')
    op.drop_index(op.f('ix_outbox_events_id'), table_name='outbox_events')
    op.drop_table('outbox_events')

    op.execute('DROP TYPE IF EXISTS payment_status_enum')
    op.execute('DROP TYPE IF EXISTS currency_enum')
