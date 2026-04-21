#!/usr/bin/env python3
"""Migrate new-api data from SQLite to MySQL (in-place row copy).

Prereq: MySQL schema already exists (run new-api once against an empty MySQL
so GORM auto-migrate creates the tables). Then stop new-api and run this
script against the SQLite backup + MySQL.

Environment:
    SQLITE_PATH      default /root/new-api/data/one-api.db
    MYSQL_HOST       required
    MYSQL_PORT       default 3306
    MYSQL_USER       required
    MYSQL_PASSWORD   required
    MYSQL_DATABASE   required
"""
import os
import re
import sys
import sqlite3

import pymysql

SQLITE_PATH = os.environ.get("SQLITE_PATH", "/root/new-api/data/one-api.db")
MYSQL_HOST = os.environ["MYSQL_HOST"]
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ["MYSQL_USER"]
MYSQL_PWD = os.environ["MYSQL_PASSWORD"]
MYSQL_DB = os.environ["MYSQL_DATABASE"]

TZ_SUFFIX = re.compile(r"([+-]\d{2}:?\d{2}|Z)$")


def strip_tz(value):
    if isinstance(value, str) and TZ_SUFFIX.search(value):
        return TZ_SUFFIX.sub("", value).strip()
    return value


def main():
    sconn = sqlite3.connect(SQLITE_PATH)
    sconn.row_factory = sqlite3.Row
    mconn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PWD,
        database=MYSQL_DB,
        charset="utf8mb4",
        autocommit=False,
    )
    mcur = mconn.cursor()
    scur = sconn.cursor()

    scur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    sqlite_tables = [r[0] for r in scur.fetchall()]

    mcur.execute("SHOW TABLES")
    mysql_tables = {r[0] for r in mcur.fetchall()}

    mcur.execute("SET FOREIGN_KEY_CHECKS=0")
    mcur.execute("SET UNIQUE_CHECKS=0")
    mcur.execute("SET SESSION sql_mode = ''")

    summary = []
    for t in sqlite_tables:
        if t not in mysql_tables:
            summary.append((t, "SKIP (not in mysql)", 0))
            continue

        rows = list(scur.execute(f"SELECT * FROM `{t}`"))
        if not rows:
            summary.append((t, "empty", 0))
            continue

        cols = [d[0] for d in scur.description]

        mcur.execute(f"SHOW COLUMNS FROM `{t}`")
        mysql_cols = {r[0] for r in mcur.fetchall()}
        use_cols = [c for c in cols if c in mysql_cols]
        missing = [c for c in cols if c not in mysql_cols]

        mcur.execute(f"TRUNCATE TABLE `{t}`")

        placeholders = ",".join(["%s"] * len(use_cols))
        colnames = ",".join(f"`{c}`" for c in use_cols)
        sql = f"INSERT INTO `{t}` ({colnames}) VALUES ({placeholders})"

        inserted = 0
        for row in rows:
            values = [strip_tz(row[c]) for c in use_cols]
            try:
                mcur.execute(sql, values)
                inserted += 1
            except Exception as exc:
                print(f"  !! row insert failed in {t}: {exc}", file=sys.stderr)
                print(f"     row={dict(zip(use_cols, values))}", file=sys.stderr)
                raise

        extra = f" (ignored cols: {missing})" if missing else ""
        summary.append((t, f"migrated{extra}", inserted))

    mcur.execute("SET FOREIGN_KEY_CHECKS=1")
    mcur.execute("SET UNIQUE_CHECKS=1")
    mconn.commit()
    mconn.close()
    sconn.close()

    print("--- MIGRATION SUMMARY ---")
    for t, status, n in summary:
        print(f"  {t:<40s} {status:<30s} rows={n}")


if __name__ == "__main__":
    main()
