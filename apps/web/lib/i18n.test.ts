import { describe, expect, it } from "vitest";
import { isLocale, translate, TRANSLATIONS } from "@/lib/i18n";

describe("i18n dictionary", () => {
  it("keeps French and English values for every inline key", () => {
    for (const [key, value] of Object.entries(TRANSLATIONS)) {
      expect(value.fr, `${key} is missing fr`).toBeTruthy();
      expect(value.en, `${key} is missing en`).toBeTruthy();
    }
  });

  it("formats parameters and falls back to French then key", () => {
    expect(translate("stream.fallback_polling", "fr", { seconds: 5 })).toBe(
      "Fallback polling - 5s",
    );
    expect(translate("missing.key", "en")).toBe("missing.key");
  });

  it("validates supported locale values", () => {
    expect(isLocale("fr")).toBe(true);
    expect(isLocale("en")).toBe(true);
    expect(isLocale("de")).toBe(false);
  });
});
