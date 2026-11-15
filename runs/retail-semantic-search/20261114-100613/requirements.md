# Reference requirements: retail semantic search

> Example. Edit this list to say what a publishable version of this sample
> must do. The builder never sees this file. The prompt reviewer predicts
> which lines the starter prompt will miss, and the auditor checks each line
> against what was built and says why any were missed.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The app is a Python Flask app.
- Products are stored in an Azure DocumentDB collection.
- Product titles and descriptions are embedded with `text-embedding-ada-002`.
- Embeddings are stored as BSON binary vectors.
- A `vector-ivf` index exists on the embedding field.
- `/search` takes a natural language query, embeds it, and returns the 10 most similar products.

## What a gallery sample also needs (the starter prompt does not say these)

- The connection string and model credentials come from environment variables; none appear in the repository.
- A `.env.example` lists every setting with placeholder values.
- The vector index dimensions match the embedding model's output.
- The vector index parameters are chosen for the catalog size, and the README says how to change them for a larger one.
- One database client is created and reused across requests.
- A seed script loads sample products and creates the index, and can be run twice without duplicating data.
- `/search` returns a clear error for an empty query and when the embedding call fails.
- Search results include the similarity score.
- Dependencies are pinned in `requirements.txt`.
- Unit tests run without a live cluster.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name.
