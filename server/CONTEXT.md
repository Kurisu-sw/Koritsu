# Koritsu — Контекст проекта

## Что это
Веб-платформа с двумя AI-модулями: **Fragmos** (генерация блок-схем из кода) и **Engrafo** (генерация отчётов из docx-шаблонов). Фронтенд на Reflex (Python), бэкенд на FastAPI, БД — SQLite.

## Стек
- **Frontend**: Reflex (Python → React), TailwindV4, dark theme
- **Backend**: FastAPI + uvicorn (порт 8001)
- **AI**: Yandex Cloud AI Studio SDK (`yandex-ai-studio-sdk`), модель `yandexgpt`
- **БД**: SQLite (`DATABASE_NAME` из .env)
- **Зависимости**: bcrypt, docxtpl, python-docx, drawpyo, openai, reflex, fastapi, httpx, Pillow, python-dotenv

## Запуск
`./start.sh` — запускает Reflex (порт 3000) + uvicorn (порт 8001). Логи в `logs/`, PID в `.pids/`.

---

## Структура файлов

```
server/
  service_api.py    — FastAPI приложение, все API эндпоинты, SQLite, Balancer
  balancer.py       — In-memory очередь задач с приоритетами (0-3), TTL, фоновые воркеры

modules/
  fragmos/
    request.py      — Клиент Yandex AI (генерация, токенизация, биллинг)
    pipeline.py     — Пайплайн: код → AI → .frg → .xml блок-схема
    parser.py       — Парсер .frg формата в список nodes (dict)
    builder.py      — Генератор .xml (drawio) из nodes через drawpyo
    prompts/
      bau.md        — Промпт "Bauman" — дословный перевод кода в .frg
      gu.md         — Промпт "ГОСТ" — перевод в русский псевдокод
    syntax.md       — Спецификация формата .frg

  engrafo/
    template_manager.py  — Загрузка/управление docx-шаблонами (глобальные + личные)
    docx_processor.py    — Подстановка тегов в docx через docxtpl (Jinja2)
    pdf_converter.py     — docx → PDF через LibreOffice headless
    report_manager.py    — Жизненный цикл отчёта: CRUD, версии, финализация
    profile_manager.py   — Именованные наборы значений тегов (JSON на диске)

webapp/reflex/
  rxconfig.py           — Reflex config (app_name="koritsu", TailwindV4)
  koritsu/
    koritsu.py          — Точка входа: регистрация всех страниц и роутов
    theme.py            — Цветовая палитра (BG, PANEL, ACCENT, TEXT, MUTED...)
    components/
      header.py         — Общий navbar: лого, навигация, аватар/меню пользователя
    pages/
      home.py           — Главная: карточки Fragmos/Engrafo, auth модалка, welcome strip
      fragmos.py        — Страница Fragmos: ввод кода, draw.io предпросмотр, чаты
      engrafo.py        — Список отчётов + создание нового
      engrafo_editor.py — Редактор: sidebar (шаблон, теги, профили, версии) + PDF preview
      profile.py        — Профиль: аккаунт, файлы, реферальная программа
      ref_page.py       — Реферальная landing-страница /ref/[ref_code]
      admin_panel.py    — Админка: topology, balancer, управление пользователями
    state/
      auth_state.py     — Авторизация: login/register/logout, localStorage, rate limiting
      fragmos_state.py  — Состояние Fragmos: чаты/схемы, генерация через балансер, настройки
      balancer_state.py — Состояние балансера для админки (список задач, фильтры)
      profile_state.py  — Состояние профиля: редактирование, аватарка, рефералы
      admin_state.py    — Состояние админки: поиск юзеров, CRUD, бан, topology health
      engrafo_state.py  — Состояние Engrafo: шаблоны, теги, preview, профили, версии
```

---

## API эндпоинты (service_api.py, порт 8001)

### Пользователи
| Метод | URL | Что делает |
|-------|-----|------------|
| POST | /register | Регистрация (username, password). Создаёт папки, identicon. +50 токенов |
| POST | /login | Авторизация → uuid |
| GET | /user/{uuid} | Данные пользователя |
| PATCH | /user/{uuid} | Обновить поле (username/password/display_name/tokens_left) |
| POST | /user/{uuid}/avatar | Загрузить аватарку (PNG, макс 2MB) |
| GET | /user/{uuid}/{folder} | Файлы пользователя (fragmos/engrafo) |

### Рефералы
| POST | /user/{uuid}/referral | Создать реф. код |
| GET | /user/{uuid}/referral | Получить реф. данные |
| POST | /register/ref/{ref_uuid} | Регистрация по рефералу |
| GET | /ref/{ref_uuid}/validate | Проверить реф. код |
| GET | /user/{uuid}/referral/details | Список приглашённых |

### Админ (X-Admin-Token header)
| POST | /admin/login | Логин админа (ADMIN_LOGIN/ADMIN_PASSWORD из env) |
| GET | /admin/health | Проверка БД |
| GET | /admin/search?username= | Поиск пользователя |
| POST | /admin/user/{uuid}/ban | Бан (permanent или timeout) |
| POST | /admin/user/{uuid}/unban | Разбан |
| DELETE | /admin/user/{uuid} | Удалить пользователя + файлы |
| POST | /admin/user/{uuid}/reset-password | Сброс пароля |
| PATCH | /admin/user/{uuid}/sub-level | Изменить подписку |

### Балансер (/balancer/)
| POST | /balancer/task | Создать задачу (priority 0-3, task_dest, payload) |
| GET | /balancer/task/{uuid} | Статус задачи |
| GET | /balancer/tasks | Все задачи (админ) |
| DELETE | /balancer/task/{uuid} | Отменить задачу |

### Fragmos
| POST | /fragmos/estimate | Оценка стоимости генерации (код + model_id → токены, рубли) |

### Файлы
`/files/...` — статика из `server/files/`

---

## Базы данных

### SQLite таблица `users`
```
uuid, username, password (bcrypt), created_at, icon, display_name,
sub_level (free/pro/enterprise), sub_expire_date, tokens_left,
is_banned, ban_reason, ban_until, referred_by
```

### SQLite таблица `referrals`
```
id, owner_uuid, ref_uuid (уникальный), created_at, referral_count
```

---

## Файловая структура пользователей
```
server/files/users/{uuid}/
  icon.png                         — аватарка (identicon или загруженная)
  fragmos/                         — XML блок-схемы (Схема_*.xml)
  engrafo/
    templates/                     — личные docx-шаблоны
    reports/{report_id}/
      meta.json, tag_values.json, current.docx, current.pdf
      versions/{vid}/snapshot.docx + meta.json
    profiles/{pid}.json            — сохранённые наборы тегов
```

---

## Fragmos — поток генерации

1. **Фронт** (`fragmos_state.py`): пользователь вводит код → `POST /fragmos/estimate` → проверка баланса
2. **Балансер**: `POST /balancer/task` (priority=2, dest=fragmos) → задача в очередь
3. **Хэндлер** (`service_api._fragmos_handler`): вызывает `pipeline.run()`
4. **Pipeline** (`pipeline.py`):
   - Оценка токенов через Yandex Tokenizer API
   - Генерация .frg через `request.AI_API.generate()` (Yandex GPT с system prompt)
   - Парсинг .frg → nodes через `parser.parse_frg()`
   - Генерация .xml через `builder.generate()`
5. **Фронт**: поллит `/balancer/task/{uuid}` каждые 2 сек → получает xml_content → draw.io iframe

### Модели AI
- `literal` → промпт `bau.md` — дословный перевод кода в .frg
- `gost` → промпт `gu.md` — русский псевдокод по ГОСТ 19.701-90

### Биллинг
- Yandex API: 0.4₽ за 1000 токенов
- Внутренние токены: `yandex_tokens / 100 * 2` (TOKEN_MULTIPLIER=2)
- Регистрация: +50 бесплатных токенов

---

## Engrafo — поток работы

1. Загрузка docx-шаблона (глобальные или личные) с тегами `{{имя_тега}}`
2. Извлечение тегов через `docxtpl.get_undeclared_variables()`
3. Заполнение тегов в sidebar → debounce 500ms → auto-preview
4. Рендер: `docxtpl.render()` → `LibreOffice --headless` → PDF
5. Экспорт: DOCX / PDF, версии (макс 5), профили тегов

---

## Роуты фронтенда

| Роут | Страница | on_load |
|------|----------|---------|
| / | home_page | check_auth_query |
| /fragmos | fragmos_page | refresh_user, FragmosState.on_load |
| /engrafo | engrafo_page | refresh_user, EngrafoState.on_load_list |
| /engrafo/editor | engrafo_editor_page | refresh_user, EngrafoState.on_load_editor |
| /profile | profile_page | refresh_user, load_user_data |
| /profile/files | profile_files_page | refresh_user, load_user_data |
| /profile/referral | profile_referral_page | refresh_user, load_user_data |
| /ref/[ref_code] | ref_page | RefPageState.on_load |
| /sys/d7f3a1b9e2c4 | admin_panel_page | refresh_user, load_tasks, check_topology |

---

## Переменные окружения (.env)
```
DATABASE_NAME     — путь к SQLite файлу
YC_API_KEY        — API ключ Yandex Cloud
YANDEX_PROJECT_ID — folder_id Yandex Cloud
ADMIN_LOGIN       — логин админки
ADMIN_PASSWORD    — пароль админки
FASTAPI_URL       — URL FastAPI (default: http://localhost:8001)
```

---

## Авторизация
- Сессия хранится в `localStorage` (koritsu_uuid)
- Rate limiting: 5 попыток логина → 3 мин cooldown; 5 попыток регистрации → 5 мин cooldown
- Пароль: минимум 12 символов + заглавная + спецсимвол
- Админ: отдельные credentials через env, токен в `X-Admin-Token` header

## Балансер
- In-memory PriorityQueue (min-heap, priority 0-3, 3=highest)
- TTL: priority≥1 → 5 мин, priority=0 → 1 мин
- Max concurrent: 3
- Статусы: pending → running → completed/failed/expired/cancelled
- Фоновый TTL checker каждые 5 сек

## Темизация
Dark theme. Основные цвета в `theme.py`:
- BG: тёмный градиент, PANEL: rgba белый 5%, ACCENT: #3b82f6 (синий)
- TEXT: rgba белый 92%, MUTED: rgba белый 40%
- Шрифт: SF Pro Display / Segoe UI / system-ui

## Известные баги (TODO.md)
- Fragmos: промежуточные файлы не в папке пользователя
- Не списывает токены (частично)
- Завышенная оценка стоимости
- Bauman режим работает некорректно
- IF без тела создаёт лишние блоки "конец"
