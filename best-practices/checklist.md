# Best-practice checklist for gallery samples

This is the team's answer key: the practices you expect a sample to follow.

It is withheld from the first audit step, in which an agent searches public
sources for best practices on its own. The auditor then compares the two:

- on this list and found by the open search: public and discoverable;
- on this list, found only when searched for by name: public but hard to find;
- on this list, not found: not public, or not written down;
- found publicly but not on this list: add it here, or check the public
  guidance says what the team intends.

This starter list is generic on purpose. Replace it with the team's real
guidance. Do not add source links: the point is to see whether an agent can
find the source without being told where it is.

## Connection

- One client is created and reused for the life of the process.
- Connection settings (timeouts, retry options, TLS) follow the service's recommendation for the chosen driver.
- The driver version is pinned and is one the service supports.

## Authentication and secrets

- No password, key or full connection string appears in source, config, tests or README.
- The sample uses the authentication method the prompt asked for; if Microsoft Entra ID is available for the scenario, it is used or the reason for not using it is stated.
- A `.env.example` (or equivalent) lists every required setting with placeholder values.

## Data model

- Document shapes match the access patterns the sample demonstrates.
- Documents cannot grow without bound (no unbounded arrays).
- If the collection is sharded, the shard key choice is explained.

## Indexing and queries

- Every query pattern in the app is served by an index, and no index is unused.
- Vector indexes use a type and parameters that suit the data size, with the embedding dimensions matching the model.
- Full-text or hybrid search uses the service's supported mechanism.
- Aggregation pipelines use only stages and operators the service supports.

## Reliability

- Transient failures are retried in the way the service recommends.
- Bulk loads are batched.

## Provisioning

- Infrastructure is defined as code using the service's own resource type, not a neighbouring service's.
- Tier, storage and region are parameters, with defaults that keep cost low.
- Clean-up steps are provided.

## Sample hygiene

- The README states what the sample shows, prerequisites, setup, run and clean-up steps.
- The sample runs with the commands in the README.
- Tests exist and pass without a live cloud resource, or the README says what they need.
- Dependencies are pinned.
- The sample names the service correctly and does not use a former or neighbouring product name.
