import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

export type Language = 'it' | 'en';

type Dict = Record<string, string>;

const dictionaries: Record<Language, Dict> = {
  it: {
    'app.title': 'Collezione Emanuele Artom - Interfaccia conversazionale',

    'header.title': 'Collezione Emanuele Artom',
    'header.subtitle': 'Accesso conversazionale alle risorse bibliografiche e archivistiche',

    // Keep "Ready" as-is per requirement (tech detail)
    'mode.ready': 'Ready',
    'mode.conversational': 'Conversazionale',
    'mode.knowledge': 'Conoscenza',

    'welcome.heading': 'Benvenuto nella Collezione di Emanuele Artom',
    'welcome.body':
      'Puoi fare domande su Emanuele Artom, sui suoi scritti e sui materiali della Collezione. Ti aiuto a esplorare documenti e risorse, indicando le fonti disponibili.',

    'input.placeholder': 'Chiedi informazioni su vita, scritti e documenti della Collezione…',
    'input.hint': 'Invio per inviare · Maiusc+Invio per andare a capo',
    'footer.beta': 'Prototipo di ricerca (beta).',

    'loading.searching': 'Ricerca nell’archivio…',

    'sources.title': 'Fonti e citazioni',
    'sources.empty': 'Le citazioni appariranno qui quando fai domande sull’archivio.',
    'sources.type.authored_by_subject': 'Scritto da Artom',
    'sources.type.subject_library': 'Dalla biblioteca di Artom',
    'sources.type.about_subject': 'Su Artom',
    'sources.type.subject_traces': 'Tracce di Artom',
    'sources.type.default': 'Documento',
    'sources.by': 'di',
    'sources.count': '{{count}} {{label}} {{found}}',
  },
  en: {
    'app.title': 'Emanuele Artom Collection - Conversational Interface',

    'header.title': 'Emanuele Artom Collection',
    'header.subtitle': 'Conversational access to bibliographic and archival resources',

    // Keep "Ready" as-is per requirement (tech detail)
    'mode.ready': 'Ready',
    'mode.conversational': 'Conversational',
    'mode.knowledge': 'Knowledge',

    'welcome.heading': 'Welcome to the Emanuele Artom Collection',
    'welcome.body':
      'Ask about Emanuele Artom, his writings, and the materials in the collection. I can help you explore documents and resources, with available sources.',

    'input.placeholder': "Ask about Artom’s life, writings, or documents in the collection…",
    'input.hint': 'Enter to send · Shift+Enter for new line',
    'footer.beta': 'Research prototype (beta).',

    'loading.searching': 'Searching the archive…',

    'sources.title': 'Sources & Citations',
    'sources.empty': 'Citations will appear here when you ask questions about the archive.',
    'sources.type.authored_by_subject': 'Written by Artom',
    'sources.type.subject_library': "From Artom's Library",
    'sources.type.about_subject': 'About Artom',
    'sources.type.subject_traces': "Artom's Traces",
    'sources.type.default': 'Document',
    'sources.by': 'by',
    'sources.count': '{{count}} {{label}} {{found}}',
  },
};

type I18nContextValue = {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);

function interpolate(template: string, vars: Record<string, string | number>) {
  return template.replace(/\{\{(\w+)\}\}/g, (_, key: string) => String(vars[key] ?? ''));
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Language>(() => {
    const stored = window.localStorage.getItem('lang');
    return stored === 'en' || stored === 'it' ? stored : 'it';
  });

  const setLang = (next: Language) => {
    setLangState(next);
    window.localStorage.setItem('lang', next);
  };

  const t = useMemo(() => {
    return (key: string, vars?: Record<string, string | number>) => {
      const dict = dictionaries[lang];
      const fallback = dictionaries.it;
      const template = dict[key] ?? fallback[key] ?? key;
      return vars ? interpolate(template, vars) : template;
    };
  }, [lang]);

  useEffect(() => {
    document.title = dictionaries[lang]['app.title'] ?? document.title;
    document.documentElement.lang = lang;
  }, [lang]);

  const value = useMemo<I18nContextValue>(() => ({ lang, setLang, t }), [lang, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return ctx;
}

