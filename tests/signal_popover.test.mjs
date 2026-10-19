import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {runInNewContext} from "node:vm";
import test from "node:test";

const source = readFileSync(new URL("../assets/app.js", import.meta.url), "utf8").replace(/\nboot\(\);\s*$/, "");
const rect = (left, top, width, height) => ({left, top, width, height, right: left + width, bottom: top + height});

function app() {
  const timers = new Map(), frames = new Map();
  let next = 0, created = 0, panel;
  const card = {getBoundingClientRect: () => rect(280, 70, 460, 630)};
  const body = {getBoundingClientRect: () => rect(280, 120, 460, 530)};
  const footer = {getBoundingClientRect: () => rect(280, 650, 460, 50)};
  const buttons = [];
  const overlay = {
    querySelector: selector => ({".mineral-card": card, ".mineral-card-body": body, ".mineral-source": footer,
      ".mineral-signal-popover": panel}[selector] || (selector.endsWith("-content") ? {innerHTML: "Signal content"} : null)),
    querySelectorAll: () => buttons,
    insertAdjacentHTML() {
      created++;
      panel = {style: {}, isConnected: true, contains: target => target === panel,
        getBoundingClientRect() {return rect(parseFloat(this.style.left) || 0, parseFloat(this.style.top) || 0,
          Math.min(190, parseFloat(this.style.maxWidth) || 190), Math.min(140, parseFloat(this.style.maxHeight) || 140));},
        remove() {this.isConnected = false;},
      };
    },
  };
  for (const [id, left, top] of [["a", 682, 180], ["b", 332, 230]]) {
    const attrs = new Map([["aria-controls", id], ["aria-expanded", "false"], ["aria-pressed", "false"]]);
    const button = {attrs, isConnected: true, hover: false, rect: rect(left, top, 38, 24),
      getAttribute: name => attrs.get(name), setAttribute: (name, value) => attrs.set(name, value),
      closest: () => overlay, matches() {return this.hover;}, contains(target) {return target === this;},
      getClientRects() {return this.isConnected ? [this.rect] : [];},
      getBoundingClientRect() {return this.rect;}, focus() {this.focused = true;},
    };
    buttons.push(button);
  }
  const window = {innerWidth: 1000, innerHeight: 800,
    requestAnimationFrame: callback => {frames.set(++next, callback); return next;},
    cancelAnimationFrame: id => frames.delete(id),
  };
  const context = {document: {querySelector: () => null, querySelectorAll: () => []}, window,
    setTimeout: callback => {timers.set(++next, callback); return next;}, clearTimeout: id => timers.delete(id)};
  runInNewContext(`${source}\nglobalThis.api = {showLocationSignals, closeLocationSignals, deferCloseLocationSignals,
    updateLocationSignalPosition, renderLocationSignals, getSignal: () => mineralSignal};`, context);
  const flush = callbacks => {for (const [id, callback] of [...callbacks]) {callbacks.delete(id); callback();}};
  return {...context.api, buttons, window, timers, frames, created: () => created,
    flushTimers: () => flush(timers), flushFrames: () => flush(frames)};
}

test("hover preview promotes to a persistent click without replacing its panel", () => {
  const api = app(), [a, b] = api.buttons;
  api.showLocationSignals(a);
  const panel = api.getSignal().panel;
  assert.equal(a.attrs.get("aria-pressed"), "false");
  api.showLocationSignals(a, "click");
  assert.equal(api.getSignal().panel, panel);
  assert.equal(api.created(), 1);
  assert.equal(api.getSignal().pinned, true);
  assert.equal(a.attrs.get("aria-pressed"), "true");
  api.showLocationSignals(b);
  api.showLocationSignals(a);
  assert.equal(api.getSignal().button, a);
  assert.equal(api.getSignal().mode, "click");
  api.deferCloseLocationSignals(null);
  api.flushTimers();
  assert.equal(api.getSignal().panel, panel);
});

test("explicit activation switches the one pinned panel and clears the previous control", () => {
  const api = app(), [a, b] = api.buttons;
  api.showLocationSignals(a, "click");
  const old = api.getSignal().panel;
  api.showLocationSignals(b, "touch");
  assert.equal(old.isConnected, false);
  assert.equal(a.attrs.get("aria-expanded"), "false");
  assert.equal(a.attrs.get("aria-pressed"), "false");
  assert.equal(b.attrs.get("aria-pressed"), "true");
  assert.equal(api.getSignal().button, b);
  assert.equal(api.getSignal().mode, "touch");
});

test("pinning cancels pending hover dismissal and closing cancels pending positioning", () => {
  const api = app(), [a] = api.buttons;
  api.showLocationSignals(a);
  api.deferCloseLocationSignals(null);
  assert.equal(api.timers.size, 1);
  api.showLocationSignals(a, "keyboard");
  assert.equal(api.timers.size, 0);
  api.updateLocationSignalPosition();
  api.updateLocationSignalPosition();
  assert.equal(api.frames.size, 1);
  api.closeLocationSignals(true);
  api.flushTimers(); api.flushFrames();
  assert.equal(api.getSignal(), null);
  assert.equal(api.frames.size, 0);
  assert.equal(a.focused, true);
  assert.equal(a.attrs.get("aria-pressed"), "false");
});

test("dismissed hovered triggers cannot immediately reopen, but explicit clicks still work", () => {
  const api = app(), [a] = api.buttons;
  a.hover = true;
  api.showLocationSignals(a, "click");
  api.closeLocationSignals();
  api.showLocationSignals(a);
  assert.equal(api.getSignal(), null);
  api.showLocationSignals(a, "click");
  assert.equal(api.getSignal().pinned, true);
});

test("scrolling repositions the mounted pinned panel and closes an out-of-view anchor", () => {
  const api = app(), [a] = api.buttons;
  api.showLocationSignals(a, "click");
  const panel = api.getSignal().panel, before = parseFloat(panel.style.top);
  a.rect = rect(682, 140, 38, 24);
  api.updateLocationSignalPosition(); api.flushFrames();
  assert.equal(api.getSignal().panel, panel);
  assert.equal(parseFloat(panel.style.top), before - 40);
  assert.equal(a.attrs.get("aria-pressed"), "true");
  a.rect = rect(682, 110, 38, 24);
  api.updateLocationSignalPosition(); api.flushFrames();
  assert.equal(api.getSignal().panel, panel);
  a.rect = rect(682, 80, 38, 24);
  api.updateLocationSignalPosition(); api.flushFrames();
  assert.equal(api.getSignal(), null);
  assert.equal(panel.isConnected, false);
});

test("transient previews still close on scrolling and detached anchors cannot leave stale panels", () => {
  const api = app(), [a] = api.buttons;
  api.showLocationSignals(a);
  api.updateLocationSignalPosition();
  assert.equal(api.getSignal(), null);
  api.showLocationSignals(a, "click");
  a.isConnected = false;
  api.updateLocationSignalPosition(); api.flushFrames();
  assert.equal(api.getSignal(), null);
});

test("signal triggers expose their toggle state without changing content or values", () => {
  const api = app();
  const location = {en: "Area", signals: [{mode: "ship", primaryMaterial: "Copper", values: [4240]}]};
  const before = JSON.stringify(location);
  const html = api.renderLocationSignals(location, "Copper", 0);
  assert.match(html.button, /aria-expanded="false" aria-pressed="false"/);
  assert.match(html.button, /title="点击固定信号"/);
  assert.match(html.panel, />4,240<\/b>/);
  assert.equal(JSON.stringify(location), before);
});
