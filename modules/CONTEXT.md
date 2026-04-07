# Koritsu — Архитектура и структура проекта

> Документ для использования как контекст в AI-ассистентах.
> Актуален на: **2026-04-02**

---

## Содержание

1. [Общая архитектура](#1-общая-архитектура)
2. [Файловая структура](#2-файловая-структура)
3. [Слои приложения](#3-слои-приложения)
4. [Модуль Engrafo](#4-модуль-engrafo)
5. [Модуль Contextualizer](#5-модуль-contextualizer)
6. [Модуль Fragmos](#6-модуль-fragmos)
7. [Модуль Klassis](#7-модуль-klassis)
8. [Сервер (FastAPI)](#8-сервер-fastapi)
9. [Frontend (Reflex)](#9-frontend-reflex)
10. [Балансер задач](#10-балансер-задач)
11. [База данных](#11-база-данных)
12. [Хранилище файлов](#12-хранилище-файлов)
13. [Аутентификация](#13-аутентификация)
14. [Конфигурация и переменные окружения](#14-конфигурация-и-переменные-окружения)
15. [prompts.yaml — формат и расширение](#15-promptsyaml--формат-и-расширение)

---

## 1. Общая архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                        БРАУЗЕР                              │
│              http://localhost:3000                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ WebSocket + HTTP
┌──────────────────────▼──────────────────────────────────────┐
│              Reflex (Python UI framework)                   │
│         webapp/reflex/  · порт 3000 (фронт)                │
│                         · порт 8002 (бэкенд Reflex)         │
│  Pages: home, engrafo, engrafo_editor, fragmos, admin_panel │
│  State: EngrafoState, FragmosState, AdminState, AuthState   │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP REST
┌──────────────────────▼──────────────────────────────────────┐
│              FastAPI / uvicorn                              │
│         server/service_api.py  · порт 8001                  │
│  Роуты: /register, /login, /user, /admin, /files,           │
│          /contextualizer/*, /balancer/*                     │
└────────┬────────────────────────────┬───────────────────────┘
         │                            │
┌────────▼────────┐          ┌────────▼────────────────────┐
│  modules/       │          │  server/files/              │
│  Engrafo        │          │  SQLite koritsu.db          │
│  Contextualizer │          │  users/{uuid}/…             │
│  Fragmos        │          │  sources/{hash}/…           │
│  Klassis        │          │  global_templates/…         │
└─────────────────┘          └─────────────────────────────┘
```

**Стек:**
- **Frontend**: [Reflex](https://reflex.dev) (Python → React/Next.js)
- **Backend API**: FastAPI + uvicorn
- **БД**: SQLite (один файл `server/files/koritsu.db`)
- **LLM**: OpenAI API / Anthropic API / Yandex GPT (настраивается)
- **OCR**: Tesseract (`rus+eng`)
- **PDF**: LibreOffice (конвертация DOCX→PDF) или unoconv

---

## 2. Файловая структура

```
Koritsu/
├── start.sh                        # Запуск/остановка (reflex + uvicorn)
├── requirements.txt
├── .env                            # Секреты и конфиг (не в git)
│
├── modules/                        # Бизнес-логика (чистый Python)
│   ├── CONTEXT.md                  # ← этот файл
│   ├── engrafo/                    # Работа с DOCX-отчётами
│   ├── contextualizer/             # AI-заполнение тегов из файлов
│   ├── fragmos/                    # Генерация блок-схем из кода
│   ├── klassis/                    # Генерация UML-диаграмм
│   └── prompts/                    # Промпты для Fragmos (bau.md, gu.md)
│
├── server/
│   ├── service_api.py              # FastAPI-приложение
│   ├── balancer.py                 # Очередь асинхронных задач
│   └── files/                      # Все пользовательские данные
│       ├── koritsu.db
│       ├── sources/                # Глобальный кэш загруженных файлов
│       ├── global_templates/       # Системные DOCX-шаблоны
│       └── users/{uuid}/           # Данные пользователя
│
└── webapp/reflex/
    ├── koritsu/
    │   ├── pages/                  # UI-страницы
    │   ├── state/                  # Reflex State-классы
    │   └── components/             # Переиспользуемые компоненты
    └── assets/                     # CSS, JS (engrafo.css, engrafo_editor.js)
```

---

## 3. Слои приложения

| Слой | Путь | Роль |
|------|------|------|
| UI | `webapp/reflex/koritsu/pages/` | Рендеринг страниц через Reflex-компоненты |
| State | `webapp/reflex/koritsu/state/` | Бизнес-логика UI, HTTP-вызовы к API |
| API | `server/service_api.py` | REST endpoints, аутентификация, маршрутизация |
| Modules | `modules/` | Чистая бизнес-логика без зависимостей от UI |
| Storage | `server/files/` | Файловое хранилище + SQLite |

**Важно:** модули в `modules/` не знают о Reflex и FastAPI — это чистые Python-библиотеки. State-классы вызывают их напрямую через `asyncio.to_thread()`.

---

## 4. Модуль Engrafo

**Назначение:** генерация отчётов из DOCX-шаблонов с тегами `{{ключ_тега}}`.

### Файлы

| Файл | Назначение |
|------|-----------|
| `template_manager.py` | CRUD шаблонов; `extract_tags(path)` → список тегов из DOCX |
| `docx_processor.py` | `render_docx(tpl, out, values)` — подставляет теги в шаблон |
| `pdf_converter.py` | `docx_to_pdf(docx, pdf)` — конвертация через LibreOffice |
| `report_manager.py` | CRUD отчётов; хранение `tag_values.json`, версии |
| `profile_manager.py` | Сохранение/загрузка профилей значений тегов |

### Жизненный цикл отчёта

```
1. Пользователь загружает .docx шаблон
   → template_manager.save_template()
   → Теги извлекаются: {{ход_работы}}, {{заключение}} и т.д.

2. Создаётся отчёт
   → report_manager.create_report() → reports/{id}/meta.json

3. Пользователь заполняет теги в редакторе
   → tag_values.json обновляется при каждом изменении (autosave)

4. Генерация превью
   → docx_processor.render_docx() → current.docx
   → pdf_converter.docx_to_pdf()  → current.pdf
   → PDF отдаётся через iframe (StaticFiles /files)

5. Скачать: current.docx или current.pdf
```

### Хранение значения тега

| Тип значения | Формат в `tag_values.json` |
|-------------|---------------------------|
| Простой текст | `"строка текста"` |
| Только картинка | `"data:image/png;base64,..."` |
| Текст + картинка | `"текст<br><img src=\"data:image/...\">"` |
| AI с изображениями | `"__ctx__:{...JSON...}"` (sentinel contextualizer) |

### Глобальные теги пользователя

Хранятся в `users/{uuid}/engrafo/global_tags.json`.
Автоматически подставляются в новые отчёты (ФИО, группа и т.д. которые пользователь задаёт сам).

---

## 5. Модуль Contextualizer

**Назначение:** автоматическое заполнение тегов отчёта из загруженных файлов через LLM.

### Файлы

| Файл | Назначение |
|------|-----------|
| `file_processor.py` | Извлечение текста/OCR из PDF, DOCX, изображений, архивов |
| `db.py` | SQLite-дедупликация источников по SHA-256 хэшу |
| `context_builder.py` | Построение `context.md` и `OCR.md` для отчёта |
| `sequencer.py` | LLM-агент: читает context.md → генерирует steps.md |
| `steps_parser.py` | Парсинг steps.md в структурированный список |
| `steps_applier.py` | Конвертация steps.md → `tag_values.json` |
| `router.py` | FastAPI endpoints `/contextualizer/*` |
| `config.yaml` | Паттерны глобальных переменных, настройки OCR |
| `prompts.yaml` | Промпты по ключам тегов; список `never_generate` |

### Полный pipeline

```
ЗАГРУЗКА ФАЙЛА
│
├─ file_processor.process_upload(filename, bytes)
│    ├─ Определить тип (PDF/DOCX/изображение/архив)
│    ├─ Извлечь текст (pdfplumber / python-docx)
│    ├─ OCR изображений (Tesseract)
│    └─ Рекурсивная обработка архивов (глубина ≤ 3)
│
├─ Сохранить файл в reports/{id}/files/ (per-report)
│
├─ db.save_source(hash, ...) — дедупликация в SQLite
│
└─ context_builder.build_context(user_uuid, report_id, files)
     ├─ Записать context.md в reports/{id}/context.md
     │    ├─ ## Header  — глобальные переменные (номер ЛР, ФИО, группа...)
     │    └─ ## File    — полный текст документа
     └─ Записать OCR.md в reports/{id}/OCR.md
          └─ ## Image entries с путём и распознанным текстом

ГЕНЕРАЦИЯ LLM
│
├─ sequencer.run_sequencer(user_uuid, report_id, tags, custom_prompts)
│    ├─ Прочитать context.md (уровень: global=только Header / full=весь)
│    ├─ Прочитать OCR.md если include_ocr=true
│    ├─ Для каждого тега из tags:
│    │    ├─ Пропустить если тег в never_generate
│    │    ├─ Найти промпт: custom_prompts > prompts_custom.json > prompts.yaml
│    │    └─ Вызвать LLM → получить текст
│    └─ Записать steps.md в reports/{id}/steps.md
│
└─ steps_applier.apply_steps(user_uuid, report_id, tag_order)
     ├─ Парсинг steps.md через steps_parser
     ├─ Назначить номера рисунков глобально
     └─ Обновить tag_values.json
```

### Форматы файлов

**context.md**
```markdown
## Header

| Переменная | Значение |
|---|---|
| Номер ЛР | 3 |
| ФИО | Иванов И.И. |
| Группа | ИС-21 |

## File: имя_файла.pdf
(полный текст документа)
```

**OCR.md**
```markdown
## Image: скриншот1.png
Путь: /path/to/stored/image.png

(распознанный текст изображения)
```

**steps.md** (промежуточный, генерируется LLM)
```yaml
## Tag: ход_работы
content: |
  Текст хода работы...
images:
  - path: /path/to/image.png
    caption: "Рисунок 1 — Схема сети"
    inline_after: "настроена маршрутизация"
options:
  image_align: center
```

### LLM провайдеры

Настраиваются через `.env`:

| Переменная | Описание |
|-----------|---------|
| `LLM_PROVIDER` | `openai` / `anthropic` / `yandex` |
| `LLM_MODEL` | Название модели (gpt-4o, claude-opus-4-6, ...) |
| `OPENAI_API_KEY` | Ключ OpenAI |
| `ANTHROPIC_API_KEY` | Ключ Anthropic |
| `YANDEX_API_KEY` | Ключ Yandex Cloud |
| `YANDEX_FOLDER_ID` | ID папки Yandex Cloud |

---

## 6. Модуль Fragmos

**Назначение:** генерация блок-схем из исходного кода (Python, C++, C#).

### Файлы

| Файл | Назначение |
|------|-----------|
| `parser.py` | Разбор `.frg` формата в список блоков |
| `builder.py` | Построение SVG/XML блок-схемы из блоков |
| `ast_generators/python_ast.py` | AST-анализ Python-кода → .frg |
| `ast_generators/cpp_ast.py` | Анализ C++-кода → .frg |
| `ast_generators/csharp_ast.py` | Анализ C#-кода → .frg |
| `modes/` | Режимы генерации (bau/gu) |
| `syntax.md` | Документация формата .frg |

### Формат .frg

```
START "Начало программы"
EXEC "инициализация переменных"
IF "x > 0"
  YES: EXEC "обработка x"
  NO:  EXEC "x = 0"
LOOP_START "i = 0, n, 1"
  PROCESS "вычисление"
LOOP_END "i"
IO "Вывод: результат"
STOP "Конец"
```

### Режимы (modes)

| Режим | Описание |
|-------|---------|
| `bau` | As-Is — сохраняет оригинальный синтаксис кода |
| `gu` | Перевод на русский псевдокод |

### LLM-промпты

Промпты для перевода кода → .frg лежат в `modules/prompts/`:
- `bau.md` — промпт для as-is режима
- `gu.md` — промпт для режима с русским псевдокодом

---

## 7. Модуль Klassis

**Назначение:** генерация UML class-диаграмм из кода.

### Файлы

| Файл | Назначение |
|------|-----------|
| `extractor.py` | Извлечение классов, методов, полей из кода |
| `builder.py` | Построение UML-диаграммы (XML/draw.io формат) |

---

## 8. Сервер (FastAPI)

**Файл:** `server/service_api.py`
**Порт:** 8001

### Группы endpoints

#### Аутентификация
| Метод | Путь | Описание |
|-------|------|---------|
| POST | `/register` | Регистрация. Создаёт папку пользователя, генерирует identicon |
| POST | `/login` | Проверка пароля (bcrypt) → возвращает `user_uuid` |
| GET | `/user/{uuid}` | Профиль пользователя |
| PATCH | `/user/{uuid}` | Обновить username, display_name, токены |
| POST | `/user/{uuid}/avatar` | Загрузить PNG/JPEG аватар |

#### Администратор
| Метод | Путь | Описание |
|-------|------|---------|
| POST | `/admin/login` | Вход по ADMIN_LOGIN/ADMIN_PASSWORD из `.env` |
| POST | `/admin/verify` | Проверить токен сессии |
| GET | `/admin/health` | Статус компонентов (Reflex, FastAPI, DB, AI) |
| GET | `/admin/search` | Поиск пользователей |
| POST | `/admin/user/{uuid}/ban` | Забанить пользователя |
| DELETE | `/admin/user/{uuid}` | Удалить пользователя |

#### Contextualizer (монтируется через `ctx_router`)
| Метод | Путь | Описание |
|-------|------|---------|
| POST | `/contextualizer/report/{id}/upload` | Загрузить файл контекста |
| POST | `/contextualizer/report/{id}/sequencer/run` | Запустить LLM-генерацию |
| GET | `/contextualizer/report/{id}/steps` | Получить steps.md |
| POST | `/contextualizer/report/{id}/prompt` | Сохранить кастомный промпт |
| POST | `/contextualizer/report/{id}/apply` | Применить steps → tag_values |

#### Балансер
- Задачи регистрируются через `balancer.register_handler(name, fn)`
- Доступны через `/balancer/*` endpoints

#### Статические файлы
- `GET /files/*` → `server/files/` (PDF, изображения, шаблоны)

---

## 9. Frontend (Reflex)

**Директория:** `webapp/reflex/`
**Порт фронтенда:** 3000
**Порт бэкенда Reflex:** 8002

### Страницы

| Файл | Маршрут | Описание |
|------|---------|---------|
| `home.py` | `/` | Главная (ссылки на модули) |
| `engrafo.py` | `/engrafo` | Список отчётов + глобальные теги |
| `engrafo_editor.py` | `/engrafo/editor` | Редактор отчёта с PDF-превью |
| `fragmos.py` | `/fragmos` | Генератор блок-схем |
| `admin_panel.py` | `/sys/d7f3a1b9e2c4` | Панель администратора |
| `profile.py` | `/profile` | Профиль пользователя |
| `ref_page.py` | `/ref` | Реферальная программа |

### State-классы

| Файл | Класс | Управляет |
|------|-------|----------|
| `auth_state.py` | `AuthState` | Сессия пользователя, cookie |
| `engrafo_state.py` | `EngrafoState` | Шаблоны, отчёты, теги, AI, превью |
| `fragmos_state.py` | `FragmosState` | Блок-схемы, код, рендеринг |
| `klassis_state.py` | `KlassisState` | UML-диаграммы |
| `admin_state.py` | `AdminState` | Пользователи, здоровье системы, prompts.yaml |
| `balancer_state.py` | `BalancerState` | Мониторинг очереди задач |
| `profile_state.py` | `ProfileState` | Редактирование профиля |

### Редактор отчёта (engrafo_editor.py)

```
┌──────────────┬──────────────────────────┬──┬───────────────────┐
│   Sidebar    │   Tags Panel             │║│   PDF Preview     │
│  260px       │   flex-grow              │║│   resizable       │
│              │                          │║│                   │
│ • Шаблон     │ [chip] [chip] [chip]     │║│  <iframe PDF>     │
│ • Профили    │                          │║│                   │
│ • Версии     │ ┌─────────────────────┐  │║│                   │
│ • Контекст   │ │ Label тега          │  │║│  [DOCX] [PDF]     │
│   & AI       │ │ [contenteditable]   │  │║│  [Завершить]      │
│              │ └─────────────────────┘  │║│                   │
└──────────────┴──────────────────────────┴──┴───────────────────┘
```

**Особенности редактора:**
- Теги редактируются в `contenteditable div` (поддержка inline-изображений)
- Синхронизация через JS-прокси textarea (`engrafo-html-proxy`)
- Drag-resize между панелями тегов и превью
- Ctrl+V для вставки изображений из буфера

### Модал генерации AI (`_generate_modal`)

```
┌─────────────────────────────────────────────────────────┐
│  ✨ Генерация тегов                                      │
├──────────────────────┬──────────────────────────────────┤
│  Теги (левая панель) │  Настройки (правая панель)       │
│                      │                                  │
│  ☑ ход_работы   ●   │  [AI авто] [Ручной]             │
│  ☑ заключение   ●   │                                  │
│  ☑ цель_работы  ●   │  Поля кастомных промптов        │
│  ☑ вывод        ○   │  для тегов без системного       │
│                      │  промпта (оранжевые)            │
│  ● = есть промпт     │                                  │
│  ○ = нет промпта     │  [✨ Сгенерировать]             │
│                      │  [Отмена]                        │
└──────────────────────┴──────────────────────────────────┘
```

Теги из `never_generate` (prompts.yaml) в модале не отображаются.

---

## 10. Балансер задач

**Файл:** `server/balancer.py`

Простая очередь для тяжёлых асинхронных задач (OCR, LLM).

```python
# Регистрация обработчика
balancer.register_handler("contextualizer", ctx_handler)
balancer.register_handler("fragmos", fragmos_handler)

# Постановка задачи
task_uuid = await balancer.enqueue(
    handler="contextualizer",
    payload={"action": "run_sequencer", ...},
    priority=2,
)

# Polling статуса через Reflex State (BalancerState)
```

**Статусы задач:** `PENDING` → `RUNNING` → `DONE` / `FAIL` / `EXPIRED` / `CANCEL`

**Приоритеты:** 0 (низкий) … 3 (высокий)

---

## 11. База данных

**Файл:** `server/files/koritsu.db` (SQLite)

### Таблица `users`

| Поле | Тип | Описание |
|------|-----|---------|
| `uuid` | TEXT PK | UUID пользователя |
| `username` | TEXT UNIQUE | Логин |
| `password_hash` | TEXT | bcrypt hash |
| `display_name` | TEXT | Отображаемое имя |
| `icon` | TEXT | Путь к аватару |
| `sub_level` | INT | Уровень подписки (0=free) |
| `sub_expire_date` | TEXT | Дата истечения подписки |
| `tokens_left` | INT | Остаток токенов |
| `is_banned` | INT | 0/1 |
| `ban_reason` | TEXT | Причина бана |
| `ban_until` | TEXT | До какого момента забанен |

### Таблица `referrals`

| Поле | Описание |
|------|---------|
| `owner_uuid` | UUID владельца реферальной ссылки |
| `ref_uuid` | UUID реферала (используется в ссылке) |
| `referral_count` | Число активированных рефералов |

### Таблица `source_files`

Глобальный кэш обработанных файлов для дедупликации (contextualizer):

| Поле | Описание |
|------|---------|
| `hash` | SHA-256 файла (PK) |
| `original_filename` | Оригинальное имя |
| `file_type` | pdf / image / docx / archive |
| `stored_path` | Путь к физическому файлу |
| `text_content` | Извлечённый текст |
| `created_at` | Дата добавления |

---

## 12. Хранилище файлов

```
server/files/
├── koritsu.db                          # SQLite
├── sources/                            # Глобальный кэш (contextualizer)
│   └── {sha256_hash}/
│       └── original_file.pdf
├── global_templates/                   # Системные шаблоны DOCX
│   └── Шаблон_отчета.docx
└── users/
    └── {user_uuid}/
        ├── icon.png                    # Аватар (identicon или загруженный)
        ├── fragmos/
        │   └── Схема_{id}.xml         # Блок-схемы
        ├── klassis/
        │   └── Диаграмма_{id}.xml
        └── engrafo/
            ├── global_tags.json        # Глобальные теги пользователя
            ├── prompts_custom.json     # Кастомные промпты уровня пользователя
            ├── templates/
            │   └── {id}.docx          # Загруженные шаблоны
            └── reports/
                └── {report_id}/        # 8-символьный hex ID
                    ├── meta.json       # Метаданные отчёта
                    ├── tag_values.json # Текущие значения тегов
                    ├── current.docx    # Отрендеренный отчёт
                    ├── current.pdf     # PDF-версия
                    ├── context.md      # Извлечённый контекст (для LLM)
                    ├── OCR.md          # OCR изображений
                    ├── steps.md        # Промежуточный вывод LLM
                    ├── ai_context.md   # Контекст для ручного режима
                    ├── prompts_custom.json  # Промпты уровня отчёта
                    ├── files/          # Загруженные файлы контекста
                    │   ├── скриншот.png
                    │   └── лабораторная.pdf
                    └── versions/
                        └── {version_id}.json
```

### meta.json

```json
{
  "id": "a1b2c3d4",
  "title": "Лабораторная работа №3",
  "template_id": "template_uuid",
  "template_name": "Шаблон сети",
  "created_at": "2026-04-01T10:00:00Z",
  "updated_at": "2026-04-02T14:30:00Z",
  "contextualizer": {
    "task_uuid": "...",
    "last_applied_at": "...",
    "sources": ["sha256_hash1", "sha256_hash2"]
  }
}
```

---

## 13. Аутентификация

- **Регистрация:** bcrypt хэш пароля → `users.password_hash`
- **Вход:** сравнение bcrypt → возвращает `user_uuid` как идентификатор сессии
- **Frontend:** `AuthState` хранит `user_uuid` в cookie (Reflex)
- **Admin:** отдельный токен сессии, генерируется при `/admin/login`, хранится в `AdminState`
- **Защита маршрутов:** каждая страница проверяет `AuthState.user_uuid` при `on_load`

---

## 14. Конфигурация и переменные окружения

**Файл:** `.env` (корень проекта)

```env
# LLM
LLM_PROVIDER=openai              # openai | anthropic | yandex
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
YANDEX_API_KEY=AQVN...
YANDEX_FOLDER_ID=b1g...

# Сервер
FASTAPI_URL=http://localhost:8001
DATABASE_NAME=files/koritsu.db

# Администратор
ADMIN_LOGIN=admin
ADMIN_PASSWORD=changeme

# Reflex
REFLEX_ENV=dev
```

**Приоритет конфигурации LLM:**
```
env LLM_MODEL  >  prompts.yaml → llm.model
env LLM_PROVIDER  >  prompts.yaml → llm.provider (если будет)
```

---

## 15. prompts.yaml — формат и расширение

**Путь:** `modules/contextualizer/prompts.yaml`

### Полный формат

```yaml
# Настройки LLM по умолчанию
llm:
  model: "gpt-4o"
  temperature: 0.3
  max_tokens: 2000

# Теги которые НИКОГДА не генерируются AI
# Не отображаются в модале генерации, пропускаются sequencer'ом
never_generate:
  - фио
  - группа
  - дата
  - преподаватель
  # добавляй любые теги с личными данными

# Промпты по ключу тега
# Ключ должен совпадать с {{ключ_тега}} в DOCX-шаблоне
tag_prompts:
  ключ_тега:
    label: "Читаемое название для UI"       # обязательно
    context_level: full                      # full | global
    include_ocr: true                        # true | false
    system: |
      Системный промпт...
    user: |
      Задание для LLM...
```

### context_level

| Значение | Что передаётся LLM |
|---------|-------------------|
| `global` | Только `## Header` из context.md (номер ЛР, ФИО, группа) — экономия токенов |
| `full` | Весь context.md включая полный текст файлов |

### Приоритет промптов

```
1. custom_prompts параметр run_sequencer()    ← наивысший
2. reports/{id}/prompts_custom.json           ← уровень отчёта
3. users/{uuid}/engrafo/prompts_custom.json   ← уровень пользователя
4. modules/contextualizer/prompts.yaml        ← системный
```

Если промпт не найден ни в одном источнике — тег попадает в `needs_prompt` и UI просит пользователя ввести промпт вручную.

### Добавление нового тега в prompts.yaml

```yaml
tag_prompts:
  # Новый тег для раздела "Оборудование"
  оборудование:
    label: "Оборудование и инструменты"
    context_level: full
    include_ocr: false
    system: |
      Ты — технический писатель академических отчётов по сетям и системам.
    user: |
      Перечисли оборудование и программные инструменты, использованные в работе.
      Формат: маркированный список. Объём: 50–100 слов.
```

Тег станет доступен для AI-генерации сразу после сохранения файла (перезапуск не нужен — файл читается при каждом открытии модала генерации).

---

*Последнее обновление: 2026-04-02 · Koritsu v0.1.5+*
