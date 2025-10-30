// webapp/src/main.ts
import { applyThemeFromTelegram } from "./theme";
import { WebSocketManager } from "./ws";
import { el, setWsStatus, appendOut } from "./ui";

const tg = window.Telegram?.WebApp;

async function verifyInitData(): Promise<boolean> {
  const e = el.ver();
  e.textContent = "checking…"; e.className = "badge";
  const initData = tg?.initData || "";
  const resp = await fetch("/api/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ init_data: initData })
  });
  if (resp.ok) {
    e.textContent = "verified"; e.className = "badge ok";
    return true;
  } else {
    e.textContent = "invalid"; e.className = "badge bad";
    return false;
  }
}

function wireTextareaAutoResize() {
  const ta = el.input();
  const resize = () => {
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, window.innerHeight * 0.5) + "px";
  };
  ta.addEventListener("input", resize);
  resize();
}

let mgr: WebSocketManager | null = null;

function startStream() {
  if (!tg) { alert("Open via Telegram"); return; }
  if (!el.input().value.trim()) { alert("Paste text first"); return; }

  mgr?.stop();
  el.startBtn().disabled = true;
  el.stopBtn().disabled = false;
  setWsStatus("connecting…");

  mgr = new WebSocketManager({
    url: "/ws/adapt",
    init: {
      init_data: tg.initData,
      source_type: "text",
      payload: el.input().value,
      level: el.level().value
    },
    onToken: appendOut,
    onStart: () => setWsStatus("connected"),
    onEnd:   () => appendOut("\n\n— done —"),
    onError: (e) => appendOut(`\n[error] ${e}`),
    maxRetries: 2,
    heartbeatMs: 20000
  });
  mgr.open();
}

function stopStream() {
  mgr?.stop();
  setWsStatus("closed");
  el.startBtn().disabled = false;
  el.stopBtn().disabled = true;
}

function clearOut() {
  el.out().textContent = "";
}

function copyOut() {
  const text = el.out().textContent || "";
  if (!text) return;
  navigator.clipboard?.writeText(text).catch(() => {});
}

async function init() {
  if (!tg) {
    document.body.innerHTML = '<p style="padding:16px">❌ Not inside Telegram WebApp. Open via the bot button.</p>';
    return;
  }
  tg.expand(); tg.ready();
  applyThemeFromTelegram(tg);

  const short = JSON.stringify(
    { query_id: tg.initDataUnsafe?.query_id, user: tg.initDataUnsafe?.user },
    null, 2
  );
  el.idata().textContent = short;

  const ok = await verifyInitData();
  if (!ok) return;

  // Wire UI
  el.startBtn().addEventListener("click", startStream);
  el.stopBtn().addEventListener("click", stopStream);
  el.clearBtn().addEventListener("click", clearOut);
  el.copyBtn().addEventListener("click", copyOut);

  wireTextareaAutoResize();

  // Theme changes from Telegram
  tg.onEvent?.("themeChanged", () => applyThemeFromTelegram(tg));
}

init();