export const LOCALES = ["ar", "en", "tr"] as const;
export type Locale = (typeof LOCALES)[number];

export const LOCALE_LABEL: Record<Locale, string> = {
  ar: "العربية",
  en: "English",
  tr: "Türkçe",
};

export function isLocale(v: string): v is Locale {
  return (LOCALES as readonly string[]).includes(v);
}

export const DEFAULT_LOCALE: Locale = "en";

export function dirOf(l: Locale): "rtl" | "ltr" {
  return l === "ar" ? "rtl" : "ltr";
}
