import { createI18n } from "vue-i18n";

import { enMessages } from "@/locales/en";
import { zhCnMessages } from "@/locales/zh-CN";

export const STORAGE_KEY = "gobot.locale";
export const supportedLocales = ["en", "zh-CN"] as const;

export type AppLocale = (typeof supportedLocales)[number];

const messages = {
  en: enMessages,
  "zh-CN": zhCnMessages,
} as const;

function isSupportedLocale(value: string | null | undefined): value is AppLocale {
  return supportedLocales.includes(value as AppLocale);
}

export function resolveLocale(browserLanguage?: string, storedLocale?: string | null): AppLocale {
  if (isSupportedLocale(storedLocale)) {
    return storedLocale;
  }

  if (browserLanguage?.toLowerCase().startsWith("zh")) {
    return "zh-CN";
  }

  return "en";
}

export function readStoredLocale(storage?: Pick<Storage, "getItem">): AppLocale | null {
  if (!storage) {
    return null;
  }

  try {
    const locale = storage.getItem(STORAGE_KEY);
    return isSupportedLocale(locale) ? locale : null;
  } catch {
    return null;
  }
}

export function persistLocale(locale: AppLocale, storage?: Pick<Storage, "setItem">): void {
  if (!storage) {
    return;
  }

  try {
    storage.setItem(STORAGE_KEY, locale);
  } catch {
    // Ignore storage failures so locale switching still works in memory.
  }
}

export function createI18nOptions(browserLanguage?: string, storedLocale?: string | null) {
  const locale = resolveLocale(browserLanguage, storedLocale);

  return {
    legacy: false,
    locale,
    fallbackLocale: "en" as const,
    messages,
  };
}

export function createAppI18n() {
  const browserLanguage = typeof navigator === "undefined" ? undefined : navigator.language;
  const storedLocale =
    typeof window === "undefined" ? null : readStoredLocale(window.localStorage);

  return createI18n(createI18nOptions(browserLanguage, storedLocale));
}
