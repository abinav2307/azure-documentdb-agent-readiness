export class SessionMemory {
  /**
   * Keep bounded process-local memory, not customer history in the database.
   * At most 100 sessions and ten completed turns per session are retained.
   * Restarting the process clears memory. Each session has its own arrays.
   */
  constructor(maxSessions = 100, maxTurns = 10) {
    this.sessions = new Map();
    this.maxSessions = maxSessions;
    this.maxTurns = maxTurns;
  }

  /** Read or create a session, refreshing its insertion order for LRU eviction. */
  get(sessionId) {
    if (!/^[a-zA-Z0-9_-]{1,64}$/.test(sessionId)) throw new Error('Session ID must be 1–64 letters, digits, underscores or hyphens.');
    const session = this.sessions.get(sessionId) || { turns: [] };
    this.sessions.delete(sessionId);
    this.sessions.set(sessionId, session);
    if (this.sessions.size > this.maxSessions) this.sessions.delete(this.sessions.keys().next().value);
    return session;
  }

  /** Serialize only completed user/assistant turns as LlamaIndex chatHistory. */
  history(sessionId) {
    return this.get(sessionId).turns.flatMap(turn => [
      { role: 'user', content: `Recommend items for ${turn.productId}.` },
      { role: 'assistant', content: JSON.stringify(turn.response) },
    ]);
  }

  /**
   * Commit memory only after validated recommendations succeed. Store the
   * input product's category as an implicit interest (not an explicit purchase
   * or dislike), so future rankings can favor recent session interests.
   */
  remember(sessionId, product, response) {
    const session = this.get(sessionId);
    session.turns.push({ productId: product._id, category: product.category, response });
    session.turns = session.turns.slice(-this.maxTurns);
  }
}
