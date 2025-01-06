"""initial migration

Revision ID: 67a057746962
Revises: 
Create Date: 2025-01-07 01:12:47.736463

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "67a057746962"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Drop the existing foreign key constraint
    op.drop_constraint("transactions_membership_id_fkey", "transactions", type_="foreignkey")

    # Alter the column types
    op.alter_column("memberships", "id", existing_type=sa.UUID(), type_=sa.String(length=9), existing_nullable=False)
    op.alter_column("transactions", "membership_id", existing_type=sa.UUID(), type_=sa.String(length=9), existing_nullable=True)

    # Recreate the foreign key constraint with the new type
    op.create_foreign_key("transactions_membership_id_fkey", "transactions", "memberships", ["membership_id"], ["id"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Drop the existing foreign key constraint
    op.drop_constraint("transactions_membership_id_fkey", "transactions", type_="foreignkey")

    # Revert the column types
    op.alter_column("transactions", "membership_id", existing_type=sa.String(length=9), type_=sa.UUID(), existing_nullable=True)
    op.alter_column("memberships", "id", existing_type=sa.String(length=9), type_=sa.UUID(), existing_nullable=False)

    # Recreate the foreign key constraint with the original type
    op.create_foreign_key("transactions_membership_id_fkey", "transactions", "memberships", ["membership_id"], ["id"])
    # ### end Alembic commands ###