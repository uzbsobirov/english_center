export const translations = {
  uz: {
    appTitle: "Ingliz Tili Testlari",
    appSubtitle: "Yo'nalish va darajangizni tanlang",
    step1Title: "1. Yo'nalishni tanlang:",
    step2Title: "2. Darajani tanlang ({selectedType}):",
    types: {
      General: {
        title: "🌱 General English",
        subtitle: "Grammatika va so'zlashuv",
      },
      CEFR: {
        title: "🎯 CEFR Testlari",
        subtitle: "Grammatika va leksika darajasi",
      },
      IELTS: {
        title: "🇬🇧 IELTS Testlari",
        subtitle: "Academic & General tayyorgarlik",
      },
    },
    levels: {
      A1: { desc: "Boshlang'ich daraja" },
      A2: { desc: "Oddiy muloqot" },
      B1: { desc: "O'rta daraja" },
      B2: { desc: "Kuchli o'rta" },
      C1: { desc: "Yuqori daraja" },
      C2: { desc: "Mukammal" },
    },
    loading: "Test savollari yuklanmoqda...",
    errorTitle: "Test yuklanmadi",
    changeTest: "Boshqa test tanlash",
    back: "◀️ Orqaga",
    submitButton: "Yakunlash ({answered}/{total})",
    submitting: "⏳ Natijalar hisoblanmoqda...",
    resultPassedTitle: "Ajoyib natija!",
    resultFailedTitle: "Test yakunlandi",
    correctAnswers: "{score} / {total} ta to'g'ri javob",
    resultPassedDesc: "Tabriklaymiz! Siz o'tish balini to'pladingiz. Natijangiz Telegram botingizga yuborildi.",
    resultFailedDesc: "Bu daraja uchun ball yetarli bo'lmadi. Bilimingizni mustahkamlab, qayta urinib ko'rishingiz mumkin.",
    retakeTest: "Yana test ishlash",
  },
  ru: {
    appTitle: "Тесты по английскому",
    appSubtitle: "Выберите направление и свой уровень",
    step1Title: "1. Выберите направление:",
    step2Title: "2. Выберите уровень ({selectedType}):",
    types: {
      General: {
        title: "🌱 General English",
        subtitle: "Грамматика и разговорная речь",
      },
      CEFR: {
        title: "🎯 Тесты CEFR",
        subtitle: "Уровень грамматики и лексики",
      },
      IELTS: {
        title: "🇬🇧 Тесты IELTS",
        subtitle: "Подготовка к Academic & General",
      },
    },
    levels: {
      A1: { desc: "Начальный уровень" },
      A2: { desc: "Базовое общение" },
      B1: { desc: "Средний уровень" },
      B2: { desc: "Выше среднего" },
      C1: { desc: "Продвинутый уровень" },
      C2: { desc: "Профессиональный" },
    },
    loading: "Загрузка вопросов теста...",
    errorTitle: "Тест не загружен",
    changeTest: "Выбрать другой тест",
    back: "◀️ Назад",
    submitButton: "Завершить ({answered}/{total})",
    submitting: "⏳ Подсчет результатов...",
    resultPassedTitle: "Отличный результат!",
    resultFailedTitle: "Тест завершен",
    correctAnswers: "{score} / {total} правильных ответов",
    resultPassedDesc: "Поздравляем! Вы набрали проходной балл. Результат отправлен в ваш Telegram-бот.",
    resultFailedDesc: "Баллов для этого уровня недостаточно. Вы можете закрепить знания и попробовать снова.",
    retakeTest: "Пройти тест еще раз",
  },
  en: {
    appTitle: "English Language Tests",
    appSubtitle: "Choose your track and level",
    step1Title: "1. Select track:",
    step2Title: "2. Select level ({selectedType}):",
    types: {
      General: {
        title: "🌱 General English",
        subtitle: "Grammar & daily conversation",
      },
      CEFR: {
        title: "🎯 CEFR Tests",
        subtitle: "Grammar & vocabulary level",
      },
      IELTS: {
        title: "🇬🇧 IELTS Tests",
        subtitle: "Academic & General preparation",
      },
    },
    levels: {
      A1: { desc: "Beginner level" },
      A2: { desc: "Elementary communication" },
      B1: { desc: "Intermediate level" },
      B2: { desc: "Upper-Intermediate" },
      C1: { desc: "Advanced level" },
      C2: { desc: "Proficiency" },
    },
    loading: "Loading test questions...",
    errorTitle: "Failed to load test",
    changeTest: "Choose another test",
    back: "◀️ Back",
    submitButton: "Finish ({answered}/{total})",
    submitting: "⏳ Calculating results...",
    resultPassedTitle: "Great result!",
    resultFailedTitle: "Test completed",
    correctAnswers: "{score} / {total} correct answers",
    resultPassedDesc: "Congratulations! You reached the passing score. Your result was sent to your Telegram bot.",
    resultFailedDesc: "Not enough score for this level. You can practice and try again.",
    retakeTest: "Take test again",
  },
};


export const getTranslation = (lang = "uz") => {
  const normalized = ["uz", "ru", "en"].includes(lang) ? lang : "uz";
  return translations[normalized];
};
