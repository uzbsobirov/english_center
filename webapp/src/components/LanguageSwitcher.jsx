import React from "react";

export default function LanguageSwitcher({ currentLang, onChangeLang }) {
  const languages = [
    { code: "uz", label: "🇺🇿 UZ" },
    { code: "ru", label: "🇷🇺 RU" },
    { code: "en", label: "🇬🇧 EN" },
  ];

  return (
    <div className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800 shadow-inner text-xs font-bold shrink-0">
      {languages.map((l) => (
        <button
          key={l.code}
          type="button"
          onClick={() => onChangeLang(l.code)}
          className={`px-2 py-1 rounded-lg transition-all text-[11px] font-bold ${
            currentLang === l.code
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-black"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
          }`}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
