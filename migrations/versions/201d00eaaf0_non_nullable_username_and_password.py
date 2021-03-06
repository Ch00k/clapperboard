"""Non-nullable username and password

Revision ID: 201d00eaaf0
Revises: 194e5dd5e1d
Create Date: 2014-12-16 14:33:18.883831

"""

# revision identifiers, used by Alembic.
revision = '201d00eaaf0'
down_revision = '194e5dd5e1d'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'user',
        'password',
        existing_type=mysql.VARCHAR(length=255),
        nullable=False
    )
    op.alter_column(
        'user',
        'username',
        existing_type=mysql.VARCHAR(length=255),
        nullable=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'user',
        'username',
        existing_type=mysql.VARCHAR(length=255),
        nullable=True
    )
    op.alter_column(
        'user',
        'password',
        existing_type=mysql.VARCHAR(length=255),
        nullable=True
    )
    # ### end Alembic commands ###
