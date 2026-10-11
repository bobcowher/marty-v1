#!/bin/bash
# Push the current branch and pull it on marty, then (re)install and restart the service.
set -e

HOST=marty
BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ -n "$(git status --porcelain -- '*.py' marty.service)" ]; then
    echo "WARNING: uncommitted Python/service changes won't be deployed."
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
    && systemctl --user restart marty \
    && git log --oneline -1 \
    && systemctl --user --no-pager status marty | head -3"
