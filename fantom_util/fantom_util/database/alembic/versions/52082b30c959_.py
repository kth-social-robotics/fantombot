"""empty message

Revision ID: 52082b30c959
Revises: 6d38d766cc97
Create Date: 2018-06-18 11:49:23.629104

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '52082b30c959'
down_revision = '6d38d766cc97'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('rating',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('conversation_id', sa.String(), nullable=True),
    sa.Column('start_time', sa.DateTime(), nullable=True),
    sa.Column('rating', sa.Float(), nullable=True),
    sa.Column('turns', sa.Integer(), nullable=True),
    sa.Column('graphsearch_ratio', sa.Float(), nullable=True),
    sa.Column('evi_ratio', sa.Float(), nullable=True),
    sa.Column('fallback_ratio', sa.Float(), nullable=True),
    sa.Column('safetyfilter_ratio', sa.Float(), nullable=True),
    sa.Column('common_ratio', sa.Float(), nullable=True),
    sa.Column('other_ratio', sa.Float(), nullable=True),
    sa.Column('named_entities', sa.ARRAY(sa.String()), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('rating')
    # ### end Alembic commands ###