"""added ability to delete appointment

Revision ID: 41ee1164e017
Revises: a866432fb942
Create Date: 2025-04-18 17:10:06.161887

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '41ee1164e017'
down_revision = 'a866432fb942'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('review', schema=None) as batch_op:
        batch_op.alter_column('appointment_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.drop_constraint('fk_review_appointment_id_appointment', type_='foreignkey')
        batch_op.create_foreign_key(batch_op.f('fk_review_appointment_id_appointment'), 'appointment', ['appointment_id'], ['id'], ondelete='SET NULL')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('review', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_review_appointment_id_appointment'), type_='foreignkey')
        batch_op.create_foreign_key('fk_review_appointment_id_appointment', 'appointment', ['appointment_id'], ['id'])
        batch_op.alter_column('appointment_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    # ### end Alembic commands ###
