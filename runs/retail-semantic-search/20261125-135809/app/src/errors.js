/** Mark application-authored errors as safe to show without leaking provider data. */
export class SampleError extends Error {}

/** Hide all raw database/provider errors and stacks, which can contain secrets. */
export function displayError(error) {
  return error instanceof SampleError ? error.message : 'Operation failed. Check database/model permissions, networking and service availability. Raw error details are hidden to protect credentials; rerun ingestion to resume acknowledged batches.';
}
