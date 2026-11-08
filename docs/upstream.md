# Upstream notes (Forge)

Things seen in Vibefish runs that belong upstream, with how to reproduce them. Vibefish pins
`forge/VERSION`; the Monte Carlo items below are from the daily snapshot (`FORGE_CHANNEL=snapshot`),
i.e. the Flat Monte Carlo work on master that is not in 2.0.15.

Reproduce any game: `runner/make-arm-profiles.sh forge/runtime-snapshot`, then

```bash
FORGE_RUNTIME=$PWD/forge/runtime-snapshot controller/vibefish-sim.sh play --out results/repro \
  --deck-dir "$PWD/forge/runtime-snapshot/res/quest/commanderprecons" \
  --deck "mutant-menace=Mutant Menace [PIP] [2024].dck" --deck "blight-curse=Blight Curse [ECC] [2026].dck" \
  --deck "veloci-ramp-tor=Veloci-Ramp-Tor [LCC] [2023].dck" --deck "squirreled-away=Squirreled Away [BLC] [2024].dck" \
  --games 1 --seed <GAME_SEED minus 1> --clock 1800 --turn-cap 120 --mc on \
  --profile Vibefish-MC --profile Vibefish-MC --profile Vibefish-Heuristic --profile Vibefish-Heuristic
```

`--seed S` plays game 1 with game seed S+1. In the A/B runs the profile assignment rotated by one seat per game;
the seat profiles for a given game are in that run's `run.json` (`games[].profiles`).

## Flat Monte Carlo rollout failures (snapshot 2026-11-08, 2.0.16-SNAPSHOT-11.08)

Forge prints `Flat Monte Carlo rollout failed, using the heuristic choice instead: ...` and plays the heuristic
choice instead. Seen in 4-player Commander games with the pod precons:

| Message | Where seen |
|---|---|
| `java.lang.RuntimeException: Couldn't map The Monarch (756)/...` | ab1, game seed 20461111 (pass `--seed 20461110`), 5 times in that game: the Monarch effect card in the command zone does not survive the game copy |
| `java.lang.RuntimeException: Couldn't map Auntie Ool, Cursewretch (201)/...` | ab1, game seed 20361111 (pass `--seed 20361110`), 5 times in that game: a commander that had left and returned |
| `java.lang.NullPointerException: Cannot invoke "forge.game.card.Card.hasRemembered()" because "origCard" is null` | smoke runs, game seeds 778 and 20261110 (`--mc on` and `--mc max`), 5 times each |

The ab1 games used `--rotate-profiles`; both listed games are game 3 of their shard, where the profile order was
`Vibefish-Heuristic, Vibefish-Heuristic, Vibefish-MC, Vibefish-MC`. At `--mc max` one game also reported `failures=16 unsimulatableCards=11` in
`FLATMC-STATS`; the harness keeps that block per game in `run.json` as `mc_stats`.

## Observations worth sharing

- With the Default profile budgets (450 ms per decision, 2 s per turn) a four-player precon board affords one or
  two rollouts per decision (about 650 ms each); Monte Carlo overrode the heuristic in about 4% of decisions, and
  7 of 23 decisions in one game were abandoned as too slow. At `--mc max` overrides rose to 35% of decisions and
  games took about three times as long. Commander may want its own budget defaults.
- Forge's AI mulligans far less than people do in Commander (about 20% of hands against Playgroup.gg's 36%) and
  its games run about three rounds longer than human games; see the calibration scorecard on the dashboard.
