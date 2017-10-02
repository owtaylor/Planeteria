#!/bin/sh

uid=`id -u planeteria`
gid=`id -g planeteria`

/usr/bin/docker run                                                     \
                --name=planeteria                                       \
                --rm                                                    \
                --user=$uid:$gid                                        \
                --security-opt="label=disable"          		\
                --volume=/srv/planeteria-data/:/srv/planeteria/data     \
                --volume=/srv/planeteria-data/log:/srv/planeteria/log   \
                --volume=/srv/planeteria-data/www:/srv/planeteria/www   \
                --publish=8001:8001                                     \
                planeteria
