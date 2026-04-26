"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prospects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("place_id", sa.String(255), nullable=False, unique=True),
        sa.Column("business_name", sa.String(255), nullable=False),
        sa.Column("trade", sa.String(50), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(2), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("address", sa.String(500)),
        sa.Column("lat", sa.DECIMAL(10, 8)),
        sa.Column("lng", sa.DECIMAL(11, 8)),
        sa.Column("google_rating", sa.DECIMAL(2, 1)),
        sa.Column("review_count", sa.Integer, server_default="0"),
        sa.Column("website_url", sa.String(500)),
        sa.Column("status", sa.String(50), server_default="identified"),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )

    op.create_table(
        "research_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("prospect_id", sa.String(36), sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("step", sa.String(50)),
        sa.Column("error_message", sa.Text),
        sa.Column("completed_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_research_jobs_prospect_id", "research_jobs", ["prospect_id"])

    op.create_table(
        "business_intelligence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("prospect_id", sa.String(36), sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("years_in_business", sa.Integer),
        sa.Column("service_area", sa.String(500)),
        sa.Column("service_specialties", sa.Text),
        sa.Column("owner_name", sa.String(255)),
        sa.Column("owner_title", sa.String(255)),
        sa.Column("gbp_profile_complete", sa.Boolean, server_default="false"),
        sa.Column("gbp_review_response_rate", sa.DECIMAL(5, 2)),
        sa.Column("site_last_updated", sa.String(100)),
        sa.Column("site_mobile_friendly", sa.Boolean),
        sa.Column("instagram_url", sa.String(500)),
        sa.Column("facebook_url", sa.String(500)),
        sa.Column("linkedin_url", sa.String(500)),
        sa.Column("youtube_url", sa.String(500)),
        sa.Column("yelp_url", sa.String(500)),
        sa.Column("business_hours", sa.Text),
        sa.Column("payment_methods", sa.Text),
        sa.Column("certifications", sa.Text),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_business_intelligence_prospect_id", "business_intelligence", ["prospect_id"])

    op.create_table(
        "competitor_intelligence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("prospect_id", sa.String(36), sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("competitor_name", sa.String(255), nullable=False),
        sa.Column("competitor_website", sa.String(500)),
        sa.Column("top_keywords", sa.Text),
        sa.Column("content_themes", sa.Text),
        sa.Column("pricing_strategy", sa.Text),
        sa.Column("estimated_monthly_volume", sa.Integer),
        sa.Column("search_ranking_position", sa.Integer),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_competitor_intelligence_prospect_id", "competitor_intelligence", ["prospect_id"])

    op.create_table(
        "clients",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("prospect_id", sa.String(36), sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stripe_customer_id", sa.String(255)),
        sa.Column("stripe_subscription_id", sa.String(255)),
        sa.Column("package", sa.String(50)),
        sa.Column("custom_domain", sa.String(255)),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_clients_prospect_id", "clients", ["prospect_id"])

    op.create_table(
        "generated_sites",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("prospect_id", sa.String(36), sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id", sa.String(36), sa.ForeignKey("clients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("template_id", sa.String(100), nullable=False),
        sa.Column("preview_url", sa.String(500)),
        sa.Column("production_url", sa.String(500)),
        sa.Column("status", sa.String(50), server_default="preview_live"),
        sa.Column("site_content", sa.JSON),
        sa.Column("site_config", sa.JSON),
        sa.Column("schema_org_json", sa.JSON),
        sa.Column("meta_title", sa.String(255)),
        sa.Column("meta_description", sa.String(500)),
        sa.Column("lighthouse_score", sa.Integer),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_generated_sites_prospect_id", "generated_sites", ["prospect_id"])
    op.create_index("ix_generated_sites_slug", "generated_sites", ["slug"])

    op.create_table(
        "outreach_sequences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("prospect_id", sa.String(36), sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("sequence_template", sa.String(100), server_default="home_services_v1"),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("current_step", sa.Integer, server_default="0"),
        sa.Column("max_steps", sa.Integer, server_default="4"),
        sa.Column("next_send_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_outreach_sequences_prospect_id", "outreach_sequences", ["prospect_id"])
    op.create_index("ix_outreach_sequences_next_send_at", "outreach_sequences", ["next_send_at"])

    op.create_table(
        "outreach_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("sequence_id", sa.String(36), sa.ForeignKey("outreach_sequences.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prospect_id", sa.String(36), sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("to_address", sa.String(255), nullable=False),
        sa.Column("from_address", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(255)),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("status", sa.String(50), server_default="queued"),
        sa.Column("provider_message_id", sa.String(255)),
        sa.Column("sent_at", sa.DateTime),
        sa.Column("delivered_at", sa.DateTime),
        sa.Column("opened_at", sa.DateTime),
        sa.Column("clicked_at", sa.DateTime),
        sa.Column("replied_at", sa.DateTime),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_outreach_messages_prospect_id", "outreach_messages", ["prospect_id"])
    op.create_index("ix_outreach_messages_sequence_id", "outreach_messages", ["sequence_id"])

    op.create_table(
        "lead_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("prospect_id", sa.String(36), sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("from_address", sa.String(255)),
        sa.Column("message_body", sa.Text),
        sa.Column("is_hot_lead", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime),
    )
    op.create_index("ix_lead_events_prospect_id", "lead_events", ["prospect_id"])


def downgrade():
    op.drop_table("lead_events")
    op.drop_table("outreach_messages")
    op.drop_table("outreach_sequences")
    op.drop_table("generated_sites")
    op.drop_table("clients")
    op.drop_table("competitor_intelligence")
    op.drop_table("business_intelligence")
    op.drop_table("research_jobs")
    op.drop_table("prospects")
