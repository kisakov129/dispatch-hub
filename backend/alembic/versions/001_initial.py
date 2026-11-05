"""create dispatch hub tables"""
from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("loads", sa.Column("id", sa.String(length=32), primary_key=True), sa.Column("customer", sa.String(length=160), nullable=False), sa.Column("pickup", sa.String(length=160), nullable=False), sa.Column("delivery", sa.String(length=160), nullable=False), sa.Column("date", sa.Date(), nullable=False), sa.Column("status", sa.String(length=20), nullable=False), sa.Column("priority", sa.String(length=20), nullable=False), sa.Column("driver", sa.String(length=160), nullable=True))
    op.create_table("drivers", sa.Column("id", sa.String(length=32), primary_key=True), sa.Column("name", sa.String(length=160), nullable=False), sa.Column("phone", sa.String(length=40), nullable=False), sa.Column("availability", sa.String(length=20), nullable=False), sa.Column("assigned_jobs", sa.Integer(), nullable=False))
    op.create_table("users", sa.Column("id", sa.String(length=32), primary_key=True), sa.Column("name", sa.String(length=160), nullable=False), sa.Column("email", sa.String(length=160), nullable=False), sa.Column("role", sa.String(length=30), nullable=False), sa.Column("password_hash", sa.String(length=255), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("user_settings", sa.Column("id", sa.Integer(), autoincrement=True, nullable=False), sa.Column("user_id", sa.String(length=32), nullable=False), sa.Column("key", sa.String(length=80), nullable=False), sa.Column("value", sa.String(length=20), nullable=False), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_user_settings_user_id", "user_settings", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_settings_user_id", table_name="user_settings")
    op.drop_table("user_settings")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("drivers")
    op.drop_table("loads")
