#!/usr/bin/env python
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.core.management import call_command

print("Faking products.0017 migration if needed...")
call_command("migrate", "products", "0017", fake=True)

print("Applying remaining migrations...")
call_command("migrate")
print("Migration fix completed successfully ✅")
