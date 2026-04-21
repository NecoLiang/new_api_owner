# deploy/

Production deployment assets for new-api running on a single host with MySQL.

## Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Compose template (mysql 8.4 + new-api). Reads secrets/paths from `.env`. |
| `.env.example` | Template for secrets/config. Copy to runtime `.env` and fill in. |
| `update.sh` | Server-side one-shot updater: `git pull` → copy compose → `docker compose up -d`. |
| `migrate_sqlite_to_mysql.py` | One-time data migration from an existing SQLite `one-api.db` to MySQL. |

## Server layout

```
/root/new-api-src/       # git clone of this repo (source of truth)
/root/new-api/           # runtime dir (state lives here, NOT in git)
  .env                   # real secrets, chmod 600
  docker-compose.yml     # synced from /root/new-api-src/deploy/ by update.sh
  data/                  # new-api data dir (logs, SQLite backups)
  mysql-data/            # MySQL 8.4 datadir
```

## First-time install on a new host

```bash
# 1. Clone repo (source of truth)
git clone https://github.com/NecoLiang/new_api_owner.git /root/new-api-src

# 2. Runtime dir
mkdir -p /root/new-api && cd /root/new-api
cp /root/new-api-src/deploy/.env.example .env
chmod 600 .env
# edit .env: set strong passwords, keep MYSQL_DATABASE/USER as-is unless you know why

# 3. Symlink update.sh for convenience
ln -sf /root/new-api-src/deploy/update.sh /usr/local/bin/new-api-update

# 4. First launch
new-api-update
```

## Ongoing updates

After pushing changes to the repo (either newapi source changes that need a new
image, or just compose tweaks):

```bash
ssh server8 new-api-update
```

This pulls the repo and restarts containers. If you rebuild the image as a
different tag, bump `NEW_API_IMAGE` in `/root/new-api/.env` first.

## SQLite → MySQL migration (only needed once)

If the existing `/root/new-api/data/one-api.db` still holds data:

```bash
cd /root/new-api
docker compose stop new-api            # keep mysql running
set -a && source .env && set +a
MYSQL_HOST=$(docker inspect new-api-mysql --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}') \
python3 /root/new-api-src/deploy/migrate_sqlite_to_mysql.py
docker compose up -d new-api
```

## Access

- Web / admin: `http://<host>:${NEW_API_PORT}`
- API base: `http://<host>:${NEW_API_PORT}/v1`

MySQL port is **not** published to the host; connect via
`docker exec -it new-api-mysql mysql -uroot -p<root_pw> newapi`.
