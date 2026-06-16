# FUNCTION_CUTOVER_AND_ROLLBACK.md — V5 Final Corrected

## Cutover Sequence (8 phases)

> No files are deleted until Phase 7.
> No Contact may be automatically moved to Running during migration.

---

## Phase 0: Critical cascade fixes (prerequisite)

**Risk: High — fixes live recursion risk**

| Step | Action |
|------|--------|
| 0.1 | Add `suppressTrigger` to processDeal Account write (L682) |
| 0.2 | Add `suppressTrigger` to processContact Account write (L940) |
| 0.3 | Add `suppressTrigger` to processLead Account write (L1294) |
| 0.4 | Add `suppressTrigger` to processAccount Account write (L710) |

**Verify**: Account edit → processAccount → processDeal → Account update → NO re-trigger.

**Rollback**: Remove suppressTrigger maps.

---

## Phase 1: Opportunity_Stage → Opportunity_Stage migration

**Risk: Medium**

| Step | Action |
|------|--------|
| 1.1 | Replace `Opportunity_Stage` writes → `Opportunity_Stage` in processLead (L510, L1177), processContact (L206, L845), processAccount (L246, L621), processDeal (L593) |
| 1.2 | Replace `Opportunity_Stage` reads → `Opportunity_Stage` in all rollup comparisons |
| 1.3 | Grep v5/: confirm zero `Opportunity_Stage` references |

**Verify**: Lead conversion → Deal.Opportunity_Stage set correctly.

**Rollback**: Revert Opportunity_Stage references from git.

---

## Phase 2: processAccount → thin wrapper

**Risk: Medium**

| Step | Action |
|------|--------|
| 2.1 | Strip processAccount: Account_Key + Deal creation (suppressTrigger) + `processDeal(dealId)` |
| 2.2 | Absorb `_util_deriveOpportunityType` into processDeal |
| 2.3 | Remove Account State rollup from processLead and processContact |
| 2.4 | Remove inline rollup from routeContactSequence (L149-175). Replace with `processDeal(dealId)` when Primary Contact |

**Verify**: Account create → full reconciliation via processDeal. No duplicate rollup.

**Rollback**: Restore files from git.

---

## Phase 3: Centralise activation + migration gate

**Risk: Medium-High**

| Step | Action |
|------|--------|
| 3.1 | Absorb `_util_resolveSequenceRoute` + `createActivationTask` into processContact |
| 3.2 | Update processLead: graph → `processDeal(dealId)` → `processContact(contactId)` |
| 3.3 | Narrow WFC-Contact trigger |
| 3.4 | **Migration dry run**: report of ~400 existing Contacts (Sequence_State, existing activities, sequence history). No bulk activation without approval |

**Verify**: Lead create → processDeal → processContact → Activation Task. No double-fire. No existing Contact auto-activated.

**Rollback**: Restore files + revert WFC-Contact trigger.

---

## Phase 4: Unify transition system

**Risk: High**

### 4a: Expand resolver
- Absorb `_util_resolveContactEntry` into `_util_resolveContactAction`
- Add trigger tokens: demo:*, commercial:*, meeting:*
- Add outputs: supersede, setContactLost, contactLostReason, dealLostReason

### 4b: Absorb helpers into routeContactSequence
- supersedeOldSequence, advancePrimaryContactStage, lossPrimaryContact (with viability check), createStageCall, createStageTask, scheduleSequencedEmail

### 4c: Update handlers
- handleDemoOutcome, handleCommercialsStatusChange, handleMeetingEvent → routeContactSequence with tokens

**Verify**: Full lifecycle. Multi-Contact loss. All-Contact loss → Deal Lost. Single-Contact loss → Deal stays Open.

**Rollback**: Restore all absorbed files + revert handlers.

---

## Phase 5: Consolidate email + new adapters

**Risk: Medium**

| Step | Action |
|------|--------|
| 5.1 | Absorb `_util_buildSendKey`, `_util_sendTemplateToContact`, `_util_resolveTemplate` into sendSequencedEmail |
| 5.2 | Add required 6th argument `existingAuditTaskId` |
| 5.3 | Update sendScheduledEmailFromTask: delegate to sendSequencedEmail |
| 5.4 | Create sendCommercialFollowUp |
| 5.5 | Stop calling sequenceRouter from all code |

**Verify**: One Task per email. Audit-Task guard. Commercial follow-up trigger.

**Rollback**: Restore absorbed files + revert sendSequencedEmail.

---

## Phase 6: Workflow retirement + creation

**Risk: Low**

| Step | Action |
|------|--------|
| 6.1 | Disable WF002 |
| 6.2 | Disable WF003 |
| 6.3 | Disable WF010a, WF010b |
| 6.4 | Create WF010d for sendCommercialFollowUp |
| 6.5 | Rename WF010c |
| 6.6 | Configure WFC-Contact narrowed trigger |

**Rollback**: Re-enable workflows.

---

## Phase 7: Deletion + documentation (after approval)

**Risk: Low**

| Step | Action |
|------|--------|
| 7.1 | Confirm: zero dangling calls |
| 7.2 | Confirm: no Zoho function references |
| 7.3 | Confirm: no workflow bindings |
| 7.4 | Request user approval |
| 7.5 | Delete absorbed/dead files |
| 7.6 | Unpublish orphaned functions (including sequenceRouter) |
| 7.7 | Mark Deal.Sequence_Status, Deal.Next_Action_Due_Date, Deal.Sequence_Paused_Until for CRM field deletion |
| 7.8 | Update all documentation |

**Rollback**: Restore from git.

---

## Go-Live Checklist

- [ ] processDeal is sole rollup owner
- [ ] processContact is sole Activation Task creator
- [ ] routeContactSequence is sole Contact state-transition executor (calls processDeal for rollup)
- [ ] sendSequencedEmail is sole email send owner (6 required args)
- [ ] Every Account write uses suppressTrigger
- [ ] Zero `Opportunity_Stage` writes
- [ ] Contact loss does NOT auto-close Deal
- [ ] One email → one Task
- [ ] Audit-Task guard prevents double-advance
- [ ] Migration dry-run approved
- [ ] All 17 workflows valid
- [ ] WF002, WF003, WF010a, WF010b disabled
