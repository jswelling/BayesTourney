#! /bin/bash

timestamp=`date "+%Y%m%d-%H%M%S"`
echo .dump | sqlite3 ./mydb.db > mydb_backup_${timestamp}.sql
echo .backup main mydb_backup_${timestamp}.db | sqlite3 ./mydb.db
