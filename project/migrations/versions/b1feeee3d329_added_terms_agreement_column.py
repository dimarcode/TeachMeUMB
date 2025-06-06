"""added terms agreement column

Revision ID: b1feeee3d329
Revises: e7115838c661
Create Date: 2025-05-09 20:36:45.971274

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1feeee3d329'
down_revision = 'e7115838c661'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('work_example', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tutor_upload_agreement', sa.Boolean(), nullable=False))
        batch_op.drop_column('upload_terms_agreement')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('work_example', schema=None) as batch_op:
        batch_op.add_column(sa.Column('upload_terms_agreement', sa.BOOLEAN(), nullable=False))
        batch_op.drop_column('tutor_upload_agreement')

    # ### end Alembic commands ###
