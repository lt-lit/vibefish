# runner/queue

Run requests for the Actions workflows, so a run can be started by a commit instead of a click. `note` says what a
request is for and is ignored by the workflows; the last request stays in each file as the record of what was asked
for. Promoting `testing` to `main` starts nothing.

`ab-run.json`: a push to `testing` that changes it starts `ab-run.yml` with the file's fields as its inputs (the same
names and defaults as the Run workflow form; a new `requested` value is enough to run the same request again).
`"runs": [{"decks": ..., "arms": ..., "seed": ...}, ...]` holds several requests played as one workflow run, each
with its own decks, arms and seed, the top-level fields as defaults. A deck written `deck@name` plays the candidate
`playbook/variants/<deck>-<name>.json`; a candidate played with `arms: playbook` on the seed of an earlier run pairs
with that run's stock arm (`runner/ab.py join`). Runs do not wait for each other: each push starts its run at once.
Seeds: a deck's runs are kept ten seeds apart, because nearby seeds draw the same opponents (`runner/ab.py`, Seeds),
and a confirming run gets a seed of its own.

`league-run.json`: a push to `testing` that changes it starts `league-run.yml` with the file's fields as its inputs
(`league`, `cycles`, `shards`, `jobs_per_shard`, `seed`, `run_id`, `forge_channel`, `forge_snapshot_build`, `profile`, `mc`,
`playbooks`, `publish`; what is left out takes the form's default). `league` is the deck list: `runner/precon-league.json`
is the 91 precons, `runner/leagues/bots-v1.json` the four decks that have a shipped playbook, as one table.
`league_request.py` is what the workflow reads either source with; `EVENT=push python3 -I runner/queue/league_request.py`
prints what the queued request would run, and refuses a value its field does not allow.

`forge-archive.json`: a push to `testing` that changes it starts `forge-archive.yml` for the snapshot `builds` named
there (comma-separated). An archive that is already on the release `forge-runtimes` is kept as it is; `"replace": true`
overwrites it, and `forge/SHA256SUMS` then needs the new checksum at once, because every pinned fetch verifies
against it.
