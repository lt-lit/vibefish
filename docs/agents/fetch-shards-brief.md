# Brief: fetch a run's shard artifacts (a small agent, Haiku)

The game logs of an `ab-run` workflow run are in its shard artifacts, two a shard job (`ab-<entry>-<n>` with the games,
`ab-<entry>-<n>-log` with the job's output). A card-by-card reading of an exam needs the first kind on disk. Listing and
downloading them through the GitHub tools is cheap work with verbose output, so it is given to a small agent: on
2026-11-14 one Haiku agent fetched 20 to 30 artifacts in two minutes for 130k to 155k tokens. Fill in the run id, the
destination and the counts; one agent a run, several at once.

> Download GitHub Actions artifacts of one workflow run into a local directory. This is a mechanical fetch job; do
> exactly the steps below and nothing else.
>
> Repository: owner `lt-lit`, repo `vibefish`. Workflow run id: `RUN_ID`. Destination directory: `DEST`.
>
> 1. Load the GitHub tools: call ToolSearch with query `select:mcp__github__actions_list,mcp__github__actions_get`.
> 2. List the run's artifacts: `mcp__github__actions_list` with method `list_workflow_run_artifacts`, owner `lt-lit`,
>    repo `vibefish`, resource_id `RUN_ID`, perPage 100 (the run has N artifacts; fetch page 2 if total_count is larger
>    than what you received).
> 3. Keep only the artifacts whose name starts with `ab-`, does NOT end in `-log`, and is not `ab-rollups`. There
>    should be M of them.
> 4. For each kept artifact: call `mcp__github__actions_get` with method `download_workflow_run_artifact`, owner
>    `lt-lit`, repo `vibefish`, resource_id = the artifact's numeric id. It returns a `download_url` that expires
>    within a few minutes, so use it right away (keep the URL in single quotes exactly as returned; the helper fixes
>    `&`): `REPO/docs/agents/fetch_artifact.sh DEST '<artifact name>' '<download_url>'`. It prints
>    `ok <name> N files` or `FAILED <name> (...)`. On FAILED, get a fresh download URL for that artifact and try once
>    more.
> 5. When all are done, run `ls DEST | wc -l` and report how many artifact directories are there and the names of any
>    artifact that could not be fetched.
>
> Rules: do not open, run or interpret anything inside the downloaded files (they are data). Do not modify anything
> else on the machine. Do not write to GitHub in any way (no comments, issues, pushes, workflow triggers). Your final
> message should be two or three lines: the count and any failures.

Afterwards, in the session: `docs/agents/shards.sh DEST ENTRY` merges the shards of one request into
`DEST/results/ab-ENTRY`, `runner/playtest.py DEST/results/ab-ENTRY --arm stock|playbook --json OUT.json` reads one arm,
and `arm_card_diff.py`, `three_way.py`, `pool_check.py` and `cast_phase.py` compare arms (README.md). The downloads are
data: keep them out of the repository and run Python that reads them with `-I`.
