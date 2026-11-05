/**
 * Shared TypeScript SDK public surface.
 *
 * Exports transport and contract types only. Page components, widget internals
 * and any backend implementation detail are deliberately not exported.
 */

export { createClient, QAError } from "./client.js";
export type { Client, ClientOptions, RequestOptions } from "./client.js";
export { subscribeAnswer, subscribeJob, parseSSE } from "./sse.js";
export type { SSECallbacks } from "./sse.js";
export type * from "./types.js";
