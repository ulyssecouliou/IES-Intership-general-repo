# Final transmission checklist — 28 August 2026

Use this as the sign-off sheet between the departing contributor, IES manager
and incoming maintainer.

## Completed in the repository

- [x] Canonical branch is `main`.
- [x] Development branch history is fully contained in `main`.
- [x] Local and `origin/main` synchronisation was verified after push.
- [x] Worktree has no modified or non-ignored untracked file.
- [x] Final handover is linked from the root README and project index.
- [x] Client SIA 380/2 and SIA 4010 scopes/claims are separated.
- [x] Known per-test SIA 4010 blockers are documented.
- [x] AI use, limits and governance are documented.
- [x] Architecture/runtime responsibilities are documented.
- [x] Data/evidence/privacy/licensing risks are documented.
- [x] Testing/release/operations are documented.
- [x] GitHub ownership/publication steps are documented.
- [x] Sixty Outlook messages are versioned for continuity.
- [x] Ten VE/client-test and SIA 4010 disposable-project snapshots are versioned
  with SHA-256 checksums for workstation-independent continuation.
- [x] Temporary/dependency/Office-lock files are ignored.
- [x] Full configured Python suite passed with private datasets present (three
  optional skips).
- [x] Black, Flake8 and selected strict MyPy gates passed.
- [x] Git integrity check found no corruption.

## Generated at final transmission

- [x] Final four-language HTML documentation build completed for `en`, `fr`,
  `de` and `it`; each build succeeded with the documented legacy API warnings.
- [x] `scripts/quality/validate_release.py` completed: 313 checks passed and
  eight non-blocking warnings were retained in the final receipt.
- [x] Final bounded MVP ZIP built under `outputs/release/`; its SHA-256 sidecar
  is generated after the final commit.
- [x] Annotated Git handover tag `handover-2026-08-28-complete-v2` is created and
  pushed by the final workflow; earlier checkpoint tags are preserved.
- [x] Final `main` SHA is the commit referenced by that annotated tag.

See `FINAL_TRANSMISSION_RECEIPT_2026-08-28.md` for the exact results and limits.

## Requires IES owner/manager action

- [ ] Confirm permanent repository owner/IES organisation.
- [ ] Add at least two incoming maintainers.
- [ ] Transfer repository ownership if it must not remain under the departing
  personal account.
- [ ] Decide and commit the software licence.
- [ ] Review rights for all tracked SIA/ISO/IES/third-party documents.
- [ ] Review privacy/public retention of the `.msg` archive.
- [ ] Decide whether a complete Git-history purge is required before publicity.
- [ ] Configure branch protection and required Actions checks.
- [ ] Open the final authenticated GitHub Actions run and record its URL/status.
- [ ] Decide and apply repository visibility; it was private at final audit.
- [ ] Define security-reporting and incident contacts.
- [ ] Confirm where restricted client VE/APS/evidence/model data will be retained.

## Requires IESVE workstation action

- [ ] Open a known disposable/reference VE project in IESVE 2025.
- [ ] Run the client launcher and complete the release smoke test.
- [ ] Generate/open final PDF and XLSX; inspect layout and claims.
- [ ] Verify four-language switching in the actual VE UI.
- [ ] Confirm no customer model is used for disposable accreditation tests.
- [ ] Archive the final VE-generated receipts/reports in approved project storage.

## Requires SIA/authority or specialist response

- [ ] Resolve Test 1E external-shade solar reflectance `0.490` and visible
  reflectance `0.496` mapping/persistence in VE/APcdb, plus remaining optical and
  APS-equivalence questions.
- [ ] Finalise Test 2A native profile/optical equivalence.
- [ ] Resolve exact source bindings and room-system read-back for Tests 3–7.
- [ ] Complete exact disposable models, simulations and official comparisons.
- [ ] Obtain independent/authority acceptance; do not label diagnostic output as
  official SIA validation.

## Restricted data handoff

For each non-Git dataset, record owner, approved location, access recipient and
retention policy. Do not write credentials in this document.

| Dataset | Approved location | New owner | Confirmed |
|---|---|---|---|
| Client VE project(s) | To be supplied by IES | To be assigned | [ ] |
| APS/Vista results | To be supplied by IES | To be assigned | [ ] |
| Reviewer evidence packs | To be supplied by IES | To be assigned | [ ] |
| Licensed source originals | IES-controlled source location | To be assigned | [ ] |
| Final reports/presentations | IES project storage | To be assigned | [ ] |

## Sign-off record

| Role | Name | Date | Confirmation |
|---|---|---|---|
| Departing contributor | Ulysse Couliou | 2026-08-28 | [ ] |
| IES manager |  |  | [ ] |
| Incoming technical maintainer |  |  | [ ] |
| Data/licensing owner |  |  | [ ] |

Signing this checklist confirms receipt and known limitations; it does not
assert SIA certification or completion of the seven official validation tests.
