import { SampleError } from './errors.js';
import { BSON } from 'mongodb';
import { SAMPLE_VERSION, DIMENSIONS } from './config.js';

export const ORDER_COUNT = 20_000;
const CATALOG = {
  outdoor: ['Hiking backpack', 'Trail shoes', 'Water bottle', 'Tent', 'Sleeping bag', 'Camp stove', 'Headlamp', 'Rain jacket', 'Walking poles', 'Trail socks'],
  kitchen: ['Coffee grinder', 'Coffee brewer', 'Espresso cups', 'Kitchen scale', 'Chef knife', 'Cutting board', 'Frying pan', 'Spatula', 'Tea kettle', 'Storage jars'],
  fitness: ['Yoga mat', 'Resistance bands', 'Dumbbells', 'Foam roller', 'Gym towel', 'Workout gloves', 'Jump rope', 'Training shoes', 'Sports bottle', 'Exercise ball'],
  office: ['Desk lamp', 'Laptop stand', 'Keyboard', 'Wireless mouse', 'Monitor stand', 'Notebook', 'Desk organizer', 'USB hub', 'Wrist rest', 'Office chair'],
};

/**
 * Build a small readable catalog: four categories, ten items, three variants.
 * Product IDs are stable p0001–p0120, and schema/sample markers permit safe reruns.
 * No external dataset or customer information is used.
 */
export function generateProducts() {
  const products = [];
  for (const [category, names] of Object.entries(CATALOG)) {
    for (const variant of ['Everyday', 'Premium', 'Travel']) {
      for (const name of names) {
        products.push({
          _id: `p${String(products.length + 1).padStart(4, '0')}`,
          title: `${variant} ${name}`, category,
          description: `${name} for ${category} activities. ${variant} version designed for practical use with other ${category} equipment.`,
          schemaVersion: 1, sampleVersion: SAMPLE_VERSION,
        });
      }
    }
  }
  return products;
}

/** Return a seeded pseudo-random generator so retries reproduce identical orders. */
export function seededRandom(seed = 42) {
  let state = seed >>> 0;
  return function nextRandom() {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

/**
 * Yield 20,000 separate orders rather than one unbounded purchase-history array.
 * Baskets contain 3–5 distinct IDs; 80% of item picks favor the anchor category.
 * Co-purchase counts therefore demonstrate complements as well as substitutes.
 * Quantity is retained, but recommendation evidence counts orders, not units.
 */
export function* generateOrders(products = generateProducts(), count = ORDER_COUNT) {
  const random = seededRandom();
  for (let i = 0; i < count; i++) {
    const anchor = products[Math.floor(random() * products.length)];
    const category = products.filter(p => p.category === anchor.category);
    const chosen = new Set([anchor._id]);
    const size = 3 + Math.floor(random() * 3);
    while (chosen.size < size) {
      const pool = random() < 0.8 ? category : products;
      chosen.add(pool[Math.floor(random() * pool.length)]._id);
    }
    yield {
      _id: `order-${String(i + 1).padStart(5, '0')}`,
      schemaVersion: 1, sampleVersion: SAMPLE_VERSION,
      purchasedAt: new Date(Date.UTC(2025, 0, 1) + i * 60_000),
      items: [...chosen].map(productId => ({ productId, quantity: 1 + Math.floor(random() * 2) })),
    };
  }
}

/**
 * Validate provider output as a finite numeric array and L2 normalize it.
 * Store arrays, not BSON binary vectors, and reject dimension/model drift early.
 */
export function normalizeEmbedding(vector, dimensions = DIMENSIONS) {
  if (!Array.isArray(vector) || vector.length !== dimensions || vector.some(n => !Number.isFinite(n))) {
    throw new SampleError('Embedding must be a finite numeric array matching the configured dimensions.');
  }
  const length = Math.hypot(...vector);
  if (!length) throw new SampleError('Embedding cannot be a zero vector.');
  return vector.map(n => n / length);
}

/**
 * Bound ingestion by both operation count and serialized BSON payload.
 * A 1 MiB ceiling and 500 operations are conservative sample defaults, not a
 * measured optimal throughput setting; retain acknowledged ordered writes.
 */
export function* batches(documents, maxCount = 500, maxBytes = 1024 * 1024) {
  let batch = [];
  let bytes = 0;
  for (const document of documents) {
    const size = BSON.calculateObjectSize(document) + 128;
    if (size > maxBytes) throw new SampleError('A sample document exceeds the batch payload limit.');
    if (batch.length && (batch.length === maxCount || bytes + size > maxBytes)) {
      yield batch;
      batch = [];
      bytes = 0;
    }
    batch.push(document);
    bytes += size;
  }
  if (batch.length) yield batch;
}
