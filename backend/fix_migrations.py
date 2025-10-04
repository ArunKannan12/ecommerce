#!/usr/bin/env python
"""
fix_migrations.py
Automatically fixes migration inconsistencies on deployment.
"""

import os
import django
from django.db import connection
from django.core.management import call_command
from django.db.migrations.loader import MigrationLoader

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()


def get_applied_migrations():
    """Return a set of applied migrations in the database."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT app, name FROM django_migrations")
        return {(row[0], row[1]) for row in cursor.fetchall()}


def fake_missing_migrations(app_label):
    """Fake migrations that exist in code but are missing in DB."""
    loader = MigrationLoader(connection)
    graph = loader.graph

    applied = get_applied_migrations()
    migrations_in_code = [
        key[1] for key in graph.nodes
        if key[0] == app_label
    ]

    for migration_name in migrations_in_code:
        if (app_label, migration_name) not in applied:
            print(f"🚨 Faking {app_label}.{migration_name}...")
            call_command("migrate", app_label, migration_name, fake=True)


if __name__ == "__main__":
    # Step 1: Fake products migrations
    fake_missing_migrations("products")

    # Step 2: Fake promoter migrations
    fake_missing_migrations("promoter")

    # Step 3: Fake orders migrations
    fake_missing_migrations("orders")

    # Step 4: Fake admin_dashboard migrations
    fake_missing_migrations("admin_dashboard")

    # Step 5: Apply remaining migrations normally
    print("🚨 Applying remaining migrations normally...")
    call_command("migrate")

    print("✅ Migration fix completed successfully!")
