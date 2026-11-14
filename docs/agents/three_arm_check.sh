#!/usr/bin/env bash
# three_arm_check.sh EXAM_DIR DECK VARIANT OUT_DIR: the card check of a candidate examined with both attacks. A session helper.
#
# EXAM_DIR holds the unzipped shard artifacts of an ab-run workflow run (fetch_artifact.sh) with the request
# `DECK@VARIANT` (stock, playbook: the candidate with its go-wide attack) and `DECK@VARIANT-forgeattack` (playbook: the
# same rules, the attack left to Forge). Merges the shards of each (shards.sh), writes the playtest report of the
# three arms into OUT_DIR/DECK-{stock,gowide,forgeattack}.{md,json} and what each attack arm casts fifteen points less
# or more often than the stock pilot on the same tables into OUT_DIR/DECK-{gowide,forgeattack}-card-diff.txt, and
# prints the wins and the counts. What a shipped playbook casts less than its stock pilot goes into its notes.
set -e
D=$1; deck=$2; v=$3; O=$4
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
mkdir -p "$O"
cd "$ROOT"
docs/agents/shards.sh "$D" "$deck@$v" > /dev/null
docs/agents/shards.sh "$D" "$deck@$v-forgeattack" > /dev/null
python3 -I runner/playtest.py "$D/results/ab-$deck@$v" --arm stock --md "$O/$deck-stock.md" --json "$O/$deck-stock.json" > /dev/null
python3 -I runner/playtest.py "$D/results/ab-$deck@$v" --arm playbook --md "$O/$deck-gowide.md" --json "$O/$deck-gowide.json" > /dev/null
python3 -I runner/playtest.py "$D/results/ab-$deck@$v-forgeattack" --arm playbook --md "$O/$deck-forgeattack.md" --json "$O/$deck-forgeattack.json" > /dev/null
for a in gowide forgeattack; do
  python3 -I docs/agents/arm_card_diff.py "$O/$deck-stock.json" "$O/$deck-$a.json" > "$O/$deck-$a-card-diff.txt"
  head -1 "$O/$deck-$a-card-diff.txt" | sed "s/playbook/$a/"
  echo "  $a: cast less $(awk '/cast LESS/{f=1;next} /cast more/{f=0} f&&NF' "$O/$deck-$a-card-diff.txt" | wc -l), cast more $(awk '/cast more/{f=1;next} f&&NF' "$O/$deck-$a-card-diff.txt" | wc -l)"
done
