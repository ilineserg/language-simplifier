// webapp/src/ws.ts
export type WSOpts = {
  url: string;
  init: object;
  onToken: (s: string) => void;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (e: string) => void;
  maxRetries?: number;
  heartbeatMs?: number;
};

export class WebSocketManager {
  private ws?: WebSocket;
  private retries = 0;
  private closedByClient = false;
  private heartbeatTimer?: number;

  constructor(private opts: WSOpts) {}

  open() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    this.ws = new WebSocket(`${proto}://${location.host}${this.opts.url}`);

    this.ws.onopen = () => {
      this.retries = 0;
      this.closedByClient = false;
      this.ws!.send(JSON.stringify(this.opts.init));
      this.opts.onStart?.();
      // heartbeat
      const hb = this.opts.heartbeatMs ?? 20000;
      this.heartbeatTimer = window.setInterval(() => {
        if (this.ws?.readyState === WebSocket.OPEN) this.ws.send('{"type":"ping"}');
      }, hb);
    };

    this.ws.onmessage = (ev) => {
      try {
        const m = JSON.parse(ev.data);
        if (m.type === "token") this.opts.onToken(m.data || "");
        else if (m.type === "start") this.opts.onStart?.();
        else if (m.type === "end") this.opts.onEnd?.();
        else if (m.type === "error") this.opts.onError?.(m.data || "error");
      } catch {/* ignore */}
    };

    this.ws.onerror = () => this.opts.onError?.("ws_error");

    this.ws.onclose = () => {
      if (this.heartbeatTimer) window.clearInterval(this.heartbeatTimer);
      if (!this.closedByClient) {
        const cap = this.opts.maxRetries ?? 3;
        if (this.retries < cap) {
          const delay = 500 * Math.pow(2, this.retries++); // 0.5s,1s,2s
          setTimeout(() => this.open(), delay);
        }
      }
    };
  }

  stop() {
    this.closedByClient = true;
    if (this.heartbeatTimer) window.clearInterval(this.heartbeatTimer);
    this.ws?.close(1000, "client stop");
  }
}