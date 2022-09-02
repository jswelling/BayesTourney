"""add_tourney_permission_fields

Revision ID: fefd35fe6e72
Revises: b0cd5dcbcc87
Create Date: 2022-08-29 13:47:02.991717

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fefd35fe6e72'
down_revision = 'b0cd5dcbcc87'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tourneys', schema=None) as batch_op:
        batch_op.add_column(sa.Column('owner_read', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('owner_write', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('owner_delete', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('group_read', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('group_write', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('group_delete', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('other_read', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('other_write', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('other_delete', sa.Boolean(), nullable=True))
    op.execute("UPDATE tourneys SET owner_read = 1")
    op.execute("UPDATE tourneys SET owner_write = 1")
    op.execute("UPDATE tourneys SET owner_delete = 1")
    op.execute("UPDATE tourneys SET group_read = 1")
    op.execute("UPDATE tourneys SET group_write = 0")
    op.execute("UPDATE tourneys SET group_delete = 0")
    op.execute("UPDATE tourneys SET other_read = 0")
    op.execute("UPDATE tourneys SET other_write = 0")
    op.execute("UPDATE tourneys SET other_delete = 0")
        
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tourneys', schema=None) as batch_op:
        batch_op.drop_column('other_delete')
        batch_op.drop_column('other_write')
        batch_op.drop_column('other_read')
        batch_op.drop_column('group_delete')
        batch_op.drop_column('group_write')
        batch_op.drop_column('group_read')
        batch_op.drop_column('owner_delete')
        batch_op.drop_column('owner_write')
        batch_op.drop_column('owner_read')

    # ### end Alembic commands ###
