# StepFree

StepFree is an evidence-bound accessibility route certification protocol on GenLayer Studio Next. It evaluates a specific ordered route against a traveler's stated needs using a venue profile and a separate independent survey.

## Why decentralized judgment matters

Accessibility is contextual: a building can advertise accessibility while one lift outage, narrow doorway, unusable restroom, or unsupported evacuation plan breaks the actual journey. StepFree asks validators to inspect complete frozen source bodies, bind every conclusion to quotes from both authorities, and agree on five fixed criteria. The independent survey controls when sources conflict.

The contract keeps the route gate **BLOCKED** until an appointed independent assessor certifies a PASSABLE or ASSISTED result. Anyone except the owner or assessor can submit new counter-evidence; doing so immediately revokes the certificate and blocks the route pending consensus. Upheld challenges force a revision while preserving the prior snapshots.

## Contract flow

1. `create_route` binds traveler needs, 2–8 ordered waypoints, two distinct-authority sources, and a separate assessor.
2. `freeze_route` retrieves complete documents through strict equivalence, stores their bodies, SHA-256 receipts, and a route snapshot digest.
3. `assess_route` produces all five ordered criteria with quotes from both sources; validators independently compare the meaningful outcome.
4. `certify_route` is restricted to the appointed assessor.
5. `challenge_route` accepts independent counter-evidence and immediately blocks the gate.
6. `resolve_challenge` binds its ruling to an exact counter-evidence quote.
7. `revise_route` is owner-only, requires a new independent survey, and preserves snapshot history.

## Local verification

```text
pytest -q
genvm-lint contracts/stepfree.py
cd frontend
npm test
npm run build
```

## Deployment

- Network: GenLayer Studio Next
- Chain ID: `61997`
- RPC: `https://studio-next.genlayer.com/api`
- Contract address and successful live transaction receipts are recorded in `deployment.json` after deployment.

Copy `frontend/.env.example` to `frontend/.env`, set `VITE_CONTRACT_ADDRESS`, then run the frontend. The interface is a route atlas: it reads public certificates without a wallet and opens GenLayer's transaction panel for writes.

## Safety boundaries

StepFree is an advisory evidence protocol, not a substitute for an on-site access check, emergency plan, or professional accessibility assessment. Missing or conflicting evidence fails safely to BLOCKED.
