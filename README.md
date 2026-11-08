# Vibefish

Commander deck playtesting built on [Forge](https://github.com/Card-Forge/forge)'s headless sim mode.
Drop in a decklist, run hundreds of AI-vs-AI pod games, get consistency stats, matchup win rates and
replayable board states. Over time the project grows deck-specific AI pilots ("playbooks") that an LLM
writes offline and the match loop executes cheaply.

This is the engine. Decks, playbooks and results live in a separate data repository and are passed in by path.
Read [`DESIGN.md`](DESIGN.md) for the full picture.

**Status:** Phase 0 (spike) complete. Forge runs 4-player Commander pods headless, locally and in GitHub Actions.

## Quick start

Requires Java 17+ (CI uses Temurin 21), `curl`, `jq`, `tar`/`bzip2`.

```bash
forge/fetch-forge.sh             # download the pinned Forge release, verify, assemble forge/runtime/
runner/pod-smoke.sh -n 3 -s 42   # the benchmark pod plays 3 games; full log lands in results/
```

Run any Forge sim command through the launcher:

```bash
forge/forge.sh sim -f Commander -D "$PWD/forge/runtime/res/quest/commanderprecons" \
  -d "Mutant Menace [PIP] [2024].dck" "Blight Curse [ECC] [2026].dck" \
     "Veloci-Ramp-Tor [LCC] [2023].dck" "Squirreled Away [BLC] [2024].dck" -n 1 -s 42 -c 900
```

## Layout

| Path | What |
|---|---|
| `forge/` | Version pin, checksum, fetch and launch scripts. The runtime is downloaded, never committed. |
| `runner/` | Sim orchestration and the frozen benchmark pod (`benchmark-pod.json`). |
| `controller/` | Java compiled against the released Forge jar: JSON event logger and playbook controller (Phase 1+). |
| `playbook/` | Playbook schema, validator, examples (Phase 2+). |
| `dashboard/` | Vanilla JS static site for GitHub Pages (Phase 1+). |
| `.github/workflows/` | Sim workflows. |

## License and credits

Vibefish is licensed under the GNU General Public License v3 (see [`LICENSE`](LICENSE)) because it links against
Forge, which is GPL v3. Forge is developed by the Forge team at <https://github.com/Card-Forge/forge>.

Card data and images come from [Scryfall](https://scryfall.com) under their [API terms](https://scryfall.com/docs/api);
images are hotlinked, never stored or altered.

> Vibefish is unofficial Fan Content permitted under the Fan Content Policy. Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC.
