"""
Matn va jadval ma'lumotlarini chiroyli formatlash uchun yordamchi funksiyalar.
"""

DAY_TRANSLATIONS = {
    "uz": {
        "monday": "Dushanba", "tuesday": "Seshanba", "wednesday": "Chorshanba",
        "thursday": "Payshanba", "friday": "Juma", "saturday": "Shanba", "sunday": "Yakshanba",
        "mon": "Dush", "tue": "Sesh", "wed": "Chor", "thu": "Pay", "fri": "Jum", "sat": "Shan", "sun": "Yak",
        "1": "Dushanba", "2": "Seshanba", "3": "Chorshanba", "4": "Payshanba", "5": "Juma", "6": "Shanba", "7": "Yakshanba",
    },
    "ru": {
        "monday": "Понедельник", "tuesday": "Вторник", "wednesday": "Среда",
        "thursday": "Четверг", "friday": "Пятница", "saturday": "Суббота", "sunday": "Воскресенье",
        "mon": "Пн", "tue": "Вт", "wed": "Ср", "thu": "Чт", "fri": "Пт", "sat": "Сб", "sun": "Вс",
        "1": "Понедельник", "2": "Вторник", "3": "Среда", "4": "Четверг", "5": "Пятница", "6": "Суббота", "7": "Воскресенье",
    },
    "en": {
        "monday": "Monday", "tuesday": "Tuesday", "wednesday": "Wednesday",
        "thursday": "Thursday", "friday": "Friday", "saturday": "Saturday", "sunday": "Sunday",
        "mon": "Mon", "tue": "Tue", "wed": "Wed", "thu": "Thu", "fri": "Fri", "sat": "Sat", "sun": "Sun",
        "1": "Monday", "2": "Tuesday", "3": "Wednesday", "4": "Thursday", "5": "Friday", "6": "Saturday", "7": "Sunday",
    },
}


def _translate_day(day_str: str, lang: str = "uz") -> str:
    cleaned = str(day_str).strip().lower()
    lang_dict = DAY_TRANSLATIONS.get(lang, DAY_TRANSLATIONS["uz"])
    return lang_dict.get(cleaned, str(day_str))


def format_schedule(schedule_data, lang: str = "uz") -> str:
    """
    Dars jadvalini toza va chiroyli matn ko'rinishida formatlaydi.
    Har qanday ma'lumot tuzilmasini (list of dicts, dict, string) to'g'ri qabul qiladi.
    """
    if not schedule_data:
        if lang == "uz":
            return "Tez orada belgilanadi"
        elif lang == "ru":
            return "Будет определено"
        return "To be announced"

    if isinstance(schedule_data, str):
        return schedule_data

    # 1. Agar list bo'lsa: [{'day': 'Monday', 'time': '18:00'}, {'day': 'Wednesday', 'time': '18:00'}]
    if isinstance(schedule_data, list):
        items = []
        common_time = None
        all_same_time = True

        for entry in schedule_data:
            if isinstance(entry, dict):
                d = _translate_day(entry.get("day", ""), lang)
                t = entry.get("time", "")
                if common_time is None and t:
                    common_time = t
                elif t and t != common_time:
                    all_same_time = False

                if t:
                    items.append((d, t))
                else:
                    items.append((d, ""))
            elif isinstance(entry, str):
                items.append((_translate_day(entry, lang), ""))

        if not items:
            return "Tez orada belgilanadi"

        if all_same_time and common_time:
            days_str = ", ".join(d for d, _ in items if d)
            return f"{days_str} ({common_time})"
        else:
            return ", ".join(f"{d} {t}".strip() for d, t in items if d)

    # 2. Agar dict bo'lsa: {'days': ['Monday', 'Wednesday'], 'time': '18:00'}
    if isinstance(schedule_data, dict):
        raw_days = schedule_data.get("days", [])
        time = schedule_data.get("time", "")
        if isinstance(raw_days, list):
            days_str = ", ".join(_translate_day(d, lang) for d in raw_days)
        else:
            days_str = _translate_day(str(raw_days), lang)

        return f"{days_str} ({time})" if time else days_str

    return str(schedule_data)
