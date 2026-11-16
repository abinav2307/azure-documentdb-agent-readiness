You find out what best-practice guidance for Azure DocumentDB a coding agent can actually get hold of from public sources. Azure DocumentDB means Microsoft's managed MongoDB-compatible document database; it is not Amazon DocumentDB and not Azure Cosmos DB for MongoDB (RU).

The Azure DocumentDB product team reads your result to learn two things: what is publicly findable, and how well the public record matches what a model already believes from its training. They hold their own list of the practices they expect, and you have deliberately not been given it: if you were, you would search for each item by name, and that would hide how hard the guidance is to find. So search the way an agent building this app would, not the way someone checking a list would.

## What you are given

- The starter prompt for a sample app, and read-only access to the app that was built from it, so you know which areas matter: connection, authentication, data model, indexing, vector search, queries, provisioning, and so on.
- The installed agent skills, which you can load and read.
- Whatever documentation and MCP tools are available. The list of sources that are reachable in this run is in your instructions; use all of them.
- **Prior beliefs**: best practices a model listed from its own training, before reading any documentation, each with an id (`K01`...) and the product that knowledge mainly comes from. Knowledge of MongoDB, Amazon DocumentDB and Azure Cosmos DB is an applicable source: it is what a coding agent really draws on. Your job is to say how the public record treats each belief.

## What to do

1. Look at the app to see what it uses. Read the main files; do not guess from names.
2. For each area the app touches, search the documentation and load the relevant skills. Use the queries a developer or agent would naturally try ("Azure DocumentDB vector index best practices"), then follow up on what you find.
3. Also look for general guidance that applies to any app on the service: connection handling, security, retries, cost, naming.
4. Record every best practice you find as one entry: a single recommendation, stated so that someone could check an app against it.
5. Then take each prior belief in turn and search for it. Every prior belief must end up in exactly one entry, with one of the last three values of `basis` below.

Do steps 2 to 4 before step 5. Searching for the prior beliefs first would turn open discovery into a search by name.

Each entry has a `basis`:

- `found_in_public_source` - you found it in a public source and it matches no prior belief. Leave `prior_belief_id` and `prior_belief` empty and set `prior_belief_about` to `none`.
- `prior_knowledge_confirmed` - a prior belief, and a public source for Azure DocumentDB says the same. Give the source. If it was already among the practices you found in steps 2 to 4, use that entry and do not add a second one.
- `prior_knowledge_contradicted` - a prior belief, and a public source for Azure DocumentDB says something different. Write what the source says as the `practice`, keep the belief in `prior_belief`, and give the source. These matter most: they are where an agent working from memory builds the wrong thing.
- `prior_knowledge_only` - a prior belief, and you searched and found no public source for Azure DocumentDB that supports or contradicts it. Set `source_kind` to `prior_knowledge`, leave the URL empty, and put the searches you tried in `how_found`.

For the three prior-knowledge values, copy the belief's id, its text and its product into `prior_belief_id`, `prior_belief` and `prior_belief_about`.

For each entry:

- `source_kind`: `public_doc` for a documentation page, `public_repo` for a public repository, `installed_skill` for an agent skill, `local_file` for anything that came from a file on this machine that is not a skill, `prior_knowledge` when there is no source.
- `source_name`: the page title or the skill name.
- `source_url`: the URL, copied exactly from a tool result or from the text of the skill. Never construct or recall a URL. If you do not have one, leave it empty; for installed skills the pipeline fills in the public address itself.
- `how_found`: the search query you ran or the skill you loaded. This shows the product team which paths lead to the guidance.
- `relevant_to_this_app`: whether the app touches the area.

## Rules

- Keep the two kinds of evidence apart. A prior belief counts as confirmed only when a source about Azure DocumentDB says it. A page about MongoDB, Amazon DocumentDB or Azure Cosmos DB that agrees with the belief does not confirm it for this service; that belief stays `prior_knowledge_only`, and you can mention the other page in `how_found`.
- Do not add to the prior beliefs from your own memory in this step. The list was fixed before any documentation was read, and that is what makes the comparison meaningful.
- If a page uses a former product name for this service, it still counts as a source for it; say so in the practice text.
- One recommendation per entry. Do not merge several into one, and do not split one into many.
- If the same practice appears in two sources, record it once and prefer the documentation page.
- List the searches that returned nothing useful in `searches_with_no_useful_result`. An area the app uses with no guidance to be found is itself a finding.
- Be thorough across areas rather than deep in one. Give ids `P01`, `P02`, and so on.
- Keep the result compact. Record at most 30 practices from open discovery, the most relevant to this app first, plus one entry per prior belief. Write `practice` as one sentence and `how_found` as the query or skill name only.
- You are read-only. Change nothing.
