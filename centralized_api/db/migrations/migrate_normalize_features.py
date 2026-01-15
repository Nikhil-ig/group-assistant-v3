"""
Migration: normalize feature flags into features_enabled

This script finds group settings documents that contain top-level feature
flags (e.g. `auto_delete_commands`) that duplicate entries inside
`features_enabled`. It will:

- By default run in dry-run mode and print a summary of documents that would
  be changed.
- If run with --apply it will update documents to ensure `features_enabled`
  contains the canonical boolean values. If `features_enabled` already has a
  key it will be preserved; if missing it will be filled from the top-level
  value.
- Optionally, when --backup is passed, the original documents that will be
  modified are copied to `group_settings_backup` with a timestamp.
- After changes, top-level duplicate keys will be removed (unset).

Usage:
    python migrate_normalize_features.py            # dry-run
    python migrate_normalize_features.py --apply    # apply changes
    python migrate_normalize_features.py --apply --backup

NOTE: This script is safe but destructive when --apply is used. Run a dry-run
first and consider creating a DB-level backup.
"""

import argparse
import pprint
import time
from datetime import datetime
from typing import Dict, Any

from pymongo import MongoClient

# Read configuration from centralized_api.config if available, else fall back to env
try:
    from centralized_api.config import MONGODB_URI, MONGODB_DATABASE
except Exception:
    import os

    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "telegram_bot")

# Keys that commonly were duplicated at top-level in older schema versions.
# We will only act on keys that are present both at top-level and inside
# features_enabled. The script is conservative: if features_enabled already
# contains a value for a key we will NOT overwrite it; we'll only populate
# missing keys from the top-level alias.
POSSIBLE_TOP_LEVEL_KEYS = [
    "auto_delete_commands",
    "auto_delete_welcome",
    "auto_delete_left",
    # add other known boolean aliases here if you used them historically
]


def connect():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]
    return client, db


def find_candidates(db):
    col = db["group_settings"]
    query = {"$or": [{k: {"$exists": True}} for k in POSSIBLE_TOP_LEVEL_KEYS]}
    # Only return docs where features_enabled is present or some top-level flags exist
    cursor = col.find(query)
    return list(cursor)


def summarize_candidates(docs):
    out = {
        "total_found": len(docs),
        "examples": [],
        "conflicts": [],
    }

    for d in docs[:20]:
        gid = d.get("group_id")
        features = d.get("features_enabled", {}) or {}
        top_vals = {k: d.get(k) for k in POSSIBLE_TOP_LEVEL_KEYS if k in d}
        conflicts = {}
        for k, tv in top_vals.items():
            if k in features and features[k] != tv:
                conflicts[k] = {"features_enabled": features.get(k), "top_level": tv}
        out["examples"].append({"group_id": gid, "top_level": top_vals, "features_present": list(features.keys())})
        if conflicts:
            out["conflicts"].append({"group_id": gid, "conflicts": conflicts})
    return out


def apply_migration(db, docs, backup=False, prefer_top=False):
    col = db["group_settings"]
    backup_col = db.get_collection("group_settings_backup") if backup else None
    modified_count = 0
    for d in docs:
        gid = d.get("group_id")
        features = d.get("features_enabled", {}) or {}
        updates = {}
        unset_keys = []

        for key in POSSIBLE_TOP_LEVEL_KEYS:
            if key in d:
                top_val = d.get(key)
                # If features_enabled lacks this key, populate it from top-level
                if key not in features:
                    updates[f"features_enabled.{key}"] = top_val
                else:
                    # Conflict: both exist and differ
                    if features.get(key) != top_val:
                        if prefer_top:
                            # overwrite features_enabled with top-level value
                            updates[f"features_enabled.{key}"] = top_val
                # Mark the top-level key for removal
                unset_keys.append(key)

        if not updates and not unset_keys:
            continue

        if backup_col is not None:
            # copy the original doc to backup collection with timestamp
            original = dict(d)
            original["_migrated_at"] = datetime.utcnow()
            backup_col.insert_one(original)

        update_op = {}
        if updates:
            update_op.setdefault("$set", {}).update(updates)
        if unset_keys:
            update_op.setdefault("$unset", {}).update({k: "" for k in unset_keys})
        update_op.setdefault("$set", {}).update({"updated_at": datetime.utcnow()})

        res = col.find_one_and_update({"group_id": gid}, update_op, return_document=False)
        modified_count += 1

    return modified_count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    parser.add_argument("--backup", action="store_true", help="Backup modified docs into group_settings_backup before applying")
    parser.add_argument("--prefer-top", action="store_true", help="When conflicts exist, prefer top-level values and overwrite features_enabled")
    args = parser.parse_args()

    client, db = connect()
    try:
        docs = find_candidates(db)
        summary = summarize_candidates(docs)

        print("Migration summary:")
        pprint.pprint(summary)
        print()

        if not docs:
            print("No candidate documents found. Nothing to do.")
            return

        if not args.apply:
            print("Dry run complete. Re-run with --apply to perform the migration.")
            return

        print("Applying migration...")
        modified = apply_migration(db, docs, backup=args.backup, prefer_top=args.prefer_top)
        print(f"Modified {modified} documents.")
        print("Done.")

    finally:
        client.close()


if __name__ == "__main__":
    main()
