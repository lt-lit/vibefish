#!/usr/bin/env bash
# Writes the AI "arm" profiles that A/B runs use into a Forge runtime's res/ai/:
#   Vibefish-MC.ai         Default settings; Flat Monte Carlo plays when the game switches it on (--mc on)
#   Vibefish-MCHard.ai     Hard settings: bigger Monte Carlo budgets
#   Vibefish-Heuristic.ai  Default settings with FLAT_MC_ENABLED=false: the plain heuristic AI, even with --mc on
# Needs a Forge build that knows FLAT_MC_ENABLED (2.0.16 snapshots and later). On 2.0.15 the unknown key would
# break profile loading at start-up, so the script refuses there.
#   runner/make-arm-profiles.sh forge/runtime-snapshot
set -euo pipefail
RUNTIME=${1:?forge runtime dir}
AI="$RUNTIME/res/ai"
[ -f "$AI/Default.ai" ] || { echo "no res/ai/Default.ai in $RUNTIME" >&2; exit 1; }
JAR=$(compgen -G "$RUNTIME/forge-gui-desktop-*-jar-with-dependencies.jar" | head -1 || true)
[ -n "$JAR" ] || { echo "no Forge jar in $RUNTIME" >&2; exit 1; }
if ! unzip -p "$JAR" forge/ai/AiProps.class | grep -aq FLAT_MC_ENABLED; then
  echo "this Forge build has no FLAT_MC_ENABLED property; arm profiles need a 2.0.16+ build" >&2
  exit 1
fi
{ grep -v '^FLAT_MC_ENABLED=' "$AI/Default.ai"; echo "FLAT_MC_ENABLED=false"; } > "$AI/Vibefish-Heuristic.ai"
cp "$AI/Default.ai" "$AI/Vibefish-MC.ai"
if [ -f "$AI/Hard.ai" ]; then cp "$AI/Hard.ai" "$AI/Vibefish-MCHard.ai"; fi
echo "arm profiles in $AI: $(ls "$AI" | grep '^Vibefish-' | tr '\n' ' ')"
