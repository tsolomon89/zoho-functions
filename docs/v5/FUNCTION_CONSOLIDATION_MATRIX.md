# FUNCTION_CONSOLIDATION_MATRIX.md — V5 Final Corrected

## Summary

```
Before:  38 published functions
After:   24 published functions
Absorbed: 14 functions
Deleted:   1 function (dead code)
New:       1 function (sendCommercialFollowUp)
```

---

## Final 24 Functions

| # | Function | Category | Workflow / Callers |
|---|----------|----------|-------------------|
| 1 | `processLead` | Core entry | WF001 |
| 2 | `processContact` | Core entry | WFC-Contact. Absorbs createActivationTask, _util_resolveSequenceRoute |
| 3 | `processAccount` | Core entry | WFC-Account. Thin → processDeal |
| 4 | `processDeal` | Core entry | WFC-Deal. Sole rollup owner. Absorbs _util_deriveOpportunityType |
| 5 | `handleCallOutcome` | Core entry | WF006 |
| 6 | `handleTaskCompletion` | Core entry | WF008 |
| 7 | `handleDemoOutcome` | Core entry | WF005 |
| 8 | `handleCommercialsStatusChange` | Core entry | WF004 |
| 9 | `handleMeetingEvent` | Core entry | WF007 |
| 10 | `sendScheduledEmailFromTask` | Core entry | WFC-SchedEmail |
| 11 | `sendDemoReminder` | Date adapter | WF010c |
| 12 | `sendCommercialFollowUp` | Date adapter | WF010d (NEW) |
| 13 | `handleEmailReplied` | Email wrapper | WF009a |
| 14 | `handleEmailBounced` | Email wrapper | WF009b |
| 15 | `handleEmailNotReplied` | Email wrapper | WF009c |
| 16 | `handleEmailOpenedNotReplied` | Email wrapper | WF009d |
| 17 | `handleEmailClicked` | Email wrapper | WF009e |
| 18 | `routeContactSequence` | Shared engine | 7 callers. Absorbs 6 functions. Calls processDeal for rollup |
| 19 | `sendSequencedEmail` | Shared engine | 6 callers. Absorbs 3 functions. 6 required args |
| 20 | `handleEmailEvent` | Shared engine | 5 email wrappers |
| 21 | `createAuxTask` | Shared helper | 3 callers |
| 22 | `_util_resolveContactAction` | Infrastructure | 1 caller. 299+ line transition matrix. Absorbs _util_resolveContactEntry |
| 23 | `_util_calculateBusinessDate` | Infrastructure | 2 callers |
| 24 | `_util_logAutomationEvent` | Infrastructure | 20+ callers |

---

## Absorbed (14)

| Function | Lines | → Into |
|----------|-------|--------|
| `sequenceRouter` | 78 | Removed (orphaned) |
| `advancePrimaryContactStage` | 46 | `routeContactSequence` |
| `lossPrimaryContact` | 58 | `routeContactSequence` (multi-Contact viability check) |
| `supersedeOldSequence` | 101 | `routeContactSequence` |
| `createStageCall` | 114 | `routeContactSequence` |
| `createStageTask` | 80 | `routeContactSequence` |
| `scheduleSequencedEmail` | 90 | `routeContactSequence` |
| `createActivationTask` | 115 | `processContact` |
| `_util_resolveContactEntry` | 78 | `_util_resolveContactAction` |
| `_util_deriveOpportunityType` | 23 | `processDeal` |
| `_util_resolveSequenceRoute` | 45 | `processContact` |
| `_util_buildSendKey` | 19 | `sendSequencedEmail` |
| `_util_sendTemplateToContact` | 136 | `sendSequencedEmail` |
| `_util_resolveTemplate` | 62 | `sendSequencedEmail` |

## Deleted (1)

| Function | Reason |
|----------|--------|
| `_util_resolveRoleFromTitle` | 0 callers — dead code |
