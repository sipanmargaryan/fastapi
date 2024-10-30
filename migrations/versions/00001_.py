"""empty message

Revision ID: 00001
Revises: 
Create Date: 2023-12-21 13:31:30.041581

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "00001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    sa.Enum(
        "pending", "active", "deleted", "expired", name="verificationstatustypes"
    ).create(op.get_bind())
    sa.Enum("member", "owner", name="usertypes").create(op.get_bind())
    sa.Enum("consultant", "superuser", name="admintypes").create(op.get_bind())
    op.create_table(
        "countries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("dial_code", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=True),
        sa.Column("domain", sa.String(), nullable=True),
        sa.Column("company_size", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("password", sa.String(), nullable=True),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("business_phone_number", sa.String(), nullable=True),
        sa.Column("reset_pass_code", sa.String(), nullable=True),
        sa.Column("auth_code", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.Column("reset_pass_code_expiration_date", sa.DateTime(), nullable=True),
        sa.Column(
            "admin_type",
            postgresql.ENUM(
                "consultant", "superuser", name="admintypes", create_type=False
            ),
            nullable=True,
        ),
        sa.Column("country_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["country_id"],
            ["countries.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("auth_code"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("reset_pass_code"),
    )
    op.create_index(op.f("ix_users_first_name"), "users", ["first_name"], unique=False)
    op.create_index(op.f("ix_users_last_name"), "users", ["last_name"], unique=False)
    op.create_table(
        "dashboards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("deleted", sa.Boolean(), nullable=True),
        sa.Column("consultant_id", sa.Integer(), nullable=True),
        sa.Column("dashboard_unique_identifier", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["consultant_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dashboard_unique_identifier"),
    )
    op.create_table(
        "user_organization",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "user_type",
            postgresql.ENUM("member", "owner", name="usertypes", create_type=False),
            nullable=True,
        ),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("invitation_date", sa.DateTime(), nullable=True),
        sa.Column(
            "verification_status",
            postgresql.ENUM(
                "pending",
                "active",
                "deleted",
                "expired",
                name="verificationstatustypes",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("verification_code", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("verification_code"),
    )
    op.create_table(
        "chart",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("dashboard_id", sa.Integer(), nullable=True),
        sa.Column("consultant_id", sa.Integer(), nullable=True),
        sa.Column("dashboard_chart_unique_identifier", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["consultant_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["dashboard_id"],
            ["dashboards.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_dashboard",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("dashboard_id", sa.Integer(), nullable=True),
        sa.Column("last_viewed", sa.DateTime(), nullable=True),
        sa.Column("pinned", sa.Boolean(), nullable=True),
        sa.Column("pinned_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["dashboard_id"],
            ["dashboards.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("user_dashboard")
    op.drop_table("chart")
    op.drop_table("user_organization")
    op.drop_table("dashboards")
    op.drop_table("users")
    op.drop_table("organizations")
    op.drop_table("countries")
    sa.Enum("consultant", "superuser", name="admintypes").drop(op.get_bind())
    sa.Enum("member", "owner", name="usertypes").drop(op.get_bind())
    sa.Enum(
        "pending", "active", "deleted", "expired", name="verificationstatustypes"
    ).drop(op.get_bind())
    # ### end Alembic commands ###
