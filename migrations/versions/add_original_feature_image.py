"""Add original_featured_image column

Revision ID: 1234567890ab
Revises:
Create Date: 2023-XX-XX

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1234567890ab'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add the new column
    op.add_column('asset', sa.Column('original_featured_image', sa.String(200)))

def downgrade():
    # Remove the column
    op.drop_column('asset', 'original_featured_image')
