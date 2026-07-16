# Functions to delete in the Zoho UI

> **STATUS 2026-07-16: COMPLETED.** All functions below were deleted in Zoho, and the
> corresponding repo files were removed. WF004 rule was deleted. This file is retained as
> a record of what was removed and why.


This lists **Zoho-side functions** that have no live caller and should be removed from
the org. It is NOT about the repo: every corresponding `.deluge` file is **kept** in the
repo (renamed with the `.ORPHANED.deluge` marker), never deleted. Generated 2026-07-16.

## How to find them in Zoho

Two different places:

- **Standalone functions** (the `_util_*` helpers and other `automation.X()` functions):
  Setup → Developer Space → **Functions**. These do NOT appear in the workflow-function
  list — search by name in the Functions gallery.
- **Workflow-bound functions**: Setup → Automation → Workflow Rules (the function is
  attached to a rule). Deactivate/detach the rule before deleting the function.

## Safe-delete rule

Delete a function only once **no workflow rule and no other function calls it**. The
repo has already been verified to contain no live call (see verification below); this
checklist is for removing the now-unreferenced copies in Zoho.

## Dead standalone helpers (zero callers in v6)

| Function name | Repo file (kept, renamed) | Notes |
|---|---|---|
| `resolveContactAction` | `_util_resolveContactAction.ORPHANED.deluge` | 443 lines. Logic was inlined into `routeContactSequence`. Only the old **v5** function still calls it — safe to delete the v6 standalone copy. |
| `validateQuotesMatchDealProduct` | `_util_validateQuotesMatchDealProduct.ORPHANED.deluge` | Never wired up. Its header comment wrongly claimed `processDeal`/`handleTaskCompletion` called it. |
| `ensureDealQuote` | `ensureDealQuote.ORPHANED.deluge` | Folded into `processDeal`. May have been a former workflow target — check no rule binds it before deleting. |
| `syncConfirmedQuoteToDeal` | `syncConfirmedQuoteToDeal.ORPHANED.deluge` | Folded into `processDeal`. Check no rule binds it. |
| `resolveQuotePlanSummary` | `_util_resolveQuotePlanSummary.ORPHANED.deluge` | Only caller was `syncConfirmedQuoteToDeal` (also dead). |
| `collectLegacyQuoteEvidence` | `_util_collectLegacyQuoteEvidence.ORPHANED.deluge` | Inlined into `normalizeToProductQuoteTuples` (2026-07-16). Republish `normalizeToProductQuoteTuples` before deleting this. |

## WF004 legacy pair — WF004 rule deleted 2026-07-16; DELETE THESE TWO FUNCTIONS

WF004 (`991103000000800001`) was deleted, so `handleCommercialsStatusChange` no longer has
a trigger and the pair is now completely unused. Both repo files are renamed `.ORPHANED`.
**Remaining Zoho action: delete these two functions** (the rule is already gone).

| Function name | Zoho function id | Repo file | Notes |
|---|---|---|---|
| `handleCommercialsStatusChange` | `991103000000780404` | `handleCommercialsStatusChange.ORPHANED.deluge` | Was WF004-bound; rule now deleted. Delete the function. |
| `applyCommercialTransition` | (standalone — find in Functions gallery) | `applyCommercialTransition.ORPHANED.deluge` | Called only by `handleCommercialsStatusChange`. Logic already lives in `routeContactSequence` ("PHANTOM-SCRUBBED"). |

## Remaining Zoho deletions (functions)

1. Delete `handleCommercialsStatusChange`, then `applyCommercialTransition`.
2. Delete the dead standalone helpers in the first table (delete `syncConfirmedQuoteToDeal`
   before `resolveQuotePlanSummary` for a clean "no caller" read). These are standalone
   functions — find them in Setup → Developer Space → Functions; some may never have been
   published, in which case there is nothing to delete.
3. Do NOT publish any `*.ORPHANED.deluge` file.
