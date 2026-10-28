/*
 * The only door to the model. Every call goes through the local Python server
 * (code/server.py), which holds the key, enforces the JSON shape, and writes the
 * call log. If the server is not running the game still plays: scripted fallbacks
 * in story.js answer, and the title screen says the model is offline.
 */

const TIMEOUT = 30000;

async function postJson(url, body) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT);
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

export class AI {
  constructor() {
    this.available = false;
    this.dry = false;
    this.model = null;
  }

  async ping() {
    if (location.protocol === 'file:') {
      // the single-file build has no server behind it
      this.available = false;
      this.standalone = true;
      return false;
    }
    try {
      const res = await fetch('/api/health', { cache: 'no-store' });
      if (!res.ok) { this.available = false; return false; }
      const data = await res.json();
      this.available = !!data.model_ready;
      this.dry = !!data.dry;
      this.model = data.model || null;
      return this.available;
    } catch {
      this.available = false;
      return false;
    }
  }

  // Free speech: the model answers in character and reports which of the listed
  // intents it recognised. The engine decides whether that intent means anything.
  async talk(payload) {
    const data = await postJson('/api/talk', payload);
    if (!data || !data.reply) return null;
    return {
      reply: data.reply,
      intent: data.intent,
      option: data.option,
      hint: data.hint || '',
      ms: data.ms,
      cost: data.cost_yuan,
    };
  }

  // A history that did not happen, clearly labelled as such.
  async chronicle(payload) {
    const data = await postJson('/api/chronicle', payload);
    if (!data || !data.text) return null;
    return { text: data.text, ms: data.ms, cost: data.cost_yuan };
  }
}
