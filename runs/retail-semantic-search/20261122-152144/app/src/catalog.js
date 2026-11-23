const themes = [
  ['camping', ['Tent', 'Sleeping bag', 'Camp stove', 'Lantern', 'Camp chair', 'Cook set', 'Water filter', 'Hiking pack', 'Ground mat', 'Dry bag']],
  ['coffee', ['Coffee grinder', 'Pour-over brewer', 'Kettle', 'Coffee beans', 'Coffee scale', 'Travel mug', 'Filter papers', 'Milk pitcher', 'Espresso cup', 'Coffee storage jar']],
  ['fitness', ['Yoga mat', 'Resistance bands', 'Foam roller', 'Water bottle', 'Training shoes', 'Gym bag', 'Jump rope', 'Exercise towel', 'Dumbbell set', 'Workout gloves']],
  ['office', ['Desk lamp', 'Keyboard', 'Mouse', 'Laptop stand', 'Desk mat', 'Notebook', 'Pen set', 'Monitor arm', 'Cable organizer', 'Headset']],
  ['cooking', ['Chef knife', 'Cutting board', 'Frying pan', 'Spatula', 'Mixing bowl', 'Measuring cups', 'Kitchen scale', 'Apron', 'Baking tray', 'Oven mitts']],
  ['cycling', ['Bike helmet', 'Bike lights', 'Tire pump', 'Repair kit', 'Cycling gloves', 'Bike lock', 'Saddle bag', 'Bottle cage', 'Chain lubricant', 'Reflective vest']],
];

/**
 * Build a small versioned catalog with stable sample IDs, meaningful titles
 * and six categories. Only these 60 products need paid embedding calls, not
 * the 20,000 orders. IDs are independent of database-generated ObjectIds.
 */
export function createCatalog() {
  return themes.flatMap(([category, names], group) => names.map((title, index) => ({
    _id: `sample-p${String(group * 10 + index + 1).padStart(3, '0')}`,
    title,
    category,
    description: `${title} for everyday ${category} activities. Durable, practical equipment for a coordinated ${category} kit.`,
    schemaVersion: 1,
  })));
}

/**
 * Yield exactly 20,000 deterministic synthetic transactions with 2–4 distinct
 * products per basket. An integer PRNG creates strong within-category bundles
 * and occasional cross-category items. The seed and timestamps never change,
 * so batched upserts are resumable and do not duplicate orders on reruns.
 */
export function* createOrders(catalog = createCatalog(), count = 20000) {
  let state = 42;
  // Advance a fixed-seed integer PRNG without using global Math.random state.
  function randomInt(max) {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return Math.floor((state / 4294967296) * max);
  }
  for (let i = 0; i < count; i++) {
    const group = randomInt(6);
    const ids = new Set();
    const size = 2 + randomInt(3);
    while (ids.size < size) {
      const index = randomInt(10) + (randomInt(10) === 0 ? randomInt(6) : group) * 10;
      ids.add(catalog[index]._id);
    }
    yield {
      _id: `sample-o${String(i + 1).padStart(5, '0')}`,
      schemaVersion: 1,
      purchasedAt: new Date(Date.UTC(2025, 0, 1) + i * 60000),
      items: [...ids].map(productId => ({ productId, quantity: 1 })),
    };
  }
}
