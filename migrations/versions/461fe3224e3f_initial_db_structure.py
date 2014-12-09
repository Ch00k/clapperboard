# -*- coding: utf-8 -*-

"""Initial db structure

Revision ID: 461fe3224e3f
Revises: None
Create Date: 2014-11-28 17:49:16.822507

"""

# revision identifiers, used by Alembic.
revision = '461fe3224e3f'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, DateTime


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'technology',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'movie',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('url_code', sa.String(length=255), nullable=True),
        sa.Column('show_start', sa.Date(), nullable=True),
        sa.Column('show_end', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'theatre',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('en_name', sa.String(length=255), nullable=True),
        sa.Column('url_code', sa.String(length=255), nullable=True),
        sa.Column('st_url_code', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'imdb_data',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('genre', sa.String(length=255), nullable=True),
        sa.Column('country', sa.String(length=255), nullable=True),
        sa.Column('director', sa.String(length=255), nullable=True),
        sa.Column('cast', sa.String(length=4096), nullable=True),
        sa.Column('runtime', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('movie_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['movie_id'], ['movie.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'show_time',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('theatre_id', sa.Integer(), nullable=True),
        sa.Column('hall_id', sa.Integer(), nullable=True),
        sa.Column('technology_id', sa.Integer(), nullable=True),
        sa.Column('date_time', sa.DateTime(), nullable=True),
        sa.Column('order_url', sa.String(length=255), nullable=True),
        sa.Column('movie_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['movie_id'], ['movie.id'], ),
        sa.ForeignKeyConstraint(['technology_id'], ['technology.id'], ),
        sa.ForeignKeyConstraint(['theatre_id'], ['theatre.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'last_fetched',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date_time', sa.DateTime(), nullable=True),
        sa.Column('theatre_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['theatre_id'], ['theatre.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    theatres_table = table(
        'theatre',
        column('id', Integer),
        column('name', String),
        column('en_name', String),
        column('url_code', String),
        column('st_url_code', String)
    )
    technologies_table = table(
        'technology',
        column('id', Integer),
        column('code', String),
        column('name', String)
    )
    last_fetched_table = table(
        'last_fetched',
        column('id', Integer),
        column('date_time', DateTime),
        column('theatre_id', Integer)
    )

    technologies = [
        ('2d', '2D'),
        ('3d', '3D'),
        ('imax', 'IMAX'),
        ('imax-3d', 'IMAX 3D'),
        ('4dx', '4DX')
    ]

    theatres = [
        (u'Київ', 'Kyiv', '', 'imax-kiev'),
        (u'Харків', 'Kharkiv', 'kharkov', 'pk-kharkov'),
        (u'Львів', 'Lviv', 'lvov', 'pk-lvov'),
        (u'Одеса (Таїрова)', 'Odesa (Tairova)', 'odessa', 'pk-odessa'),
        (u'Одеса (Котовського)', 'Odesa (Kotovskoho)', 'odessa2',
         'pk-odessa2'),
        (u'Суми', 'Sumy', 'sumy', 'pk-sumy'),
        (u'Ялта', 'Yalta', 'yalta', 'pk-yalta')
    ]

    op.bulk_insert(
        theatres_table,
        [
            {
                'name': t[0],
                'en_name': t[1],
                'url_code': t[2],
                'st_url_code': t[3]
            } for t in theatres
        ]
    )
    op.bulk_insert(
        technologies_table,
        [
            {
                'code': t[0],
                'name': t[1]
            } for t in technologies
        ]
    )

    op.bulk_insert(
        last_fetched_table,
        [
            {
                'date_time': None,
                'theatre_id': l
            } for l in range(1, len(theatres) + 1)
        ]
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('last_fetched')
    op.drop_table('show_time')
    op.drop_table('imdb_data')
    op.drop_table('theatre')
    op.drop_table('movie')
    op.drop_table('technology')
    # ### end Alembic commands ###
