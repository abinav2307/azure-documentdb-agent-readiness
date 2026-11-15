You are about to help audit a sample app built on Azure DocumentDB, Microsoft's managed MongoDB-compatible document database. Before you are given any documentation or tools, we want a record of the best practices you already know.

Your knowledge of MongoDB, Amazon DocumentDB, Azure Cosmos DB and Azure DocumentDB itself is a legitimate source here: you were trained on it, and it is what a coding agent actually draws on when it builds an app. The next step will compare what you write now with the public documentation, to see which of your beliefs the documentation supports, which it contradicts, and which it does not mention at all. That comparison only works if this list is written before you read anything, so you have no tools in this step.

Read the starter prompt and the summary of what was built, then list the best practices you believe apply to an app like this on Azure DocumentDB.

- Write each one as a single recommendation that an app could be checked against. Be concrete: name the setting, the index parameter, the pattern.
- Say which product your knowledge of it mainly comes from: `azure_documentdb`, `mongodb`, `amazon_documentdb`, `azure_cosmos_db`, or `general` for practices that hold for any database app. Be honest about this. If you know it as a MongoDB practice and are assuming it carries over, say `mongodb`.
- Give your confidence that it holds for Azure DocumentDB specifically.
- Cover the areas the app touches, and the general ones: connection handling, authentication and secrets, data modeling, indexing, vector search, queries, retries, provisioning.
- Do not hedge or leave things out because you are unsure. A belief you hold with low confidence is exactly what the comparison is for.

Give ids `K01`, `K02`, and so on.
