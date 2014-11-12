#!/bin/bash
# This is a rather crude way to get 15-minute intervals, given only the choice of
# minute or hour intervals. Hopefully cron always runs the scripts after the minute
# has updated, so we won't, say, get 14 14 16 as the values for $minute

source $VIRTUAL_ENV/bin/activate

minute=`date +%M`
case $minute in
    0|15|30|45)
        python $OPENSHIFT_REPO_DIR/planeteria.py
        ;;
esac

