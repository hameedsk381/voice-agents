export interface Language {
    code: string;
    name: string;
    nativeName: string;
    sttSupported: boolean;
}

export const LANGUAGES: Language[] = [
    { code: "hi", name: "Hindi", nativeName: "हिन्दी", sttSupported: true },
    { code: "ta", name: "Tamil", nativeName: "தமிழ்", sttSupported: true },
    { code: "te", name: "Telugu", nativeName: "తెలుగు", sttSupported: true },
    { code: "bn", name: "Bengali", nativeName: "বাংলা", sttSupported: true },
    { code: "mr", name: "Marathi", nativeName: "मराठी", sttSupported: true },
    { code: "gu", name: "Gujarati", nativeName: "ગુજરાતી", sttSupported: true },
    { code: "kn", name: "Kannada", nativeName: "ಕನ್ನಡ", sttSupported: true },
    { code: "ml", name: "Malayalam", nativeName: "മലയാളം", sttSupported: true },
    { code: "pa", name: "Punjabi", nativeName: "ਪੰਜਾਬੀ", sttSupported: true },
    { code: "or", name: "Odia", nativeName: "ଓଡ଼ିଆ", sttSupported: false },
    { code: "as", name: "Assamese", nativeName: "অসমীয়া", sttSupported: false },
    { code: "en-IN", name: "English (India)", nativeName: "English (India)", sttSupported: true },
    { code: "en-US", name: "English (US)", nativeName: "English (US)", sttSupported: true },
    { code: "en-GB", name: "English (UK)", nativeName: "English (UK)", sttSupported: true },
];

export const INDIAN_LANGUAGES = LANGUAGES.filter(l => l.code !== "en-US" && l.code !== "en-GB");

export function languageDisplay(code: string): string {
    const lang = LANGUAGES.find(l => l.code === code);
    if (!lang) return code;
    return `${lang.name} (${lang.nativeName})`;
}

export function defaultLanguage(): string {
    return "en-IN";
}
