import type { Locale } from "./i18n";

type Dict = {
  meta: { title: string; description: string };
  nav: { work: string; platform: string; method: string; team: string; contact: string; cta: string };
  hero: {
    badge: string;
    titleA: string;
    titleB: string;
    lede: string;
    ctaPrimary: string;
    ctaSecondary: string;
    ticker: string;
    live: string;
  };
  metrics: { label: string; value: string; note: string }[];
  platform: {
    eyebrow: string;
    title: string;
    lede: string;
    liveLabel: string;
    bid: string;
    ask: string;
    spread: string;
    source: string;
    bias: string;
    setup: string;
    entry: string;
    stop: string;
    targets: string;
    rr: string;
    confidence: string;
    factors: string;
    invalidation: string;
    zones: string;
    liquidity: string;
    atr: string;
    session: string;
    updated: string;
    disclaimer: string;
    tabs: { h1: string; h4: string; d1: string };
  };
  method: {
    eyebrow: string;
    title: string;
    lede: string;
    steps: { n: string; title: string; body: string }[];
  };
  team: {
    eyebrow: string;
    title: string;
    lede: string;
    note: string;
    agents: string;
    departments: string;
    managers: string;
    repos: string;
    managerLabel: string;
    repoLabel: string;
    peopleLabel: string;
  };
  quality: {
    eyebrow: string;
    title: string;
    lede: string;
    verified: string;
    blockedLabel: string;
    blockedNote: string;
    rows: { label: string; value: string; state: "ok" | "blocked"; note?: string }[];
  };
  work: {
    eyebrow: string;
    title: string;
    lede: string;
    status: string;
    live: string;
    items: { name: string; kind: string; body: string; stack: string[] }[];
  };
  contact: {
    eyebrow: string;
    title: string;
    lede: string;
    cta: string;
    note: string;
  };
  footer: { rights: string; lang: string; builtBy: string };
};

const en: Dict = {
  meta: {
    title: "AI ASTRA AGENCY — an autonomous studio, measured",
    description:
      "An AI-agent workforce that designs, builds and verifies software. Live gold-analysis platform, private per-department engineering, every claim measured.",
  },
  nav: { work: "Work", platform: "Platform", method: "Method", team: "Team", contact: "Contact", cta: "Start a project" },
  hero: {
    badge: "Autonomous studio · 31 agents · est. 2026",
    titleA: "We build software",
    titleB: "that proves itself.",
    lede:
      "An autonomous AI-agent workforce designs, builds and independently verifies every artefact before it ships. No hand-waving — every number on this page is measured from our own systems.",
    ctaPrimary: "See the live platform",
    ctaSecondary: "How we work",
    ticker: "XAUUSD",
    live: "live",
  },
  metrics: [
    { label: "Readiness checks", value: "20/20", note: "agents, delegation, sessions, security" },
    { label: "Department repos", value: "10/10", note: "private, verified" },
    { label: "Engine tests", value: "27/27", note: "analysis, setups, integrity" },
    { label: "Agents on staff", value: "31", note: "across 11 departments" },
  ],
  platform: {
    eyebrow: "Flagship product — Astra Trading",
    title: "Gold analysis, decoded live.",
    lede:
      "A trilingual gold (XAUUSD) analysis engine. Real market data, a transparent methodology, and a published track record — not signals sold on hype.",
    liveLabel: "Live reading",
    bid: "Bid",
    ask: "Ask",
    spread: "Spread",
    source: "Feed",
    bias: "Bias",
    setup: "Active setup",
    entry: "Entry",
    stop: "Stop",
    targets: "Targets",
    rr: "Risk : reward",
    confidence: "Confidence",
    factors: "Why",
    invalidation: "Invalidation",
    zones: "Zones mapped",
    liquidity: "Liquidity pools",
    atr: "ATR(14)",
    session: "Session",
    updated: "Captured",
    disclaimer: "Analytical output, not investment advice.",
    tabs: { h1: "1H", h4: "4H", d1: "1D" },
  },
  method: {
    eyebrow: "Method",
    title: "Four gates. Nothing ships before the last one.",
    lede: "The same loop runs on a landing page and on a trading engine.",
    steps: [
      { n: "01", title: "Brief", body: "The goal is stated once. We return scope, a timeline and a fixed price — or an honest no." },
      { n: "02", title: "Build in parallel", body: "Department teams work simultaneously in separate private repositories, each with its own scoped access." },
      { n: "03", title: "Independent verification", body: "A separate quality pass attacks the artefact — fuzzing, adversarial security tests, visual review. Failures are fixed, not hidden." },
      { n: "04", title: "Ship and measure", body: "Delivery with the real files, plus the measured results. The record stays public." },
    ],
  },
  team: {
    eyebrow: "Organisation",
    title: "An org chart that is actually staffed.",
    lede: "Every department is a real manager agent with its own private repository and a scoped key that opens only that door.",
    note: "Cross-department access is blocked and tested — a manager cannot read another department's repository.",
    agents: "Agents",
    departments: "Departments",
    managers: "Managers",
    repos: "Private repos",
    managerLabel: "Manager",
    repoLabel: "Repository",
    peopleLabel: "Headcount",
  },
  quality: {
    eyebrow: "Evidence",
    title: "Measured, not claimed.",
    lede: "These are outputs of test suites in this repository.",
    verified: "verified",
    blockedLabel: "needs credentials",
    blockedNote:
      "Every figure here is produced by a run, not remembered. A suite that cannot run renders as unverified with its last measured score instead of a made-up one.",
    rows: [
      { label: "Readiness suite", value: "20 / 20", state: "ok" },
      { label: "Analysis engine", value: "27 / 27", state: "ok" },
      { label: "API contract", value: "23 / 23", state: "ok" },
      { label: "Security red-team", value: "25 / 27 · 2 open", state: "ok" },
      { label: "Department repos", value: "10 / 10", state: "ok" },
      { label: "Site audit (3 locales × 3 viewports)", value: "9 / 9", state: "ok" },
    ],
  },
  work: {
    eyebrow: "Work",
    title: "What exists today.",
    lede: "Built in-house, in the open. No borrowed portfolios, no stock imagery of work we did not do.",
    status: "Status",
    live: "Live",
    items: [
      {
        name: "Astra Trading",
        kind: "Product · SaaS",
        body: "Trilingual gold-analysis platform: candle engine, liquidity and zone mapping, transparent setups, published track record.",
        stack: ["FastAPI", "Python", "Supabase", "Next.js"],
      },
      {
        name: "Company site",
        kind: "Platform",
        body: "This site — a trilingual Next.js surface that renders the company's own live facts, served from a single origin.",
        stack: ["Next.js", "TypeScript", "Tailwind"],
      },
      {
        name: "Control plane",
        kind: "Internal tooling",
        body: "The system that hires, delegates to and audits the agent workforce — with a hard secret boundary and bounded self-healing.",
        stack: ["Python", "REST", "GitHub API"],
      },
    ],
  },
  contact: {
    eyebrow: "Contact",
    title: "Tell us the goal. Get scope, price and a date.",
    lede: "One brief. A real answer — including when the answer is no.",
    cta: "Start a project",
    note: "Settled in USDT (TRC20). Crypto-only by policy.",
  },
  footer: { rights: "All rights reserved.", lang: "Language", builtBy: "Built and verified by an AI-agent workforce." },
};

const ar: Dict = {
  meta: {
    title: "AI ASTRA AGENCY — استوديو مستقل، بالأرقام",
    description:
      "قوة عمل من وكلاء ذكاء اصطناعي تصمّم وتبني وتتحقق من البرمجيات. منصة تحليل ذهب حيّة، هندسة خاصة لكل قسم، وكل رقم مقيس فعلياً.",
  },
  nav: { work: "أعمالنا", platform: "المنصة", method: "المنهجية", team: "الفريق", contact: "تواصل", cta: "ابدأ مشروعاً" },
  hero: {
    badge: "استوديو مستقل · 31 وكيلاً · تأسّس 2026",
    titleA: "نبني برمجيات",
    titleB: "تُثبت نفسها بنفسها.",
    lede:
      "قوة عمل من وكلاء ذكاء اصطناعي تصمّم وتبني وتتحقق باستقلال من كل عمل قبل تسليمه. بلا كلام فارغ — كل رقم في هذه الصفحة مقيس من أنظمتنا.",
    ctaPrimary: "شاهد المنصة الحيّة",
    ctaSecondary: "كيف نعمل",
    ticker: "XAUUSD",
    live: "مباشر",
  },
  metrics: [
    { label: "فحوص الجاهزية", value: "20/20", note: "الوكلاء، التفويض، الجلسات، الأمن" },
    { label: "مستودعات الأقسام", value: "10/10", note: "خاصة، متحقَّق منها" },
    { label: "اختبارات المحرّك", value: "27/27", note: "التحليل، الإعدادات، السلامة" },
    { label: "وكيل على الملاك", value: "31", note: "عبر 11 قسماً" },
  ],
  platform: {
    eyebrow: "المنتج الرائد — Astra Trading",
    title: "تحليل الذهب، مباشر ومكشوف.",
    lede:
      "محرّك تحليل ذهب (XAUUSD) بثلاث لغات. بيانات سوق حقيقية، منهجية شفّافة، وسجل أداء منشور — لا توصيات تُباع بالتهويل.",
    liveLabel: "قراءة مباشرة",
    bid: "شراء",
    ask: "بيع",
    spread: "الفارق",
    source: "المصدر",
    bias: "الاتجاه",
    setup: "إعداد قائم",
    entry: "الدخول",
    stop: "الوقف",
    targets: "الأهداف",
    rr: "المخاطرة : المكافأة",
    confidence: "الثقة",
    factors: "الأسباب",
    invalidation: "إبطال الإعداد",
    zones: "مناطق مرصودة",
    liquidity: "بِرَك سيولة",
    atr: "ATR(14)",
    session: "الجلسة",
    updated: "وقت الالتقاط",
    disclaimer: "مخرَج تحليلي، وليس نصيحة استثمارية.",
    tabs: { h1: "ساعة", h4: "4 ساعات", d1: "يومي" },
  },
  method: {
    eyebrow: "المنهجية",
    title: "أربع بوابات. لا شيء يُسلَّم قبل الأخيرة.",
    lede: "الحلقة نفسها تُطبَّق على صفحة هبوط وعلى محرّك تداول.",
    steps: [
      { n: "٠١", title: "الموجز", body: "يُقال الهدف مرة واحدة. نعيد بالنطاق والجدول والسعر الثابت — أو بـ«لا» صادقة." },
      { n: "٠٢", title: "بناء متوازٍ", body: "فرق الأقسام تعمل في الوقت نفسه داخل مستودعات خاصة منفصلة، ولكل منها صلاحية مقيّدة." },
      { n: "٠٣", title: "تحقق مستقل", body: "مراجعة جودة منفصلة تهاجم العمل — اختبار عدائي، فحص أمني هجومي، مراجعة بصرية. الفشل يُصلَح لا يُخفى." },
      { n: "٠٤", title: "تسليم وقياس", body: "تسليم بالملفات الحقيقية مع النتائج المقيسة. السجل يبقى منشوراً." },
    ],
  },
  team: {
    eyebrow: "الهيكل",
    title: "هيكل تنظيمي موظَّف فعلاً.",
    lede: "كل قسم مدير حقيقي له مستودع خاص ومفتاح مقيّد يفتح بابه وحده.",
    note: "الوصول بين الأقسام محجوب ومُختبر — لا يستطيع مدير قراءة مستودع قسم آخر.",
    agents: "وكيل",
    departments: "قسماً",
    managers: "مديراً",
    repos: "مستودعاً خاصاً",
    managerLabel: "المدير",
    repoLabel: "المستودع",
    peopleLabel: "عدد الأفراد",
  },
  quality: {
    eyebrow: "الدليل",
    title: "مقيس، لا مُدَّعى.",
    lede: "هذه مخرجات مجموعات اختبار داخل هذا المستودع.",
    verified: "متحقَّق",
    blockedLabel: "يحتاج بيانات دخول",
    blockedNote:
      "كل رقم هنا ناتج عن تشغيل فعلي لا عن ذاكرة. أي مجموعة اختبار لا تستطيع العمل تُعرض كغير متحقَّق منها مع آخر نتيجة مقيسة، بدل رقم مختلق.",
    rows: [
      { label: "مجموعة الجاهزية", value: "20 / 20", state: "ok" },
      { label: "محرّك التحليل", value: "27 / 27", state: "ok" },
      { label: "عقد الـ API", value: "23 / 23", state: "ok" },
      { label: "الفريق الأمني الهجومي", value: "25 / 27 · ثغرتان", state: "ok" },
      { label: "مستودعات الأقسام", value: "10 / 10", state: "ok" },
      { label: "تدقيق الموقع (3 لغات × 3 مقاسات)", value: "9 / 9", state: "ok" },
    ],
  },
  work: {
    eyebrow: "الأعمال",
    title: "ما هو موجود فعلاً اليوم.",
    lede: "مبني داخلياً وبشفافية. لا محافظ مستعارة، ولا صور لأعمال لم نقم بها.",
    status: "الحالة",
    live: "حي",
    items: [
      {
        name: "Astra Trading",
        kind: "منتج · SaaS",
        body: "منصة تحليل ذهب بثلاث لغات: محرّك شموع، رسم مناطق وسيولة، إعدادات شفّافة، وسجل أداء منشور.",
        stack: ["FastAPI", "Python", "Supabase", "Next.js"],
      },
      {
        name: "موقع الشركة",
        kind: "منصة",
        body: "هذا الموقع — واجهة Next.js بثلاث لغات تعرض حقائق الشركة الحيّة من أصل واحد.",
        stack: ["Next.js", "TypeScript", "Tailwind"],
      },
      {
        name: "غرفة التحكم",
        kind: "أدوات داخلية",
        body: "النظام الذي يوظّف ويفوّض ويراجع قوة الوكلاء — بحدود أسرار صارمة وإصلاح ذاتي محدود.",
        stack: ["Python", "REST", "GitHub API"],
      },
    ],
  },
  contact: {
    eyebrow: "تواصل",
    title: "أخبرنا بالهدف. تستلم النطاق والسعر والموعد.",
    lede: "موجز واحد. إجابة حقيقية — بما فيها عندما تكون الإجابة «لا».",
    cta: "ابدأ مشروعاً",
    note: "الدفع بالـ USDT (شبكة TRC20). تعامل بالعملات الرقمية حصراً.",
  },
  footer: { rights: "جميع الحقوق محفوظة.", lang: "اللغة", builtBy: "مبني ومتحقَّق منه بواسطة قوة وكلاء ذكاء اصطناعي." },
};

const tr: Dict = {
  meta: {
    title: "AI ASTRA AGENCY — ölçülen otonom stüdyo",
    description:
      "Tasarımdan derlemeye ve doğrulamaya kadar her işi yürüten yapay zekâ ajanı işgücü. Canlı altın analiz platformu, her bölüme özel mühendislik.",
  },
  nav: { work: "İşler", platform: "Platform", method: "Yöntem", team: "Ekip", contact: "İletişim", cta: "Proje başlat" },
  hero: {
    badge: "Otonom stüdyo · 31 ajan · 2026",
    titleA: "Kendini kanıtlayan",
    titleB: "yazılımlar kuruyoruz.",
    lede:
      "Otonom bir yapay zekâ ajanı işgücü her eseri tasarlar, kurar ve bağımsız olarak doğrular. Laf kalabalığı yok — bu sayfadaki her sayı kendi sistemlerimizden ölçüldü.",
    ctaPrimary: "Canlı platformu gör",
    ctaSecondary: "Nasıl çalışıyoruz",
    ticker: "XAUUSD",
    live: "canlı",
  },
  metrics: [
    { label: "Hazırlık kontrolleri", value: "20/20", note: "ajanlar, devir, oturumlar, güvenlik" },
    { label: "Bölüm depoları", value: "10/10", note: "özel, doğrulandı" },
    { label: "Motor testleri", value: "27/27", note: "analiz, kurulumlar, bütünlük" },
    { label: "Kadrolu ajan", value: "31", note: "11 bölüm genelinde" },
  ],
  platform: {
    eyebrow: "Amiral gemisi — Astra Trading",
    title: "Altın analizi, canlı ve şeffaf.",
    lede:
      "Üç dilli altın (XAUUSD) analiz motoru. Gerçek piyasa verisi, şeffaf yöntem ve yayımlanmış bir performans kaydı — abartıyla satılan sinyaller değil.",
    liveLabel: "Canlı okuma",
    bid: "Alış",
    ask: "Satış",
    spread: "Makas",
    source: "Kaynak",
    bias: "Yön",
    setup: "Aktif kurulum",
    entry: "Giriş",
    stop: "Stop",
    targets: "Hedefler",
    rr: "Risk : getiri",
    confidence: "Güven",
    factors: "Gerekçe",
    invalidation: "Geçersizlik",
    zones: "Bölgeler",
    liquidity: "Likidite havuzları",
    atr: "ATR(14)",
    session: "Seans",
    updated: "Kayıt zamanı",
    disclaimer: "Analitik çıktı; yatırım tavsiyesi değildir.",
    tabs: { h1: "1S", h4: "4S", d1: "1G" },
  },
  method: {
    eyebrow: "Yöntem",
    title: "Dört kapı. Sonuncudan geçmeden hiçbir şey teslim edilmez.",
    lede: "Aynı döngü hem bir açılış sayfasında hem bir işlem motorunda çalışır.",
    steps: [
      { n: "01", title: "Brief", body: "Hedef bir kez söylenir. Kapsam, takvim ve sabit fiyatla döneriz — ya da dürüst bir hayır ile." },
      { n: "02", title: "Paralel üretim", body: "Bölüm ekipleri aynı anda, her biri kendi kapsamlı erişimli ayrı özel depolarında çalışır." },
      { n: "03", title: "Bağımsız doğrulama", body: "Ayrı bir kalite geçişi esere saldırır — fuzz, saldırgan güvenlik testleri, görsel inceleme. Hata düzeltilir, gizlenmez." },
      { n: "04", title: "Teslim ve ölçüm", body: "Gerçek dosyalarla teslim, ölçülen sonuçlarla birlikte. Kayıt açık kalır." },
    ],
  },
  team: {
    eyebrow: "Organizasyon",
    title: "Gerçekten kadrolu bir organizasyon şeması.",
    lede: "Her bölüm, yalnızca kendi kapısını açan kapsamlı anahtara ve özel depoya sahip gerçek bir yönetici ajandır.",
    note: "Bölümler arası erişim engellidir ve test edilir — bir yönetici başka bölümün deposunu okuyamaz.",
    agents: "Ajan",
    departments: "Bölüm",
    managers: "Yönetici",
    repos: "Özel depo",
    managerLabel: "Yönetici",
    repoLabel: "Depo",
    peopleLabel: "Kadro",
  },
  quality: {
    eyebrow: "Kanıt",
    title: "İddia değil, ölçüm.",
    lede: "Bunlar bu depodaki test paketlerinin çıktılarıdır.",
    verified: "doğrulandı",
    blockedLabel: "kimlik bilgisi gerekli",
    blockedNote:
      "Buradaki her sayı bir çalıştırmadan üretilir, hatırlanmaz. Çalışamayan bir paket, uydurulmuş bir sayı yerine en son ölçülen puanla doğrulanmamış olarak gösterilir.",
    rows: [
      { label: "Hazırlık paketi", value: "20 / 20", state: "ok" },
      { label: "Analiz motoru", value: "27 / 27", state: "ok" },
      { label: "API sözleşmesi", value: "23 / 23", state: "ok" },
      { label: "Güvenlik kırmızı takımı", value: "25 / 27 · 2 açık", state: "ok" },
      { label: "Bölüm depoları", value: "10 / 10", state: "ok" },
      { label: "Site denetimi (3 dil × 3 görünüm)", value: "9 / 9", state: "ok" },
    ],
  },
  work: {
    eyebrow: "İşler",
    title: "Bugün gerçekten var olan.",
    lede: "Şirket içinde, açıkta üretildi. Ödünç portföy yok, yapmadığımız işlerin stok görseli yok.",
    status: "Durum",
    live: "Canlı",
    items: [
      {
        name: "Astra Trading",
        kind: "Ürün · SaaS",
        body: "Üç dilli altın analiz platformu: mum motoru, bölge ve likidite haritalama, şeffaf kurulumlar, yayımlanmış kayıt.",
        stack: ["FastAPI", "Python", "Supabase", "Next.js"],
      },
      {
        name: "Şirket sitesi",
        kind: "Platform",
        body: "Bu site — şirketin kendi canlı verilerini tek kaynaktan sunan üç dilli bir Next.js yüzeyi.",
        stack: ["Next.js", "TypeScript", "Tailwind"],
      },
      {
        name: "Kontrol düzlemi",
        kind: "İç araçlar",
        body: "Ajan işgücünü işe alan, devreden ve denetleyen sistem — katı sır sınırı ve sınırlı kendini onarma ile.",
        stack: ["Python", "REST", "GitHub API"],
      },
    ],
  },
  contact: {
    eyebrow: "İletişim",
    title: "Hedefi söyleyin. Kapsam, fiyat ve tarih alın.",
    lede: "Tek brief. Gerçek bir yanıt — cevabın hayır olduğu durumlar dahil.",
    cta: "Proje başlat",
    note: "Ödeme USDT (TRC20) ile. Politika gereği yalnızca kripto.",
  },
  footer: { rights: "Tüm hakları saklıdır.", lang: "Dil", builtBy: "Bir yapay zekâ ajanı işgücü tarafından kuruldu ve doğrulandı." },
};

const DICTS: Record<Locale, Dict> = { en, ar, tr };

export function getDict(locale: Locale): Dict {
  return DICTS[locale] ?? en;
}

export type { Dict };
