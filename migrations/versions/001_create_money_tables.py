"""
001_create_money_tables

Create Money service HVAC dispatch and billing tables.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # dispatches table
    op.create_table(
        'dispatches',
        sa.Column('dispatch_id', sa.Text(), primary_key=True),
        sa.Column('customer_name', sa.Text(), nullable=True),
        sa.Column('customer_phone', sa.Text(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('issue_summary', sa.Text(), nullable=True),
        sa.Column('urgency', sa.Text(), nullable=True),
        sa.Column('tech_name', sa.Text(), nullable=True),
        sa.Column('eta', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), server_default='pending', nullable=True),
        sa.Column('crew_result', sa.Text(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.Text(), nullable=True),
    )
    op.create_index('idx_dispatches_status', 'dispatches', ['status'])

    # messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('direction', sa.Text(), nullable=True),  # 'inbound' | 'outbound'
        sa.Column('phone', sa.Text(), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('sms_sid', sa.Text(), nullable=True),
        sa.Column('channel', sa.Text(), server_default='sms', nullable=True),  # 'sms' | 'whatsapp'
        sa.Column('created_at', sa.Text(), nullable=True),
    )
    op.create_index('idx_messages_phone', 'messages', ['phone'])

    # customers table (multi-tenant billing)
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('stripe_customer_id', sa.Text(), unique=True, nullable=True),
        sa.Column('stripe_subscription_id', sa.Text(), unique=True, nullable=True),
        sa.Column('api_key', sa.Text(), unique=True, nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('company', sa.Text(), nullable=True),
        sa.Column('phone', sa.Text(), nullable=True),
        sa.Column('plan', sa.Text(), server_default='free', nullable=True),  # free, starter, professional, enterprise
        sa.Column('status', sa.Text(), server_default='active', nullable=True),  # active, inactive, past_due, cancelled
        sa.Column('billing_status', sa.Text(), server_default='trialing', nullable=True),  # trialing, active, past_due, cancelled
        sa.Column('trial_ends_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('subscription_starts_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('subscription_ends_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('monthly_revenue', sa.DECIMAL(10, 2), server_default='0', nullable=True),
        sa.Column('lead_source', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('outreach_status', sa.Text(), server_default='new', nullable=True),  # new, contacted, qualified, proposal, closed_won, closed_lost
        sa.Column('outreach_last_contact', sa.TIMESTAMP(), nullable=True),
        sa.Column('outreach_next_contact', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
    )
    op.create_index('idx_customers_api_key', 'customers', ['api_key'])
    op.create_index('idx_customers_stripe_id', 'customers', ['stripe_customer_id'])
    op.create_index('idx_customers_status', 'customers', ['status'])
    op.create_index('idx_customers_outreach', 'customers', ['outreach_status'])

    # customer_events table for audit/revenue tracking
    op.create_table(
        'customer_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.Text(), nullable=False),  # dispatch_created, api_called, subscription_started, payment_succeeded, etc.
        sa.Column('event_data', postgresql.JSONB(), nullable=True),
        sa.Column('revenue_impact', sa.DECIMAL(10, 2), server_default='0', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
    )
    op.create_index('idx_customer_events_customer', 'customer_events', ['customer_id'])
    op.create_index('idx_customer_events_type', 'customer_events', ['event_type'])
    op.create_index('idx_customer_events_created', 'customer_events', ['created_at'])


def downgrade():
    op.drop_index('idx_customer_events_created', table_name='customer_events')
    op.drop_index('idx_customer_events_type', table_name='customer_events')
    op.drop_index('idx_customer_events_customer', table_name='customer_events')
    op.drop_table('customer_events')

    op.drop_index('idx_customers_outreach', table_name='customers')
    op.drop_index('idx_customers_status', table_name='customers')
    op.drop_index('idx_customers_stripe_id', table_name='customers')
    op.drop_index('idx_customers_api_key', table_name='customers')
    op.drop_table('customers')

    op.drop_index('idx_messages_phone', table_name='messages')
    op.drop_table('messages')

    op.drop_index('idx_dispatches_status', table_name='dispatches')
    op.drop_table('dispatches')