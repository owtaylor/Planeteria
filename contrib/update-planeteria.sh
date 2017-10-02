#!/bin/bash

set -e

cd /srv/planeteria

image=planeteria:latest
created_date=""
vcs_ref=""

IFS=";" read x y < <(
    docker inspect --type=image -f '{{index .Config.Labels "org.label-schema.vcs-ref"}};{{.Created}}' $image
)

if [ $? = 0 ] ; then
    vcs_ref=$x
    created_date=$y
fi

git fetch origin
head_revision=`git rev-parse origin/master`

rebuild=false

if [ "$vcs_ref" = "" ] ; then
    image_revision='<none>'
else
    image_revision=`git rev-parse $vcs_ref`
fi

if [ $head_revision != $image_revision ] ; then
    rebuild=true
    echo "Must rebuild for git revision"
    echo "Head: $head_revision"
    echo "Image: $image_revision"
    echo
fi

created_ts=$(date --date "$created_date" +"%s")
now_ts=$(date +"%s")
ago=$((($now_ts - $created_ts)/(24*60*60)))

if [ "$ago" -ge 7 ] ; then
    echo "Image was created $ago days ago, must rebuild"
    echo
fi

if $rebuild ; then
    git reset --hard $head_revision
    docker build --no-cache --build-arg vcs_ref="$head_revision" -t planeteria .
    systemctl restart planeteria
    docker images --quiet --filter "dangling=true" | xargs --no-run-if-empty docker rmi
fi

exec /usr/bin/docker exec planeteria /srv/planeteria/planeteria.py
