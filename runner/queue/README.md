# runner/queue

Run requests for the Actions workflows, so a run can be started by a commit instead of a click. A push to `testing`
that changes `ab-run.json` starts `ab-run.yml` with the file's fields as its inputs (the same names and defaults as
the Run workflow form; a new `requested` value is enough to run the same request again). Runs on the branch queue
behind each other, and promoting `testing` to `main` starts nothing. `note` says what the run is for and is ignored
by the workflow. The last request stays in the file as the record of what was asked for.
