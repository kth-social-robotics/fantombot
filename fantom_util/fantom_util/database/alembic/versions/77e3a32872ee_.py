"""empty message

Revision ID: 77e3a32872ee
Revises: be2f23cf3a6d
Create Date: 2018-05-16 14:06:12.931143

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77e3a32872ee'
down_revision = 'be2f23cf3a6d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('merging',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('left_node_id', sa.Integer(), nullable=True),
    sa.Column('right_node_id', sa.Integer(), nullable=True),
    sa.Column('merged', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['left_node_id'], ['node.id'], ),
    sa.ForeignKeyConstraint(['right_node_id'], ['node.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('merging')
    # ### end Alembic commands ###