# GitHub and ownership transfer

## Links to share

Repository page:

`https://github.com/ulyssecouliou/IES-Intership-general-repo`

HTTPS clone URL:

`https://github.com/ulyssecouliou/IES-Intership-general-repo.git`

Final handover document after access is granted:

`https://github.com/ulyssecouliou/IES-Intership-general-repo/blob/main/docs/project/HANDOVER_2026-08-28.md`

AI-use disclosure:

`https://github.com/ulyssecouliou/IES-Intership-general-repo/blob/main/docs/project/AI_USAGE_AND_GOVERNANCE.md`

The same URLs remain valid if repository visibility later changes.

## Verified Git state at handover

- Canonical/default branch: `main`.
- Local and remote `main` were synchronised after the final handover commits.
- No local or remote branch contained a commit absent from `main`.
- Worktree and non-ignored untracked-file counts were zero.
- Sixty `.msg` correspondence files were tracked.
- Git object integrity had no missing/corrupt-object error.

Always re-run the verification commands because SHA values change with each
documented handover action.

## Current access state

Anonymous HTTP requests to the repository and Actions page returned `404` on
27 August 2026. The Git remote accepted authenticated pushes, so the repository
exists but is private/access-restricted. The share link works only for accounts
granted access until visibility changes.

## Required owner actions before departure

These actions require GitHub owner/administrator permissions and accountable IES
decisions; they cannot be inferred from source code:

1. identify the IES organisation or employee account that will own the project;
2. add at least two maintainers with suitable permissions;
3. confirm a recovery/backup owner independent of the departing account;
4. transfer the repository to the approved IES organisation if required;
5. set branch protection/rules for `main`;
6. require pull-request review and passing Actions before future merges;
7. enable Actions and verify the final workflow run;
8. choose and commit an approved software licence;
9. decide whether Issues/Discussions/Wiki are enabled and where security reports
   go;
10. decide private versus public visibility only after the data/licensing gate.

## Public-visibility blocker

Do not make the whole repository public merely to share the `.msg` archive. The
repository currently contains tracked SIA standard PDFs, other third-party
documents and no software licence. A public change exposes the complete Git
history, not only current `main`.

Before publication, follow `DATA_EVIDENCE_AND_LICENSING.md`. If legal review
requires removal from history, use a separately reviewed `git filter-repo` or
equivalent migration, preserve a restricted archive, coordinate all clones and
force-push only with explicit owner approval. This is not a routine cleanup.

## Recommended branch rules

For the future IES-owned repository:

- protect `main` from force pushes and deletion;
- require at least one technically competent reviewer;
- require the Python quality workflow;
- dismiss stale approvals after new changes;
- require conversation resolution;
- restrict bypass to a small IES owner group;
- allow tags only from release maintainers;
- use short-lived task branches and delete them after merge.

Do not name a departing individual as the sole `CODEOWNER`. Add a CODEOWNERS file
only after the permanent IES team/usernames are known.

## Actions and CI

The workflow is `.github/workflows/engine-tests.yml`. The final local suite was
green, but the Actions status could not be read from the available unauthorised
GitHub connector/browser. An authenticated owner must open:

`https://github.com/ulyssecouliou/IES-Intership-general-repo/actions`

and record the final run URL/status. If Actions is disabled, enable it under the
repository/organisation policy and re-run the workflow on `main`.

## Repository transfer checklist

Before transferring ownership:

- confirm destination organisation and repository name;
- confirm whether visibility will remain private;
- review GitHub Apps, deploy keys, webhooks, secrets and Actions permissions;
- verify no personal credential is committed;
- verify large files and storage limits;
- retain the handover tag and final SHA;
- notify maintainers that remote URLs may redirect but should be updated;
- test a fresh clone with the new owner account;
- confirm Issues, tags, Actions history and branch rules migrated.

## What to send to a new maintainer

Send:

1. the repository page link;
2. an invitation/collaborator access from the owner;
3. `HANDOVER_2026-08-28.md`;
4. `NEW_MAINTAINER_START_HERE.md`;
5. the handover tag and final commit SHA;
6. the bounded release ZIP and SHA-256 if a file transfer is required;
7. the location of restricted client VE/APS/evidence data not held in Git;
8. names of the IES manager, technical maintainer and SIA contact.

Do not send passwords, tokens or personal-account recovery information.
