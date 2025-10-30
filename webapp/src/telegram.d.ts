interface TelegramWebApp {
  initData: string;
  initDataUnsafe?: any;
  colorScheme?: "light" | "dark";
  themeParams?: Record<string, string>;
  expand: () => void;
  ready: () => void;
  onEvent?: (event: "themeChanged", cb: () => void) => void;
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}
export {};