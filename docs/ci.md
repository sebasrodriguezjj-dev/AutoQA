# GitHub Actions integration

`autoqa integrate --provider github --project projects/NAME` writes `.github/workflows/autoqa-NAME.yml` in the current QA repository. It requires a generated suite and root `pyproject.toml` plus `uv.lock`, validates a repository-relative project path and refuses to overwrite an existing workflow. It never commits or pushes. The QA repository can be separate from application source.

Official latest stable releases and their tag commits were resolved through GitHub's REST API on November 17, 2026. Exact pins and tags are recorded in `action-revisions.json`; the generator contains these immutable commits. The workflow has manual and pull-request triggers, read-only contents permission, `persist-credentials: false`, locked uv installation, Chromium OS/browser installation, real tests, always-attempted reporting and artifact upload. Failed tests fail the job.

Before enabling:

1. Review generated Python tests and approved expectations.
2. Include the AutoQA package, pyproject.toml, uv.lock and the selected project's config, discovery workflow map, test matrix and automation files in the private QA repository. `projects/` is ignored deliberately: add only reviewed files explicitly with `git add -f` or relocate the project and adjust ignores. Never broadly force-add private evidence or credentials.
3. Configure the repository Actions variable `AUTOQA_BASE_URL` to the authorized staging origin. Update the project's `allowed_domains` to that exact staging hostname. Target paths must correspond to the observed paths. Set `allow_localhost: false` for public staging jobs.
4. Keep staging secrets out of this version's pull-request workflow. Advanced authentication is unsupported. For future authenticated workflows, use protected environments, manual approvals and separate trusted-branch jobs; do not expose credentials to fork PRs.
5. Review artifact contents and seven-day retention. The generated upload contains reports and run evidence, which can contain application data.

The workflow does not start or deploy the application. A runner must be able to reach the authorized target. A localhost demo needs a separate server startup/readiness step on the same runner. Generated workflows were parsed and inspected locally, but not executed on GitHub; no remote CI success is claimed.
