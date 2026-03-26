import { describe, expect, it, vi } from "vitest";

import {
  STORAGE_KEY,
  createI18nOptions,
  persistLocale,
  readStoredLocale,
  resolveLocale,
} from "@/lib/i18n";

describe("resolveLocale", () => {
  it("defaults to zh-CN for Chinese browsers", () => {
    expect(resolveLocale("zh-CN", null)).toBe("zh-CN");
  });

  it("falls back to English for non-Chinese browsers", () => {
    expect(resolveLocale("en-US", null)).toBe("en");
  });

  it("prefers a stored locale when it is supported", () => {
    expect(resolveLocale("en-US", "zh-CN")).toBe("zh-CN");
  });
});

describe("storage helpers", () => {
  it("reads a supported locale from storage", () => {
    const getItem = vi.fn(() => "zh-CN");

    expect(readStoredLocale({ getItem })).toBe("zh-CN");
    expect(getItem).toHaveBeenCalledWith(STORAGE_KEY);
  });

  it("persists the selected locale", () => {
    const setItem = vi.fn();

    persistLocale("en", { setItem });

    expect(setItem).toHaveBeenCalledWith(STORAGE_KEY, "en");
  });
});

describe("createI18nOptions", () => {
  it("returns an options object with fallback locale and messages", () => {
    const options = createI18nOptions("zh-CN", null);

    expect(options.locale).toBe("zh-CN");
    expect(options.fallbackLocale).toBe("en");
    expect(options.messages.en.nav.overview).toBe("Overview");
  });
});
