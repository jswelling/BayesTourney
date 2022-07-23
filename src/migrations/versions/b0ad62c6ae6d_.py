"""empty message

Revision ID: b0ad62c6ae6d
Revises: c84d60b69801
Create Date: 2022-07-23 18:08:14.890208

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0ad62c6ae6d'
down_revision = 'c84d60b69801'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('email', sa.String(), nullable=True))
    op.add_column('user', sa.Column('password_hash', sa.String(), nullable=False))
    op.add_column('user', sa.Column('date_registered', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('admin', sa.Boolean(), nullable=False))
    op.add_column('user', sa.Column('confirmed', sa.Boolean(), nullable=False))
    op.add_column('user', sa.Column('confirmed_on', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_user_date_registered'), 'user', ['date_registered'], unique=False)
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.drop_column('user', 'password')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('password', sa.VARCHAR(), nullable=False))
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_index(op.f('ix_user_date_registered'), table_name='user')
    op.drop_column('user', 'confirmed_on')
    op.drop_column('user', 'confirmed')
    op.drop_column('user', 'admin')
    op.drop_column('user', 'date_registered')
    op.drop_column('user', 'password_hash')
    op.drop_column('user', 'email')
    # ### end Alembic commands ###