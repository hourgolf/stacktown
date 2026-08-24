#!/bin/sh
set -eu

project_root=$(git rev-parse --show-toplevel)
cd "$project_root"

if ! command -v git-lfs >/dev/null 2>&1; then
  echo "Git LFS is not installed. Install it, then rerun this script."
  exit 1
fi

git lfs install --local
git lfs track "*.uasset" "*.umap"

echo "Future Unreal binary tracking is configured."
echo "No history was migrated and no files were staged. Review .gitattributes with git diff."
