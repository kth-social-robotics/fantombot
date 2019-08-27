"""empty message

Revision ID: 42ccd12a6320
Revises: 804129b3e01d
Create Date: 2018-06-15 11:39:45.320524

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '42ccd12a6320'
down_revision = '804129b3e01d'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    op.add_column('node_utterance', sa.Column('node_utterance_worker_job_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'node_utterance', 'node_utterance_worker_job', ['node_utterance_worker_job_id'], ['id'])
    op.add_column('node_utterance_worker_job', sa.Column('job_id', sa.Integer(), nullable=True))
    op.add_column('node_utterance_worker_job', sa.Column('worker_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'node_utterance_worker_job', 'worker', ['worker_id'], ['id'])
    op.create_foreign_key(None, 'node_utterance_worker_job', 'job', ['job_id'], ['id'])

    results = connection.execute('select id, worker_job_id from node_utterance_worker_job').fetchall()
    for id_, worker_job_id in results:
        worker_id, job_id = connection.execute(
            'select worker_id, job_id from worker_job WHERE id=%s', worker_job_id
        ).fetchone()

        connection.execute(
            'update node_utterance_worker_job set worker_id=%s, job_id=%s WHERE id=%s', worker_id, job_id, id_
        )

    op.drop_constraint('node_utterance_status_worker_job_id_fkey', 'node_utterance_status', type_='foreignkey')
    op.drop_constraint('node_utterance_worker_job_worker_job_id_fkey', 'node_utterance_worker_job', type_='foreignkey')
    op.drop_column('node_utterance_status', 'worker_job_id')
    op.drop_column('node_utterance_worker_job', 'worker_job_id')
    op.drop_table('worker_job')



def downgrade():
    connection = op.get_bind()

    op.add_column('node_utterance_worker_job', sa.Column('worker_job_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('node_utterance_worker_job_worker_job_id_fkey', 'node_utterance_worker_job', 'worker_job', ['worker_job_id'], ['id'])
    op.add_column('node_utterance_status', sa.Column('worker_job_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('node_utterance_status_worker_job_id_fkey', 'node_utterance_status', 'worker_job', ['worker_job_id'], ['id'])
    op.create_table('worker_job',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('worker_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('job_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['job.id'], name='worker_job_job_id_fkey'),
        sa.ForeignKeyConstraint(['worker_id'], ['worker.id'], name='worker_job_worker_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='worker_job_pkey')
    )

    results = connection.execute('select worker_id, job_id from node_utterance_worker_job').fetchall()
    for worker_id, job_id in results:
        connection.execute('INSERT INTO worker_job (worker_id, job_id, updated_at) VALUES (%s, %s, %s)', worker_id, job_id, datetime.now())

    op.drop_constraint(None, 'node_utterance_worker_job', type_='foreignkey')
    op.drop_constraint(None, 'node_utterance_worker_job', type_='foreignkey')
    op.drop_column('node_utterance_worker_job', 'worker_id')
    op.drop_column('node_utterance_worker_job', 'job_id')
    op.drop_constraint(None, 'node_utterance', type_='foreignkey')
    op.drop_column('node_utterance', 'node_utterance_worker_job_id')

