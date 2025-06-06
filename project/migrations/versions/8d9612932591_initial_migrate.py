"""initial migrate

Revision ID: 8d9612932591
Revises: 43af2e35dae6
Create Date: 2025-05-03 23:21:03.232186

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d9612932591'
down_revision = '43af2e35dae6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('profile_picture', sa.String(length=120), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('profile_picture')

    # ### end Alembic commands ###
