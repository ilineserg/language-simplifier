// webapp/src/ui.ts
export function qs<T extends Element = Element>(sel: string): T {
  const el = document.querySelector(sel);
  if (!el) throw new Error(`Missing element: ${sel}`);
  return el as T;
}

export const el = {
  ver:   () => qs<HTMLDivElement>("#ver"),
  user:  () => qs<HTMLSpanElement>("#user"), // если захочешь добавить
  idata: () => qs<HTMLPreElement>("#idata"),
  level: () => qs<HTMLSelectElement>("#level"),
  input: () => qs<HTMLTextAreaElement>("#input"),
  out:   () => qs<HTMLDivElement>("#out"),
  wsStatus: () => qs<HTMLSpanElement>("#wsStatus"),
  startBtn: () => qs<HTMLButtonElement>("#start"),
  stopBtn:  () => qs<HTMLButtonElement>("#stop"),
  clearBtn: () => qs<HTMLButtonElement>("#clear"),
  copyBtn:  () => qs<HTMLButtonElement>("#copy"),
};

export function setWsStatus(s: string) {
  el.wsStatus().textContent = `WS: ${s}`;
}

let buffer = "";
let rafPending = false;

export function appendOut(s: string) {
  buffer += s;
  if (!rafPending) {
    rafPending = true;
    requestAnimationFrame(() => {
      el.out().textContent += buffer;
      buffer = "";
      rafPending = false;
      const out = el.out();
      out.scrollTop = out.scrollHeight;
    });
  }
}