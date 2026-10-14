#!/bin/bash
# Push the current branch and pull it on marty, then (re)install and restart the service.
#
#   ./deploy.sh                      code only
#   ./deploy.sh firmware             also flash the main firmware, then restart the service
#   ./deploy.sh firmware/i2c_scan    flash a test sketch; the service stays stopped
#                                    (run ./deploy.sh firmware to go back)
set -e

HOST=marty
BRANCH=$(git rev-parse --abbrev-ref HEAD)
SKETCH=${1:-}

if [ -n "$(git status --porcelain -- '*.py' '*.ino' marty.service build.sh)" ]; then
    echo "WARNING: uncommitted Python/firmware/service changes won't be deployed."
fi

git push origin "$BRANCH"

ssh "$HOST" "cd ~/marty-v1 \
    && git fetch -q origin \
    && git checkout -q $BRANCH \
    && git pull -q --ff-only origin $BRANCH \
    && mkdir -p ~/.config/systemd/user \
    && cp marty.service ~/.config/systemd/user/ \
    && systemctl --user daemon-reload \
    && systemctl --user enable -q marty \
    && git log --oneline -1"

if [ -n "$SKETCH" ]; then
    # main.py holds the serial port, so stop it before uploading.
    ssh "$HOST" "systemctl --user stop marty && cd ~/marty-v1 && ./build.sh $SKETCH"
    if [ "$SKETCH" != "firmware" ]; then
        echo "Flashed $SKETCH. marty service left stopped. Read output with:"
        echo "  ssh $HOST 'stty -F /dev/ttyACM0 115200 raw -echo; timeout 10 cat /dev/ttyACM0'"
        exit 0
    fi
fi

ssh "$HOST" "systemctl --user restart marty && systemctl --user --no-pager status marty | head -3"
