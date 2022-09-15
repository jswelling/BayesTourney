"""add user group pairs

Revision ID: 62f460f5d2b7
Revises: 6fc3fa8b9d7f
Create Date: 2022-08-17 19:15:24.885666

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '62f460f5d2b7'
down_revision = '6fc3fa8b9d7f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_group_pair',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['group.id'], name='user_group_pair_group_id_constraint'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='user_group_pair_user_id_constraint'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user_group_pair', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_group_pair_group_id'), ['group_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_group_pair_user_id'), ['user_id'], unique=False)
    op.execute("create temporary table t1 as select id from 'group' where name = 'everyone'")
    op.execute("create temporary table t2 as select id, name from 'group'")
    op.execute("INSERT into 'user_group_pair' (user_id, group_id) "
               "select distinct user.id, t1.id from user, t1")
    op.execute("INSERT into 'user_group_pair' (user_id, group_id) "
               "select distinct user.id, t2.id from user, t2 where user.username = t2.name")
    op.execute("drop table t2")
    op.execute("drop table t1")

        

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_group_pair', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_group_pair_user_id'))
        batch_op.drop_index(batch_op.f('ix_user_group_pair_group_id'))

    op.drop_table('user_group_pair')
    # ### end Alembic commands ###