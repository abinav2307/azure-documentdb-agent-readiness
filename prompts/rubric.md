# Prompt sufficiency rubric

Assess every item, in this order, using exactly these names. The list is fixed
so that verdicts can be compared across the whole gallery.

1. **Goal and scenario** - the business problem, the user, and what the sample demonstrates about the database.
2. **Workflow type** - single-agent, multi-agent, orchestration, or no-agent, and which agent framework if any.
3. **Language and runtime** - language and its version.
4. **Driver and version** - which MongoDB driver or SDK, and which version or version range.
5. **Target service and tier** - Azure DocumentDB cluster tier, storage, region, high availability; or a local instance for development.
6. **Authentication and secrets** - native credentials or Microsoft Entra ID; where secrets live.
7. **Data model** - databases, collections, document shapes, relationships, shard key if any.
8. **Sample data** - source, size, licence, and how it is loaded.
9. **Queries and indexes** - the query patterns, and each index with its type and parameters (including vector and full-text indexes).
10. **AI components** - embedding model and dimensions, chat model, provider, and where they are called.
11. **App surface** - CLI, API or web UI; routes or commands; expected inputs and outputs.
12. **Provisioning and deployment** - CLI, Bicep, Terraform or azd; whether the build may create cloud resources.
13. **Run and test instructions** - the commands, what a successful run looks like, which tests must exist.
14. **Definition of done** - acceptance criteria someone can check.
15. **Constraints and non-goals** - cost limits, things to leave out, licences, compliance.
16. **Repository conventions** - folder layout, README sections, naming, telemetry or attribution requirements.
