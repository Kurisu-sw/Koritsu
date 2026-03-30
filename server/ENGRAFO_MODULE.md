# Engrafo — модуль генерации отчётов

Добавлен в проект Koritsu как новый раздел `/engrafo`.
Дата: 2026-03-26

---

## Что было сделано

### 1. Backend-модули (`modules/engrafo/`)

| Файл | Назначение |
|------|-----------|
| `template_manager.py` | Список шаблонов (глобальных + личных), извлечение тегов через `docxtpl.get_undeclared_variables()` |
| `docx_processor.py` | Подстановка тегов в docx через docxtpl / Jinja2 — автоматически склеивает XML-runs, сохраняет форматирование |
| `pdf_converter.py` | Конвертация docx → PDF через **LibreOffice 7.3 headless** (`subprocess`, timeout 90s) |
| `report_manager.py` | Полный CRUD отчётов: создание, чтение, обновление тегов, удаление, финализация. Версионирование (максимум 5 версий, restore) |
| `profile_manager.py` | Именованные профили значений тегов: create / list / get / delete |

Все модули используют **абсолютные пути** через `os.path.abspath(__file__)` — работают независимо от CWD.

Файлы хранятся в:
```
server/files/
├── global_templates/           ← глобальные .docx (для всех пользователей)
└── users/{uuid}/engrafo/
    ├── templates/              ← личные шаблоны пользователя
    ├── profiles/{pid}.json     ← сохранённые профили
    └── reports/{rid}/
        ├── meta.json
        ├── tag_values.json
        ├── current.docx
        ├── current.pdf
        └── versions/v_TIMESTAMP/
            ├── snapshot.docx
            └── meta.json
```

---

### 2. Reflex State (`webapp/reflex/koritsu/state/engrafo_state.py`)

**Класс `EngrafoState`** управляет:
- Списком шаблонов и отчётов
- Тегами текущего шаблона (`tag_entries: list[dict]`)
- Генерацией PDF preview в фоне (`@rx.background` + `asyncio.to_thread`)
- Профилями и версиями
- `form_key` — инкрементируется при загрузке профиля/версии, чтобы `debounce_input` выполнил ремаунт

Ключевые детали:
- `set_tag_value()` → rebuilds `tag_entries` (list comprehension) → возвращает `generate_preview`
- Debounce 500ms на каждом поле ввода
- Флаг `_preview_in_progress` защищает от параллельных генераций

---

### 3. Reflex-страницы

#### `/engrafo` — список отчётов
- Карточки всех отчётов (открыть / удалить)
- Диалог создания нового отчёта (выбор шаблона + название)
- Диалог загрузки личного шаблона (`rx.upload`)

#### `/engrafo/editor` — редактор
Компоновка: сайдбар (300px) | PDF iframe (flex-grow)

**Сайдбар:**
- Выбор шаблона (dropdown)
- Форма тегов с debounce 500ms
- Профили (загрузить / удалить / сохранить новый)
- История версий (сохранить / восстановить)

**Главная панель:**
- Toolbar: Обновить / Скачать DOCX / Скачать PDF / Завершить
- PDF iframe (`/engrafo-pdf/{uuid}/{rid}?t={ts}`)

---

### 4. Маршруты в `koritsu.py`

```
GET  /engrafo                         → список отчётов
GET  /engrafo/editor                  → редактор
GET  /engrafo-pdf/{uuid}/{rid}        → отдаёт current.pdf (для iframe)
GET  /engrafo-download/{uuid}/{rid}/{pdf|docx}  → скачивание файла
```

PDF-маршруты добавлены в `app.api` (Reflex встроенный FastAPI) — нет CORS-проблем.

---

### 5. Инфраструктура

- **LibreOffice 7.3.7.2** установлен через `apt`
- `requirements.txt` обновлён: добавлен `python-docx`
- Директория `server/files/global_templates/` создана

---

## Как добавить глобальный шаблон

```bash
cp my_template.docx /home/v2rayendmin/Koritsu/server/files/global_templates/
```

Шаблон сразу появится у всех пользователей в выпадающем списке.
Теги в шаблоне должны иметь формат `{{имя_тега}}` (Jinja2 / docxtpl).

---

## Известные ограничения (TODO)

- [ ] Загрузка глобальных шаблонов через UI для admin-пользователей
- [ ] Автосохранение версий по таймеру (сейчас — только ручное)
- [ ] Поддержка сложных тегов: `{{forEach}}`, `{{if}}` (docxtpl поддерживает, нужен UI)
- [ ] Zoom-контроль в PDF preview
- [ ] Подтверждение перед удалением отчёта
