import { describe, expect, it } from "vitest";

import { parseSseBlock, readChatEvents, type ChatStreamEvent } from "./sse";

function streamOf(...chunks: (string | Uint8Array)[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(typeof chunk === "string" ? encoder.encode(chunk) : chunk);
      }
      controller.close();
    },
  });
}

async function collect(body: ReadableStream<Uint8Array>): Promise<ChatStreamEvent[]> {
  const events: ChatStreamEvent[] = [];
  for await (const event of readChatEvents(body)) {
    events.push(event);
  }
  return events;
}

describe("parseSseBlock", () => {
  it("parses an event with a JSON data line", () => {
    expect(parseSseBlock('event: token\ndata: {"type":"token","text":"Hi"}')).toEqual({
      type: "token",
      text: "Hi",
    });
  });

  it("ignores comments, malformed JSON, and unknown event types", () => {
    expect(parseSseBlock(": keep-alive")).toBeNull();
    expect(parseSseBlock("data: {not json")).toBeNull();
    expect(parseSseBlock('data: {"type":"surprise"}')).toBeNull();
  });
});

describe("readChatEvents", () => {
  it("yields every event in order", async () => {
    const body = streamOf(
      'event: conversation\ndata: {"type":"conversation","conversation_id":"c1"}\n\n',
      'event: token\ndata: {"type":"token","text":"Hello"}\n\n',
      'event: done\ndata: {"type":"done"}\n\n',
    );

    expect((await collect(body)).map((e) => e.type)).toEqual(["conversation", "token", "done"]);
  });

  it("reassembles events split across network chunks", async () => {
    const body = streamOf("event: tok", 'en\ndata: {"type":"tok', 'en","text":"Hi"}\n', "\n");

    expect(await collect(body)).toEqual([{ type: "token", text: "Hi" }]);
  });

  it("decodes multi-byte characters split between chunks", async () => {
    const bytes = new TextEncoder().encode('data: {"type":"token","text":"café"}\n\n');
    const split = bytes.length - 5; // inside the two-byte "é"

    const events = await collect(streamOf(bytes.slice(0, split), bytes.slice(split)));

    expect(events).toEqual([{ type: "token", text: "café" }]);
  });

  it("accepts CRLF line endings and a final event without a trailing blank line", async () => {
    const body = streamOf('data: {"type":"token","text":"a"}\r\n\r\ndata: {"type":"done"}');

    expect((await collect(body)).map((e) => e.type)).toEqual(["token", "done"]);
  });
});
