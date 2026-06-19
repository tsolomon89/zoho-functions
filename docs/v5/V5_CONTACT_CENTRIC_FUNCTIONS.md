# V5 Contact-Centric Function Inventory

All functions live in `v5/` and `v5/activity/`. "Owner" = the function the
behaviour belongs to (no transition rules are duplicated; everything routes
through `_util_resolveContactAction`).

## Engine
| Function | Args | Role |
|---|---|---|
| `_util_resolveContactAction` | (stage, seqType, seqState, seqStage, seqStep, trigger) → map | **Single source of truth** for transitions. Pure. |
| `_util_resolveContactEntry` | (stage, seqType, isActivation) → map | Entry action for a Stage by class (cadence/meeting/task). Pure. |
| `_util_deriveOpportunityType` | (oppStage) → string | Opportunity_Stage → MQL/SQL/FTP/RTP. Pure. |
| `_util_resolveTemplate` | (stage, step, kind) → string | (Stage, Step, kind) → one canonical template name. Pure. |
| `_util_resolveSequenceRoute` | (contactId) → string | Recommended activation Sequence_Type (Email/Call/Manual) from source. |
| `_util_buildSendKey` | (contactId, dealId, stage, step, template) → string | Deterministic email send identity. Pure. |
| `sequenceRouter` | (contactId) | Public WF entry: resolve canonical Deal (unique Deal_Key) → `routeContactSequence(…, "resume")`. |
| `routeContactSequence` | (contactId, dealId, trigger) | **Executor**: resolve action, run it (Who=Contact/What=Deal), write Contact fields (suppressed), roll up to Deal if Primary. Blocked-by-Task guard on resume. |

## Email / Call / Task creation
| Function | Args | Role |
|---|---|---|
| `_util_sendTemplateToContact` | (contactId, dealId, template) → messageId | Low-level Send Mail primitive (shared). |
| `sendSequencedEmail` | (contactId, dealId, stage, step, kind) | Immediate send + idempotency + ONE Completed audit Task after success. |
| `scheduleSequencedEmail` | (contactId, dealId, stage, step, kind, dueOffsetDays) | Future-dated wake-up Task for a delayed email. |
| `sendScheduledEmailFromTask` | (taskId) | Fired by WFC-SchedEmail on Due_Date; sends + flips same Task to audit; completes post-call. |
| `createStageCall` | (contactId, dealId, stage, attempt, dueOffsetDays) → callId | Per-Contact Call (dedup by Who+stage+attempt). |
| `createStageTask` | (contactId, dealId, stage) → taskId | Blocking internal Task for Task-class stages. |
| `createAuxTask` | (contactId, dealId, taskType, note) → taskId | Blocking Data Repair / Manual Review / Review Reply Task. |
| `createActivationTask` | (contactId, dealId) → taskId | One Sequence Activation Task for an unactivated Contact. |
| `sendDemoReminder` | (dealId) | WFC-DemoReminder: Demo Confirmation Reminder to Primary Contact. |

## Handlers (activity outcomes → Contact transitions)
| Function | Source record | Role |
|---|---|---|
| `handleCallOutcome` | Call (Who=Contact, What=Deal) | Map Call_Outcome → trigger → `routeContactSequence`; deferral reschedule; aux Tasks; Lost reason. |
| `handleTaskCompletion` | Task | **Audit guard** (Email Sent) + **scheduled-send guard**; activation mapping; task-class completion; resume on Data Repair/Review Reply/Enrichment. |
| `handleMeetingEvent` | Event (What=Deal) | Mirror demo fields to Deal + reminder; Confirmation email on first link; Cancelled/No-Show recovery. |
| `handleDemoOutcome` | Deal-driven (Primary Contact) | Advance Primary Contact via `advancePrimaryContactStage`; demo emails; loss. |
| `handleCommercialsStatusChange` | Deal-driven (Primary Contact) | Sent→Commercial Agreement; Signed→Onboarding; Rejected→loss; commercial data stays on Deal. |
| `handleEmailEvent` (+ wrappers) | Email event | Reply→Review Reply Task; Bounce→Data Repair Task; no Paused, no Deal sequence writes. |
| `advancePrimaryContactStage` | (dealId, newStage) → contactId | Supersede + advance Primary Contact + route. |
| `lossPrimaryContact` | (dealId, contactReason, dealReason) | Terminal commercial loss: Contact + Deal Lost. |
| `supersedeOldSequence` | (contactId, dealId) | Cancel one Contact's stale Calls/scheduled Tasks; defer blocking Tasks. |

## Orchestrators
| Function | Sequence change |
|---|---|
| `processLead` | Creates Activation Task for the Primary Contact; **no auto-start**; no Deal sequence bootstrap. |
| `processContact` | Ensures unactivated Contact has an Activation Task (`createActivationTask` dedups); no Deal sequence bootstrap; never restarts an active sequence. |
| `processAccount` | No `sequenceRouter` call, no Deal sequence bootstrap. |
| `processDeal` | No `sequenceRouter` call, no Deal sequence bootstrap; commercial/contract data + Primary Contact rollup only. |

> Flagged remaining polish in the orchestrators (needs live field confirmation):
> replace Deal `Opportunity_Stage` writes with `Opportunity_Stage`, and migrate stage-value
> comparisons from "Marketing Qualification" to "Marketing Consent" (keeping the
> `*_Marketing_Qualification_Completed_At` field API names). The Deal pipeline
> rollup is already written as `Opportunity_Stage` by `routeContactSequence`.
