---
name: ci-debug
description: Diagnose failing continuous integration runs and flaky pipeline steps
keywords: ci, pipeline, workflow, actions, failing, build, flaky
---
# CI debug

1. Read the failing job log. Find the first error, not the last.
2. Reproduce the step locally with the same interpreter version.
3. Fix the cause. Re-run the whole workflow.
