"""
002_create_complianceone_tables

Create ComplianceOne compliance framework tables.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # compliance_frameworks table
    op.create_table(
        'compliance_frameworks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
    )

    # compliance_controls table
    op.create_table(
        'compliance_controls',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('framework_id', sa.Integer(), sa.ForeignKey('compliance_frameworks.id'), nullable=True),
        sa.Column('control_id', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.Text(), nullable=True),
        sa.Column('severity', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.UniqueConstraint('framework_id', 'control_id', name='uq_framework_control')
    )

    # compliance_audits table
    op.create_table(
        'compliance_audits',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('audit_id', sa.Text(), unique=True, nullable=False),
        sa.Column('framework_id', sa.Integer(), sa.ForeignKey('compliance_frameworks.id'), nullable=True),
        sa.Column('status', sa.Text(), server_default='in_progress', nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('findings', sa.dialects.postgresql.JSONB(), server_default='{}', nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('auditor', sa.Text(), nullable=True),
    )

    # compliance_evidence table
    op.create_table(
        'compliance_evidence',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('control_id', sa.Integer(), sa.ForeignKey('compliance_controls.id'), nullable=True),
        sa.Column('audit_id', sa.Integer(), sa.ForeignKey('compliance_audits.id'), nullable=True),
        sa.Column('evidence_type', sa.Text(), nullable=True),
        sa.Column('file_hash', sa.Text(), nullable=True),
        sa.Column('metadata', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('collected_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('collected_by', sa.Text(), nullable=True),
    )

    # compliance_violations table
    op.create_table(
        'compliance_violations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('control_id', sa.Integer(), sa.ForeignKey('compliance_controls.id'), nullable=True),
        sa.Column('severity', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('resolved_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('status', sa.Text(), server_default='open', nullable=True),
    )


def downgrade():
    op.drop_table('compliance_violations')
    op.drop_table('compliance_evidence')
    op.drop_table('compliance_audits')
    op.drop_table('compliance_controls')
    op.drop_table('compliance_frameworks')