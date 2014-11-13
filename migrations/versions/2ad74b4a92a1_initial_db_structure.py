"""Initial db structure

Revision ID: 2ad74b4a92a1
Revises: None
Create Date: 2014-11-12 20:56:45.262549

"""

# revision identifiers, used by Alembic.
revision = '2ad74b4a92a1'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('movie',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('show_start', sa.Integer(), nullable=True),
    sa.Column('show_end', sa.Integer(), nullable=True),
    sa.Column('url', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('imdb_data',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('rating', sa.Float(), nullable=True),
    sa.Column('movie_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['movie_id'], ['movie.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('show_time',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('date_time', sa.Integer(), nullable=True),
    sa.Column('hall_id', sa.Integer(), nullable=True),
    sa.Column('technology', sa.String(length=8), nullable=True),
    sa.Column('order_url', sa.String(length=255), nullable=True),
    sa.Column('movie_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['movie_id'], ['movie.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('show_time')
    op.drop_table('imdb_data')
    op.drop_table('movie')
    ### end Alembic commands ###