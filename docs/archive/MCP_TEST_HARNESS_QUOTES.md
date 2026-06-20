# (Merged) → see `E2E_TEST_HARNESS.md`

The v6 Quote-layer tests have been consolidated into the **complete end-to-end harness**, which exercises the whole pipeline as one continuous workflow (Lead → Deal → sequence → Proposal Preparation → seeded Quote → priced → Confirmed → contract ledger → renewal/upsell):

**`docs/v6/E2E_TEST_HARNESS.md`**

- Phase 3 covers Quote pricing + the contract ledger (Initial / Renewal / Upsold / Renewed & Upsold).
- Phase 4 covers the edge matrix (mixed plan, between-bands, above-band, Cortex, idempotency, Amount handoff, Closed Lost).

This single doc is the canonical place to extend with new coverage (see its **Extension points** section).
