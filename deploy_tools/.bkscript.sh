# carpeta destino backups
BASEPATH=$HOME/sites/SITENAME/bcks/;

DB_NAME=
DB_USERNAME=
DB_PASSWORD=

# find . -type f -mtime +60 -name "*.gz" -o -name "*.sql" -exec rm -f {} \;
#/usr/bin/pg_dump --inserts --dbname=postgres://"${DB_USERNAME}":"${DB_PASSWORD}"@localhost:5432/"${DB_NAME}" |gzip > "${BASEPATH}$(date +%Y-%m-%d).sql.gz"
/usr/bin/pg_dump -Fc --dbname=postgres://"${DB_USERNAME}":"${DB_PASSWORD}"@localhost:5432/"${DB_NAME}" |gzip > "${BASEPATH}$(date +%Y-%m-%d).backup.gz"