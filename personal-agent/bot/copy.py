WELCOME = (
    "Привет, {name}! Я твой <b>личный агент</b> — помогаю не забывать дела "
    "и держать всё под контролем.\n\n"
    "<b>Что умею:</b>\n"
    "📋 <b>Задачи</b> — напоминания текстом, голосом или звонком на телефон\n"
    "📆 <b>Сегодня</b> — что запланировано на день\n"
    "📝 <b>Заметки</b> — быстро записать мысль\n"
    "📅 <b>Календарь</b> — синхронизация с Google Calendar\n"
    "🌐 <b>Переводчик</b> — перевод текста и голосовых\n"
    "☀️ <b>Утром</b> — краткий обзор задач на день\n\n"
    "<b>Как пользоваться:</b>\n"
    "Просто напиши или надиктуй, например:\n"
    "• «Завтра в 9:00 позвонить маме»\n"
    "• «Каждый понедельник в 10 созвон с командой»\n"
    "• «Заметка: идея для проекта»\n\n"
    "В списке <b>📋 Мои задачи</b> — кнопки ✏️ изменить и ✅ выполнить.\n\n"
    "Сначала укажи свой часовой пояс: /timezone\n"
    "Всё по кнопкам внизу. Подробнее: /help"
)

TIMEZONE_HELP_EXAMPLES = (
    "Примеры:\n"
    "/timezone playa — Playa del Carmen\n"
    "/timezone плая — то же (кириллицей)\n"
    "/timezone moscow — Москва\n"
    "/timezone new york — Нью-Йорк\n"
    "/timezone Asia/Tokyo — любой IANA-пояс\n"
    "Можно без слэша: <code>таймзон playa</code>"
)

TIMEZONE_SETUP_PROMPT = (
    "🌍 <b>Укажите ваш часовой пояс</b>\n\n"
    "У каждого пользователя свой пояс — задачи и Google Calendar "
    "будут в <b>вашем</b> локальном времени.\n\n"
    + TIMEZONE_HELP_EXAMPLES
    + "\n\nТекущий пояс: /timezone"
)

HELP_TEXT = (
    "<b>Как пользоваться</b>\n\n"
    "<b>📋 Задачи</b>\n"
    "Напиши или надиктуй обычным языком:\n"
    "• «Завтра в 10:00 купить молоко»\n"
    "• «Каждый понедельник в 9 созвон»\n"
    "• «Через час позвонить — голосом»\n\n"
    "Кнопка <b>📋 Мои задачи</b> — список, там же ✏️ изменить и ✅ выполнить.\n"
    "Кнопка <b>📆 Сегодня</b> — только задачи на сегодня.\n\n"
    "<b>📝 Заметки</b>\n"
    "«Заметка: текст» или кнопка <b>📝 Заметки</b>\n\n"
    "<b>📅 Календарь</b>\n"
    "Кнопка <b>📅 Календарь</b> — подключить Google (один раз). "
    "Новые задачи попадут в календарь сами.\n\n"
    "<b>📞 Телефон</b>\n"
    "Кнопка <b>📞 Телефон</b> — привязать номер, если нужен звонок-напоминание.\n\n"
    "<b>🌐 Переводчик</b>\n"
    "Кнопка <b>🌐 Переводчик</b> — перевести текст или голос.\n\n"
    "<b>☀️ Утром</b> пришлю краткий обзор дня "
    "(выключить: /digest off)\n\n"
    "<b>Полезные команды</b>\n"
    "/timezone — часовой пояс\n"
    "/edit — изменить задачу\n"
    "/tasks_done — завершённые задачи"
)

TASK_CREATED = (
    "✅ Задача #{task_id} создана\n"
    "<b>{title}</b>\n"
    "⏰ {due_at}\n"
    "🔔 {notify_types}{recurrence_line}{calendar_line}\n\n"
    "Список: кнопка <b>📋 Мои задачи</b>\n"
    "<i>Кнопки «Выполнено» / «15 мин» придут только когда наступит время напоминания.</i>"
)

CALENDAR_SYNCED_LINE = "\n📅 Добавлено в Google Calendar"
CALENDAR_NOT_SYNCED_LINE = "\n⚠️ В Google Calendar не добавлено (подключите 📅 Календарь)"
CALENDAR_REMOVED_LINE = "\n📅 Удалено из Google Calendar"
CALENDAR_REMOVE_FAILED_LINE = (
    "\n⚠️ Не удалось удалить из Google Calendar — попробуйте /calendar_resync"
)

TASK_LIST_EMPTY = "У тебя нет активных задач. Напиши, что нужно напомнить."

TASK_LIST_HEADER = "<b>Активные задачи ({count}):</b>"
TASK_TODAY_HEADER = "<b>Задачи на сегодня ({count}):</b>"

TASK_ITEM = (
    "#{id} — <b>{title}</b>\n"
    "⏰ {due_at} · {notify_types}{recurrence}"
)

DIGEST_HEADER = "☀️ <b>Доброе утро! Задачи на сегодня ({count}):</b>"
DIGEST_EMPTY = "☀️ <b>Доброе утро!</b> На сегодня задач нет — отличный день!"
DIGEST_ITEM = "#{id} — <b>{title}</b>\n⏰ {due_at} · {notify_types}{recurrence}"
DIGEST_ENABLED = "☀️ Утренний дайджест включён ({hour}:00)."
DIGEST_DISABLED = "Утренний дайджест отключён. Включить: /digest on"
DIGEST_TIME_SET = "☀️ Дайджест будет приходить в <b>{hour}:00</b> (ваш часовой пояс)."

NOTE_VIEW = "📝 <b>Заметка #{note_id}</b>\n\n{content}"
NOTE_DELETE_CONFIRM = "🗑 Заметка #{note_id} удалена."

TASK_DONE = "✅ Задача #{task_id} отмечена выполненной."
TASK_CANCELLED = "🗑 Задача #{task_id} отменена."
TASK_NOT_FOUND = "Задача не найдена или уже завершена."
TASK_ARCHIVED_HEADER = "<b>Завершённые задачи (последние):</b>"
TASK_ARCHIVED_EMPTY = "Нет завершённых или отменённых задач."
TASK_ARCHIVED_ITEM = "#{id} — <b>{title}</b> ({status})\n⏰ {due_at}"
TASK_RESTORED = "↩️ Задача #{task_id} «{title}» снова в активных."

TASK_EDIT_NEED_ID = (
    "Использование: <code>/edit ID</code>\n"
    "Пример: <code>/edit 5</code>\n\n"
    "Или напишите: «перенеси задачу 5 на завтра в 10:00»"
)
TASK_EDIT_NOT_FOUND = "Задача #{task_id} не найдена или уже завершена."
TASK_EDIT_PROMPT = (
    "✏️ <b>Редактирование задачи #{task_id}</b>\n"
    "<b>{title}</b>\n"
    "⏰ {due_at} · {notify_types}\n\n"
    "Напишите что изменить:\n"
    "• время: «завтра в 15:00» или «через 2 часа»\n"
    "• название: «позвонить маме»\n"
    "• оба: «завтра в 9 позвонить маме»\n\n"
    "Выйти: <code>/edit_off</code> или кнопка ❌"
)
TASK_EDIT_SUCCESS = (
    "✏️ Задача #{task_id} обновлена\n"
    "<b>{title}</b>\n"
    "⏰ {due_at}\n"
    "🔔 {notify_types}"
)
TASK_EDIT_EMPTY_CHANGES = (
    "Не понял, что изменить. Примеры:\n"
    "• «завтра в 10:00»\n"
    "• «купить хлеб»\n"
    "• «только время — через 3 часа»"
)
TASK_EDIT_EXIT = "✏️ Редактирование завершено."

REMINDER_MESSAGE = "⏰ <b>Напоминание</b>\n{title}"
REMINDER_ACTIONS_HINT = (
    "Что сделать?\n"
    "• <b>Выполнено</b> — готово\n"
    "• <b>15 мин</b> / <b>+1ч</b> / <b>Завтра 9:00</b> / <b>Вечером</b> — отложить\n"
    "• <b>Отменить</b> — снять напоминание"
)
REMINDER_CALL_CAPTION = "📞 Голосовое напоминание: {title}"
REMINDER_PHONE_SENT = "📞 Звонок на телефон отправлен: <b>{title}</b>"

PARSE_FAILED = (
    "Не удалось понять задачу. Уточни время, например:\n"
    "«Завтра в 10:00 купить молоко»"
)

TIMEZONE_UPDATED = (
    "Часовой пояс обновлён: <b>{timezone}</b>\n"
    "Все новые задачи будут в этом времени."
)
INVALID_TIMEZONE = (
    "Не понял часовой пояс: <b>{input}</b>\n\n"
    + TIMEZONE_HELP_EXAMPLES
    + "\n\nМожно просто написать: <code>плая</code> или <code>playa</code>"
)

NOTIFY_MESSAGE = "сообщение"
NOTIFY_CALL = "звонок"
NOTIFY_PHONE = "телефон"
NOTIFY_BOTH = "сообщение + звонок"
NOTIFY_PHONE_CALL = "звонок + телефон"

VOICE_HINT = (
    "🎙 Голосовой ввод требует OPENAI_API_KEY (Whisper).\n"
    "Добавьте ключ в .env и перезапустите бота."
)
VOICE_FAILED = "Не удалось распознать голосовое сообщение. Попробуйте ещё раз."
VOICE_TRANSCRIBED = "🎙 Распознано: <i>{text}</i>"

CALENDAR_NOT_CONFIGURED = (
    "Google Calendar временно недоступен.\n\n"
    "Сервер бота перезапускается — попробуйте через минуту.\n"
    "Если не помогло: GitHub → Settings → Secrets →\n"
    "<code>GOOGLE_CLIENT_ID</code> и <code>GOOGLE_CLIENT_SECRET</code>"
)
CALENDAR_NOT_CONNECTED = (
    "📅 <b>Подключение Google Calendar</b> (один раз)\n\n"
    '<a href="{url}">Авторизоваться в Google</a>\n\n'
    "<b>Как это работает:</b>\n"
    "1. Нажмите ссылку и войдите в Google\n"
    "2. Вернитесь в Telegram — придёт «Google Calendar подключён»\n"
    "3. Если бот молчит — на странице Google нажмите «Скопировать команду» и отправьте боту\n\n"
    "После подключения:\n"
    "• новые задачи сразу попадают в Google Calendar\n"
    "• старые активные — через /calendar_sync\n"
    "• выполненные и отменённые — удаляются из календаря автоматически\n\n"
    "События создаются в <b>вашем</b> часовом поясе — сначала укажите: /timezone"
)
CALENDAR_CONNECTED = "✅ Google Calendar подключён!"
CALENDAR_ENABLED = "✅ Синхронизация с Google Calendar включена."
CALENDAR_DISABLED = "Синхронизация с Google Calendar отключена."
CALENDAR_STATUS = (
    "📅 Календарь: {status}\n"
    "Ваш часовой пояс в боте: <b>{timezone}</b>\n\n"
    "События в Google Calendar создаются в этом поясе.\n"
    "Если время в календаре не совпадает — смените пояс: /timezone\n\n"
    "Синхронизировать: /calendar_sync\n"
    "Пересоздать события: /calendar_resync"
)

PHONE_SAVED = "📞 Номер сохранён: <b>{phone}</b>\nТеперь можно использовать «на телефон» в задачах."
PHONE_CURRENT = "📞 Ваш номер: <b>{phone}</b>\nИзменить: /phone +79991234567\nУдалить: /phone удалить"
PHONE_REMOVED = "📞 Номер телефона удалён."
INVALID_PHONE = "Неверный формат. Пример: +79991234567"
PHONE_TWILIO_NOT_CONFIGURED = (
    "Телефонные звонки не настроены на сервере.\n"
    "Нужны TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER"
)

NOTE_CREATED = "📝 Заметка #{note_id} сохранена."
NOTE_LIST_EMPTY = "Заметок пока нет. Напишите: Заметка: ваш текст"
NOTE_LIST_HEADER = "<b>Заметки ({count}):</b>"
NOTE_NOT_FOUND = "Заметка не найдена."
NOTE_DELETED = "🗑 Заметка #{note_id} удалена."

TRANSLATE_PROMPT = (
    "🌐 <b>Режим переводчика</b>\n\n"
    "Отправьте текст или голосовое — определю язык и переведу.\n"
    "• любой язык → <b>русский</b>\n"
    "• русский → <b>English</b> (/translate_lang es, de…)\n\n"
    "⚠️ Перевод <b>только здесь</b>. В обычном чате текст идёт в задачи.\n"
    "Для задачи: нажмите 📋 или любую другую кнопку меню.\n\n"
    "Указать язык вручную:\n"
    "• <code>на испанский: Hello world</code>\n"
    "• <code>переведи на немецкий: Good morning</code>\n\n"
    "Выйти: любая другая кнопка меню."
)
TRANSLATE_RESULT = (
    "🌐 <b>{source_lang}</b> → <b>{target_lang}</b>\n\n"
    "<i>{source}</i>\n\n"
    "➡️ {translation}"
)
TRANSLATE_LANG_SET = "Язык перевода с русского: <b>{lang}</b>"
TRANSLATE_UNKNOWN_LANG = (
    "Не знаю такой язык.\n"
    "Примеры: en, es, de, fr, it, pt, uk, tr, zh, ja, ko, ar"
)
TRANSLATE_SAME_LANG = (
    "Не удалось перевести — возможно, текст уже на нужном языке.\n"
    "Попробуйте: <code>на русский: ваш текст</code> или уточните язык."
)
TRANSLATE_EXIT = "🌐 Переводчик выключен. Возвращайтесь в любое время кнопкой «🌐 Переводчик»."
TRANSLATE_NEED_OPENAI = "Переводчик требует OPENAI_API_KEY в настройках бота."
