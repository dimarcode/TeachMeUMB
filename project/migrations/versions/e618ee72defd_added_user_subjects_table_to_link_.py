"""added user_subjects table to link subjects and users

Revision ID: e618ee72defd
Revises: e5e8b9b2eab0
Create Date: 2025-03-11 20:40:48.054832

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e618ee72defd'
down_revision = 'e5e8b9b2eab0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_subject',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('subject_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['subject_id'], ['subject.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'subject_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_subject')
    # ### end Alembic commands ###
