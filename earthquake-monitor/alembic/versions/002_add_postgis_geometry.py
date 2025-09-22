"""Add PostGIS geometry column for spatial queries

Revision ID: 002_add_postgis_geometry
Revises: abc123def456
Create Date: 2025-09-22 12:00:00.000000

"""

import geoalchemy2
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "002_add_postgis_geometry"
down_revision = "abc123def456"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # Add geometry column
    op.add_column(
        "earthquakes",
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
    )

    # Create spatial index
    op.execute(
        "CREATE INDEX ix_earthquakes_location_gist ON earthquakes USING GIST (location);"
    )

    # Populate geometry column from existing lat/lng data
    op.execute(
        """
        UPDATE earthquakes
        SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        WHERE location IS NULL;
    """
    )


def downgrade() -> None:
    # Drop spatial index
    op.execute("DROP INDEX IF EXISTS ix_earthquakes_location_gist;")

    # Drop geometry column
    op.drop_column("earthquakes", "location")
