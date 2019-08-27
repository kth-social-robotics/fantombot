"""empty message

Revision ID: be2f23cf3a6d
Revises:
Create Date: 2018-04-15 21:04:28.539213

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils

# revision identifiers, used by Alembic.
revision = 'be2f23cf3a6d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION ltree')
    op.create_table('job',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('is_user', sa.Boolean(), nullable=True),
    sa.Column('persona_sample', sa.ARRAY(sa.String()), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('node',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('_path', sqlalchemy_utils.types.ltree.LtreeType(), server_default='', nullable=True),
    sa.Column('visited_count', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['node.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('utterance',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('utterance_text', sa.String(), nullable=True),
    sa.Column('spellchecked_text', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('worker',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('external_worker_id', sa.String(), nullable=True),
    sa.Column('blocked', sa.Boolean(), nullable=True),
    sa.Column('source', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('external_worker_id', 'source', name='_external_worker_id_source_uc')
    )
    op.create_table('node_equivalence',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('left_node_id', sa.Integer(), nullable=True),
    sa.Column('right_node_id', sa.Integer(), nullable=True),
    sa.Column('verified', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['left_node_id'], ['node.id'], ),
    sa.ForeignKeyConstraint(['right_node_id'], ['node.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('training',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('worker_id', sa.Integer(), nullable=True),
    sa.Column('tasks', sa.ARRAY(sa.Integer()), nullable=True),
    sa.ForeignKeyConstraint(['worker_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('utterance_id', sa.Integer(), nullable=True),
    sa.Column('is_user', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['utterance_id'], ['utterance.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('worker_job',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('worker_id', sa.Integer(), nullable=True),
    sa.Column('job_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['job.id'], ),
    sa.ForeignKeyConstraint(['worker_id'], ['worker.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('node_utterance',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('node_id', sa.Integer(), nullable=True),
    sa.Column('utterance_id', sa.Integer(), nullable=True),
    sa.Column('tts_id', sa.Integer(), nullable=True),
    sa.Column('source', sa.String, nullable=True),
    sa.Column('with_audio', sa.Boolean(), nullable=True),
    sa.Column('corrected', sa.Boolean(), nullable=True),
    sa.Column('used_text_as_input', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['node_id'], ['node.id'], ),
    sa.ForeignKeyConstraint(['tts_id'], ['tts.id'], ),
    sa.ForeignKeyConstraint(['utterance_id'], ['utterance.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('job_node_utterance',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('job_id', sa.Integer(), nullable=True),
    sa.Column('node_utterance_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['job.id'], ),
    sa.ForeignKeyConstraint(['node_utterance_id'], ['node_utterance.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('node_utterance_status',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('node_utterance_id', sa.Integer(), nullable=True),
    sa.Column('referenced_node_utterance_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.String, nullable=True),
    sa.Column('worker_job_id', sa.Integer(), nullable=True),
    sa.Column('with_audio', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['node_utterance_id'], ['node_utterance.id'], ),
    sa.ForeignKeyConstraint(['referenced_node_utterance_id'], ['node_utterance.id'], ),
    sa.ForeignKeyConstraint(['worker_job_id'], ['worker_job.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('node_utterance_worker_job',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('worker_job_id', sa.Integer(), nullable=True),
    sa.Column('node_utterance_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['node_utterance_id'], ['node_utterance.id'], ),
    sa.ForeignKeyConstraint(['worker_job_id'], ['worker_job.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('node_utterance_worker_job')
    op.drop_table('node_utterance_status')
    op.drop_table('job_node_utterance')
    op.drop_table('node_utterance')
    op.drop_table('worker_job')
    op.drop_table('tts')
    op.drop_table('training')
    op.drop_table('node_equivalence')
    op.drop_table('worker')
    op.drop_table('utterance')
    op.drop_table('node')
    op.drop_table('job')
    op.execute('DROP EXTENSION ltree')
