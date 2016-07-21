#!/bin/sh
USER='root'

cd ../

HOST="$1"
PASSWD="$2"

ncftp -u $USER -p $PASSWD $HOST <<END_SCRIPT
cd /mnt/storage/materials
binary
put ka-lite-static-0.16.7b2.tar.gz
quit
END_SCRIPT

cd ansible/