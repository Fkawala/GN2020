#!/bin/bash
tmux splitw -h -p 35
tmux send-keys "countdown $1; sudo shutdown -h now" C-m
tmux selectp -t 0

