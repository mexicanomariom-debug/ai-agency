WELCOME = (
    "Привет, {name}! Я твой <b>личный агент</b> в Telegram.\n\n"
    "<b>Модули:</b>\n"
    "📋 <b>Задачи</b> — напоминания сообщением, голосом и на телефон\n"
    "🎙 <b>Голос</b> — надиктуй задачу голосовым сообщением\n"
    "📅 <b>Календарь</b> — синхронизация с Google Calendar\n"
    "📝 <b>Заметки</b> — быстрые записи\n"
    "🤖 <b>AI</b> — свободный диалог (нужен OPENAI_API_KEY)\n"
    "🌐 <b>Переводчик</b> — перевод текста и голоса\n\n"
    "Пример: «Завтра в 9:00 напомни позвонить маме»\n"
    "Сначала укажите свой часовой пояс: /timezone\n"
    "Google Calendar: /calendar — подключить один раз\n"
    "Команды: /help"
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
    "<b>Личный агент — справка</b>\n\n"
    "<b>📋 Задачи</b>\n"
    "Напиши или надиктуй задачу — я создам напоминание.\n"
    "• сообщение — текст в чат\n"
    "• звонок — голосовое в Telegram\n"
    "• на телефон — реальный звонок (Twilio, нужен /phone)\n\n"
    "<b>🎙 Голос</b>\n"
    "Отправь голосовое сообщение — распознаю через Whisper.\n\n"
    "<b>📅 Google Calendar</b>\n"
    "/calendar — подключить (один раз)\n"
    "Новые задачи попадают в календарь автоматически.\n"
    "Выполненные и отменённые — удаляются из календаря.\n"
    "/calendar_sync — отправить активные задачи в Google Calendar\n"
    "/calendar_resync — пересоздать события в Google Calendar\n"
    "/calendar_on · /calendar_off — вкл/выкл синхронизацию\n\n"
    "<b>📞 Телефон</b>\n"
    "/phone +79991234567 — привязать номер для звонков\n\n"
    "<b>📝 Заметки</b>\n"
    "«Заметка: текст» или /note текст\n"
    "/notes — список заметок\n\n"
    "<b>🌐 Переводчик</b>\n"
    "Кнопка «🌐 Переводчик» — автоопределение языка и перевод\n"
    "/translate_off — выйти из режима\n\n"
    "<b>Команды задач</b>\n"
    "/tasks — все активные\n"
    "/tasks_done — завершённые и отменённые\n"
    "/restore &lt;id&gt; — вернуть задачу в активные\n"
    "/done &lt;id&gt; · /cancel &lt;id&gt;\n"
    "/timezone — ваш часовой пояс (у каждого пользователя свой)\n\n"
    "<b>Кнопки при напоминании</b>\n"
    "• Выполнено — убрать из активных и удалить из Google Calendar\n"
    "• Через 15 мин — отложить (задача остаётся)\n"
    "• Отменить — снять задачу и удалить из Google Calendar"
)

TASK_CREATED = (
    "✅ Задача #{task_id} создана\n"
    "<b>{title}</b>\n"
    "⏰ {due_at}\n"
    "🔔 {notify_types}{calendar_line}\n\n"
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
    "⏰ {due_at} · {notify_types}"
)

TASK_DONE = "✅ Задача #{task_id} отмечена выполненной."
TASK_CANCELLED = "🗑 Задача #{task_id} отменена."
TASK_NOT_FOUND = "Задача не найдена или уже завершена."
TASK_ARCHIVED_HEADER = "<b>Завершённые задачи (последние):</b>"
TASK_ARCHIVED_EMPTY = "Нет завершённых или отменённых задач."
TASK_ARCHIVED_ITEM = "#{id} — <b>{title}</b> ({status})\n⏰ {due_at}"
TASK_RESTORED = "↩️ Задача #{task_id} «{title}» снова в активных."

REMINDER_MESSAGE = "⏰ <b>Напоминание</b>\n{title}"
REMINDER_ACTIONS_HINT = (
    "Что сделать с напоминанием?\n"
    "• <b>Выполнено</b> — убрать из активных (событие удалится из Google Calendar)\n"
    "• <b>Через 15 мин</b> — отложить напоминание\n"
    "• <b>Отменить</b> — снять задачу (событие удалится из Google Calendar)"
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
    "Не понял часовой пояс.\n"
    + TIMEZONE_HELP_EXAMPLES
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
    "Отправьте текст или голосовое — определю язык и переведу автоматически.\n"
    "Русский → English, English → русский.\n\n"
    "Выйти: любая другая кнопка меню."
)
TRANSLATE_RESULT = (
    "🌐 <b>{source_lang}</b> → <b>{target_lang}</b>\n\n"
    "<i>{source}</i>\n\n"
    "➡️ {translation}"
)
TRANSLATE_EXIT = "🌐 Переводчик выключен. Возвращайтесь в любое время кнопкой «🌐 Переводчик»."
TRANSLATE_NEED_OPENAI = "Переводчик требует OPENAI_API_KEY в настройках бота."
