#!/bin/zsh
# Run a UE python script with the project/level guard prepended.
cd "/private/tmp/claude-501/-Users-ben-Documents-New-project/c7b8ef13-3903-46ab-bd2b-18279bb95fe6/scratchpad"
{ cat _guard.py; echo ""; cat "$1"; } > _guarded_tmp.py
python3 uepy.py _guarded_tmp.py
