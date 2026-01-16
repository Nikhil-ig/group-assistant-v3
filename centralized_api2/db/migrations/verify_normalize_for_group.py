"""
Verification helper for normalize_features migration for a single group

This script prints the document before and after applying the same
normalization logic as the migration script for a single `group_id`.
By default it runs in dry-run mode and only shows the computed 'after' doc.
With --apply it will actually perform the update. With --prefer-top it will
prefer top-level values in conflicts.

Usage:
    python verify_normalize_for_group.py <group_id>             # dry-run
    python verify_normalize_for_group.py <group_id> --apply     # apply change
    python verify_normalize_for_group.py <group_id> --apply --backup --prefer-top

"""
import argparse
import pprint
from datetime import datetime

try:
    from centralized_api.config import MONGODB_URI, MONGODB_DATABASE
except Exception:
    import os
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "telegram_bot")

from pymongo import MongoClient

POSSIBLE_TOP_LEVEL_KEYS = [
    "auto_delete_commands",
    "auto_delete_welcome",
    "auto_delete_left",
]


def connect():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]
    return client, db


def compute_normalized(doc, prefer_top=False):
    if doc is None:
        return None
    features = dict(doc.get("features_enabled", {}) or {})
    updates = {}
    unset_keys = []
    for key in POSSIBLE_TOP_LEVEL_KEYS:
        if key in doc:
            top_val = doc.get(key)
            if key not in features:
                features[key] = top_val
                updates[f"features_enabled.{key}"] = top_val
            else:
                if features.get(key) != top_val:
                    if prefer_top:
                        features[key] = top_val
                        updates[f"features_enabled.{key}"] = top_val
            unset_keys.append(key)
    normalized = dict(doc)
    normalized["features_enabled"] = features
    for k in unset_keys:
        normalized.pop(k, None)
    normalized["updated_at"] = datetime.utcnow()
    return normalized, updates, unset_keys


def apply_for_group(db, group_id, updates, unset_keys, backup=False):
    col = db["group_settings"]
    if backup:
        backup_col = db.get_collection("group_settings_backup")
        original = col.find_one({"group_id": group_id})
        if original:
            original["_migrated_at"] = datetime.utcnow()
            backup_col.insert_one(original)
    update_op = {}
    if updates:
        update_op.setdefault("$set", {}).update(updates)
    if unset_keys:
        update_op.setdefault("$unset", {}).update({k: "" for k in unset_keys})
    update_op.setdefault("$set", {}).update({"updated_at": datetime.utcnow()})
    res = col.find_one_and_update({"group_id": group_id}, update_op, return_document=True)
    return res


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("group_id", type=int)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--prefer-top", action="store_true")
    args = parser.parse_args()

    client, db = connect()
    try:
        col = db["group_settings"]
        doc = col.find_one({"group_id": args.group_id})
        print("Before:")
        pprint.pprint(doc)
        normalized, updates, unset_keys = compute_normalized(doc, prefer_top=args.prefer_top)
        print('\nComputed After (dry-run):')
        pprint.pprint(normalized)
        print('\nProposed updates:')
        pprint.pprint(updates)
        print('Keys to unset:')
        pprint.pprint(unset_keys)
        if args.apply:
            res = apply_for_group(db, args.group_id, updates, unset_keys, backup=args.backup)
            print('\nAfter applying:')
            pprint.pprint(res)
    finally:
        client.close()

if __name__ == '__main__':
    main()
