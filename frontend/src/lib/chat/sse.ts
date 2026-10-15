import type { components } from "@/lib/api/schema";

type Schemas = components["schemas"];

/** One `data:` payload from `POST /api/chat` (SPEC section 7.2). Generated from the backend schema. */
export type ChatStreamEvent =
  | Schemas["ConversationEvent"]
  | Schemas["FlagEvent"]
  | Schemas["TokenEvent"]
  | Schemas["LeadCapturedEvent"]
  | Schemas["ErrorEvent"]
  | Schemas["DoneEvent"];

const KNOWN_TYPES = new Set<ChatStreamEvent["type"]>([
  "conversation",
  "flag",
  "token",
  "lead_captured",
  "error",
  "done",
]);

function isChatStreamEvent(value: unknown): value is ChatStreamEvent {
  return (
    typeof value === "object" &&
    value !== null &&
    "type" in value &&
    KNOWN_TYPES.has((value as { type: ChatStreamEvent["type"] }).type)
  );
}

/** Parse one SSE block (lines separated by `\n`). Returns null for comments and unknown events. */
export function parseSseBlock(block: string): ChatStreamEvent | null {
  const data = block
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).replace(/^ /, ""))
    .join("\n");
  if (!data) {
    return null;
  }
  try {
    const parsed: unknown = JSON.parse(data);
    return isChatStreamEvent(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

/**
 * Turn a `text/event-stream` body into typed events. Network chunks may split anywhere, including
 * inside a line or a multi-byte character, so text is decoded in streaming mode and buffered until
 * a blank line ends each event.
 */
export async function* readChatEvents(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<ChatStreamEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        buffer += decoder.decode();
        break;
      }
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n?/g, "\n");
      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        const event = parseSseBlock(buffer.slice(0, boundary));
        buffer = buffer.slice(boundary + 2);
        if (event) {
          yield event;
        }
        boundary = buffer.indexOf("\n\n");
      }
    }
    const trailing = parseSseBlock(buffer.trim());
    if (trailing) {
      yield trailing;
    }
  } finally {
    reader.releaseLock();
  }
}
