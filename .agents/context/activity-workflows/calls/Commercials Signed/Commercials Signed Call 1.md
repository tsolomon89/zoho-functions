# Commercials Signed Call 1 — Onboarding Kickoff & Success Handoff

## Objective
Celebrate the signed agreement, introduce the customer success/onboarding manager, verify details for kickoff, and schedule the kickoff session.

## Call Script

### Opening (Warm & Celebratory)
"Hi `${Contacts.First_Name}`, this is `${User.First_Name}` calling from Jurnii. I'm absolutely thrilled to welcome you and `${Contacts.Account_Name}` to the Jurnii platform!"

*(Wait for response)*

"We received the signed agreement today, so everything is fully official. I wanted to reach out to outline our immediate next steps and coordinate the kickoff. 

I’d like to introduce you to `${User.First_Name}` (or our Onboarding lead), who will guide you through the setup. Do you have a quick 5 minutes early next week for our kickoff meeting?"

### Gathering Kickoff Info
"To prepare:
- Who on your technical team will oversee the CRM installation?
- And are there any specific security or data guidelines we should have ready?"

## Call Outcomes
- **Positive**: Kickoff meeting scheduled. Set `Stage1` = `Onboarding` / create kickoff Task.
- **Neutral**: Agreement signed, but team is busy to book kickoff immediately. Send `Commercials Signed Email 1`.
- **No Answer**: Voicemail left. Send `Commercials Signed Email 1`.
- **Negative**: N/A (contract is signed, but if they request delay, set Deferred).
