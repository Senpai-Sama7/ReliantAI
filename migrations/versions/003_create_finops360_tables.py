"""
003_create_finops360_tables

Create FinOps360 cloud cost and resource tables.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # cloud_accounts table
    op.create_table(
        'cloud_accounts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('account_id', sa.Text(), nullable=False),
        sa.Column('account_name', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.UniqueConstraint('provider', 'account_id', name='uq_provider_account')
    )

    # cost_data table
    op.create_table(
        'cost_data',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('account_id', sa.Integer(), sa.ForeignKey('cloud_accounts.id'), nullable=True),
        sa.Column('service_name', sa.Text(), nullable=False),
        sa.Column('resource_id', sa.Text(), nullable=True),
        sa.Column('region', sa.Text(), nullable=True),
        sa.Column('cost_amount', sa.DECIMAL(12, 4), nullable=False),
        sa.Column('currency', sa.Text(), server_default='USD', nullable=True),
        sa.Column('usage_date', sa.Date(), nullable=False),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
    )

    # budgets table
    op.create_table(
        'budgets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('account_id', sa.Integer(), sa.ForeignKey('cloud_accounts.id'), nullable=True),
        sa.Column('monthly_limit', sa.DECIMAL(12, 2), nullable=False),
        sa.Column('current_spend', sa.DECIMAL(12, 2), server_default='0', nullable=True),
        sa.Column('alert_threshold', sa.Integer(), server_default='80', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
    )

    # cost_alerts table
    op.create_table(
        'cost_alerts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('budget_id', sa.Integer(), sa.ForeignKey('budgets.id'), nullable=True),
        sa.Column('alert_type', sa.Text(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('severity', sa.Text(), nullable=True),
        sa.Column('is_acknowledged', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
    )

    # cost_optimization_recommendations table
    op.create_table(
        'cost_optimization_recommendations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('account_id', sa.Integer(), sa.ForeignKey('cloud_accounts.id'), nullable=True),
        sa.Column('resource_id', sa.Text(), nullable=True),
        sa.Column('service_name', sa.Text(), nullable=True),
        sa.Column('recommendation_type', sa.Text(), nullable=True),
        sa.Column('potential_savings', sa.DECIMAL(12, 2), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_implemented', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
    )

    # resource_utilization table
    op.create_table(
        'resource_utilization',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('account_id', sa.Integer(), sa.ForeignKey('cloud_accounts.id'), nullable=True),
        sa.Column('resource_id', sa.Text(), nullable=False),
        sa.Column('service_name', sa.Text(), nullable=True),
        sa.Column('metric_name', sa.Text(), nullable=True),
        sa.Column('metric_value', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('recorded_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
    )


def downgrade():
    op.drop_table('resource_utilization')
    op.drop_table('cost_optimization_recommendations')
    op.drop_table('cost_alerts')
    op.drop_table('budgets')
    op.drop_table('cost_data')
    op.drop_table('cloud_accounts')