import { OpenAI, OpenAIEmbedding } from '@llamaindex/openai';

/**
 * Configure LlamaIndex's OpenAI chat and embedding providers with explicit
 * model identities, dimensions, bounded retries and 60-second API timeouts.
 * Secrets come from config/environment only and are never logged or persisted.
 */
export function createModels(config) {
  const options = { apiKey: config.apiKey, maxRetries: 2, timeout: 60000 };
  return {
    llm: new OpenAI({ ...options, model: config.chatModel, temperature: 0, maxTokens: 2000 }),
    embeddingModel: new OpenAIEmbedding({ ...options, model: config.embeddingModel, dimensions: config.dimensions }),
  };
}
