#!/usr/bin/env bash
# Move Standard state between a runner and two branches of the maintained repository:
#   standard-journal  journal/, genesis.json, report/
#   standard-pins     pins/   (a separate branch: in production, a separate restore domain)
# usage: state.sh load|save <repo checkout> <state dir> [message]
set -euo pipefail
cmd=$1 repo=$(realpath "$2") state=$3 msg=${4:-"standard: state"}
mkdir -p "$state"
state=$(realpath "$state")
for branch in standard-journal standard-pins; do
  wt="$RUNNER_TEMP/$branch"
  if [ "$cmd" = load ]; then
    rm -rf "$wt"
    if git -C "$repo" fetch -q origin "$branch" 2>/dev/null; then
      git -C "$repo" worktree add -q -f "$wt" FETCH_HEAD
      if [ "$branch" = standard-pins ]; then cp -r "$wt/pins" "$state/"; else
        cp -r "$wt/journal" "$state/"; cp "$wt/genesis.json" "$state/"; fi
    fi
  else
    git -C "$repo" worktree remove -f "$wt" 2>/dev/null || true
    rm -rf "$wt"
    if git -C "$repo" fetch -q origin "$branch" 2>/dev/null; then
      git -C "$repo" worktree add -q -f -B "$branch" "$wt" FETCH_HEAD
    else
      git -C "$repo" worktree add -q -f --orphan -b "$branch" "$wt"
    fi
    if [ "$branch" = standard-pins ]; then
      rm -rf "$wt/pins"; cp -r "$state/pins" "$wt/"
    else
      rm -rf "$wt/journal"; cp -r "$state/journal" "$wt/"; cp "$state/genesis.json" "$wt/"
      if [ -d "$state/report" ]; then rm -rf "$wt/report"; cp -r "$state/report" "$wt/"; fi
    fi
    git -C "$wt" add -A
    git -C "$wt" -c user.name=standard -c user.email=standard@standard.invalid commit -q -m "$msg" || true
    git -C "$wt" push -q origin "HEAD:$branch"
  fi
done
