#!/usr/bin/env bash
# Compile and run the free-standing pre-flight. See CoreMinimal.h in this
# directory for what a pass here does and does not mean.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${1:-$ROOT/Saved/SelfTest/econ_harness}"
SRC_RULES="${STACKTOWN_RULES_CPP:-$ROOT/Source/StacktownAlpha/Private/StacktownEconomyRules.cpp}"

mkdir -p "$(dirname "$OUT")"
clang++ -std=c++20 -O0 -g -Wall -Wextra -Wno-unused-parameter \
	-I"$ROOT/Tools/preflight" \
	-I"$ROOT/Source/StacktownAlpha/Public" \
	-I"$ROOT/Source/StacktownAlpha/Private/Tests" \
	"$ROOT/Tools/preflight/harness.cpp" \
	"$SRC_RULES" \
	-o "$OUT"
"$OUT"
