#! /bin/bash

set -e

for index in movies personas genres; do
    echo "uploading $index"
    for type in settings mapping data; do
        /usr/bin/dumb-init elasticdump \
        --input=/data/"$index"_"$type".json \
        --output=http://$ELASTIC_HOST:$ELASTIC_PORT/$index \
        --type=$type
    done
done
