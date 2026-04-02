const translations = {
  ru: {
    logo: "LoRa mini-landing",
    lang_label: "Языки:",
    wiki_link: "📚 Первоисточник: статья в Wikipedia про LoRa",
    wiki_href: "https://ru.wikipedia.org/wiki/LoRa",
    badge: "Связь будущего",
    hero_title: "LoRa — радиосвязь на большие расстояния",
    hero_subtitle:
      "Представь: датчик в школьной теплице отправляет температуру на другой конец города без интернета и почти без батарейки.",
    hero_cta: "Узнать за 1 минуту",
    what_title: "Что это?",
    what_text:
      "LoRa (Long Range) — технология передачи маленьких сообщений по радио на километры, даже если сигнал слабый.",
    where_title: "Где пригодится?",
    where_1: "Умная школа: контроль света и температуры.",
    where_2: "Экология: датчики воздуха и влажности.",
    where_3: "Проекты STEM: «умные» рюкзаки, теплицы, метеостанции.",
    why_title: "Почему школьникам это круто?",
    why_text:
      "Это простой вход в IoT: можно собрать свой проект на Arduino/ESP32 и показать реальное применение физики и программирования.",
    challenge_title: "Мини-челлендж",
    challenge_text:
      "Собери 2 устройства LoRa: одно измеряет температуру, второе показывает её на экране. Дальность теста: чем дальше — тем интереснее!",
    challenge_note: "⚡ Главное: маленькие сообщения, зато очень далеко и экономно."
  },
  en: {
    logo: "LoRa mini-landing",
    lang_label: "Languages:",
    wiki_link: "📚 Source: Wikipedia article about LoRa",
    wiki_href: "https://en.wikipedia.org/wiki/LoRa",
    badge: "Future-ready communication",
    hero_title: "LoRa — long-range radio communication",
    hero_subtitle:
      "Imagine this: a sensor in a school greenhouse sends temperature data across the city without internet and with tiny battery usage.",
    hero_cta: "Learn in 1 minute",
    what_title: "What is it?",
    what_text:
      "LoRa (Long Range) is a technology for sending small radio messages over kilometers, even with weak signal.",
    where_title: "Where can it help?",
    where_1: "Smart school: light and temperature monitoring.",
    where_2: "Ecology: air quality and humidity sensors.",
    where_3: "STEM projects: smart backpacks, greenhouses, weather stations.",
    why_title: "Why is it cool for students?",
    why_text:
      "It is an easy entry into IoT: build a project with Arduino/ESP32 and show real-world use of physics and coding.",
    challenge_title: "Mini challenge",
    challenge_text:
      "Build 2 LoRa devices: one measures temperature, the other displays it on screen. Test who can reach the longest distance!",
    challenge_note: "⚡ Key point: tiny messages, but very far and power-efficient."
  }
};

const langButtons = document.querySelectorAll(".lang-btn");
const translatable = document.querySelectorAll("[data-i18n]");
const translatableHref = document.querySelectorAll("[data-i18n-href]");

function setLanguage(lang) {
  const dict = translations[lang] ?? translations.ru;
  document.documentElement.lang = lang;

  translatable.forEach((el) => {
    const key = el.dataset.i18n;
    if (key && dict[key]) {
      el.textContent = dict[key];
    }
  });

  translatableHref.forEach((el) => {
    const key = el.dataset.i18nHref;
    if (key && dict[key]) {
      el.setAttribute("href", dict[key]);
    }
  });

  langButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === lang);
  });
}

langButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    const nextLang = btn.dataset.lang === "en" ? "en" : "ru";
    setLanguage(nextLang);
  });
});

setLanguage("ru");
