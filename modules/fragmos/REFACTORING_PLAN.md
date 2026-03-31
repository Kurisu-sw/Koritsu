# 📋 План переработки Fragmos — от исходного кода к блок-схеме

**Дата:** 2026-03-31  
**Статус:** Планирование  
**Область:** modules/fragmos

---

## 🎯 Цель

Переработать систему так, чтобы она работала напрямую с исходным кодом (Python, C#, C++) вместо текущего подхода через Yandex AI и `.frg` формат.

**Новый pipeline:**
```
Исходный код + язык программирования
  ↓
[1] AST генератор (Language-specific)
  ↓
[2] Парсер (Parser) + Табница режимов (YAML)
  ↓
[3] Builder (существующий, без изменений)
  ↓
XML Блок-схема
```

---

## 📁 Новая структура файлов

```
fragmos/
├── ast_generators/          ← [НОВОЕ] AST генераторы для каждого языка
│   ├── __init__.py
│   ├── base.py              ← Базовый класс для всех генераторов
│   ├── python_ast.py        ← Python AST на основе встроенного ast модуля
│   ├── csharp_ast.py        ← C# на основе tree-sitter
│   └── cpp_ast.py           ← C++ на основе tree-sitter
├── modes/                   ← [НОВОЕ] Конфигурация режимов
│   ├── __init__.py
│   └── modes.yaml           ← Таблица соответствия кода → блоков
├── parser.py                ← [ПЕРЕДЕЛАТЬ] Парсит JSON от AST → JSON для Builder
├── builder.py               ← [БЕЗ ИЗМЕНЕНИЙ] Существующий Builder
├── pipeline.py              ← [АРХИВ] Сохраняем, но не используем
├── request.py               ← [АРХИВ] Сохраняем, но не используем
└── REFACTORING_PLAN.md      ← Этот файл
```

---

## 🔧 Компоненты

### 2️⃣ AST генераторы (`ast_generators/`)

**Базовый интерфейс (`base.py`):**
```python
class ASTGenerator:
    """Базовый класс для генераторов AST."""
    
    def generate(self, code: str) -> dict:
        """
        Преобразует исходный код в унифицированный AST.
        
        Возвращает:
        {
            "type": "program|function|class|control_flow",
            "name": "название или пусто",
            "body": [список узлов],
            "metadata": {
                "language": "python|csharp|cpp",
                "ast_version": "1.0",
                "raw_ast": {...}  # оригинальный AST для отладки
            }
        }
        """
        pass
    
    def visit_node(self, node) -> dict:
        """Посещает узел AST и преобразует в унифицированный формат."""
        pass
```

**Унифицированные типы узлов:**
```
- start / stop
- function_def
- class_def
- assignment
- function_call
- control_flow (if, for, while, switch)
- expression
- return
- import
```

#### 2.1 Python AST (`python_ast.py`)

**Использует:** встроенный модуль `ast`

**Особенности:**
- Парсит код через `ast.parse(code)`
- Рекурсивно обходит AST дерево через `ast.NodeVisitor`
- Извлекает типы узлов: FunctionDef, ClassDef, If, For, While, Return и т.д.

**Выход для примера:**
```json
{
  "type": "program",
  "body": [
    {
      "type": "function_def",
      "name": "factorial",
      "body": [
        {
          "type": "control_flow",
          "control_type": "if",
          "condition": "n <= 1",
          "body": [
            {"type": "return", "value": "1"}
          ]
        }
      ]
    }
  ]
}
```

#### 2.2 C# AST (`csharp_ast.py`)

**Использует:** tree-sitter + привязка для C#

**Установка:**
```bash
pip install tree-sitter tree-sitter-languages
```

**Особенности:**
- Парсит через tree-sitter
- Преобразует в унифицированный формат

#### 2.3 C++ AST (`cpp_ast.py`)

**Использует:** tree-sitter + привязка для C++

**Установка:**
```bash
pip install tree-sitter tree-sitter-languages
```

---

### 3️⃣ Парсер (`parser.py`) — ПЕРЕДЕЛКА

**Текущее:** Парсит `.frg` формат от Yandex AI

**Новое:** Парсит JSON от AST генератора + применяет режимы из `modes.yaml`

**Функция:**
```python
def parse_ast_to_flowchart(ast_dict: dict, mode_id: str = "default") -> dict:
    """
    Трансформирует AST в JSON для Builder.
    
    Args:
        ast_dict: {'type': 'program', 'body': [...]}
        mode_id: ID режима из modes.yaml (default, extended, etc.)
    
    Returns:
        cfg (конфигурация для Builder)
        nodes (структура блок-схемы)
    """
```

**Примеры преобразований:**

| AST тип | Mode 1 (default) | Mode 2 (loopLimit) |
|---------|------------------|--------------------|
| `for` | Блок `for_default` (шестиугольник) | Блоки `loop_limit_start` + тело + `loop_limit_end` |
| `while` | Ромб `while` | Блоки `loop_limit_start` + тело + `loop_limit_end` |
| `if/else` | Ромб `if` с YES/NO ветками | Ромб `if` с YES/NO ветками (без изменений) |
| `function_call` | Блок `execute` | Блок `execute` |

**Режим передаётся парсеру:**
```python
parse_ast_to_flowchart(ast_dict, mode_id="loopLimit")
```

---

### 4️⃣ Таблица режимов (`modes/modes.yaml`)

**Зачем:** Сохранить конфиг для ИИ и для парсера.

**Структура:**
```yaml
modes:
  default:
    description: "Стандартный режим: циклы как обычные блоки"
    blocks:
      for:
        type: "for_default"
        display: "шестиугольник"
        generator: "default_for_block"
      while:
        type: "while"
        display: "ромб с возвратом"
      if:
        type: "if"
        display: "ромб с YES/NO ветками"

  loopLimit:
    description: "Режим ограничения цикла: for/while как LOOP_LIMIT"
    blocks:
      for:
        type: "loop_limit_start"
        pair_end: "loop_limit_end"
        display: "овал петли (открывающий)"
        generator: "loop_limit_for_block"
      while:
        type: "loop_limit_start"
        pair_end: "loop_limit_end"
        display: "овал петли (открывающий)"
      if:
        type: "if"
        display: "ромб с YES/NO ветками"
  
  # Можно добавить больше режимов
  nested:
    description: "Режим отображения вложенности"
    blocks:
      for:
        type: "for_default"
```

---

## 📊 JSON структура для Builder

**Текущий вход в Builder (from parser.py):**
```python
nodes = [
    {'type': 'start', 'value': ''},
    {'type': 'execute', 'value': 'int n = 5'},
    {
        'type': 'if',
        'value': 'n > 0',
        'children': [
            {'type': 'execute', 'value': 'print(n)'}
        ],
        'else_children': []
    },
    {'type': 'stop', 'value': ''}
]
```

**Новый парсер будет производить ту же структуру!**

---

## 🔄 Pipeline (новый)

```python
# В server/service_api.py

async def process_code(code: str, language: str, mode_id: str = "default"):
    # 1. Генерировать AST
    ast_gen = get_ast_generator(language)  # Python → PythonAST(), C# → CSharpAST()
    ast_dict = ast_gen.generate(code)
    
    # 2. Парсить AST → JSON для Builder (с режимом)
    cfg, nodes = parse_ast_to_flowchart(ast_dict, mode_id)
    
    # 3. Builder генерирует XML
    xml_path = generate_xml_from_nodes(cfg, nodes)
    
    return xml_path
```

---

## 📝 Поэтапная реализация

### Фаза 1: Основа (Priority HIGH)

- [ ] **ast_generators/base.py** — базовый класс
- [ ] **ast_generators/python_ast.py** — Python AST генератор
- [ ] **modes/modes.yaml** — конфиг режимов (2 режима)
- [ ] **parser.py** — переделать для работы с AST JSON

### Фаза 2: Расширение (Priority MEDIUM)

- [ ] **ast_generators/csharp_ast.py** — C# AST генератор (tree-sitter)
- [ ] **ast_generators/cpp_ast.py** — C++ AST генератор (tree-sitter)
- [ ] Тестирование всех трёх языков

### Фаза 3: Интеграция (Priority MEDIUM)

- [ ] Обновить **service_api.py** для использования нового pipeline`а
- [ ] Обновить фронтенд (webapp) для передачи `mode_id`
- [ ] Архивировать **pipeline.py** и **request.py** (не удалять!)

### Фаза 4: Валидация (Priority LOW)

- [ ] Добавить юнит-тесты для каждого компонента
- [ ] Документация по добавлению новых режимов
- [ ] Примеры использования

---

## 🧪 Примеры использования

### Пример 1: Python код

```python
code = """
def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)
"""

# Новый pipeline (язык передаётся явно)
ast_gen = PythonAST()
ast_dict = ast_gen.generate(code)

cfg, nodes = parse_ast_to_flowchart(ast_dict, mode_id="default")

xml_path = generate_xml_from_nodes(cfg, nodes)
# → /server/files/users/.../fragmos/scheme.xml
```

### Пример 2: Режим переключения

```python
# Режим 1: Циклы как обычные блоки
cfg1, nodes1 = parse_ast_to_flowchart(ast_dict, mode_id="default")

# Режим 2: Циклы как LOOP_LIMIT
cfg2, nodes2 = parse_ast_to_flowchart(ast_dict, mode_id="loopLimit")

# Один и тот же AST → два разных представления!
```

---

## 🎓 Ключевые различия

| Аспект | Было (старое) | Стало (новое) |
|--------|---------------|---------------|
| Вход | Исходный код (текст) | Исходный код (текст) + язык |
| Обработка | Yandex AI генерирует `.frg` | Локально парсим в AST |
| Парсер | Парсит `.frg` текст | Парсит JSON от AST |
| Режимы | Не было | YAML конфиг с таблицей соответствия |
| Языки | Зависело от AI | Python, C#, C++ (расширяемо) |
| Скорость | Медленно (сетевой запрос) | Быстро (локально) |
| Затраты | Yandex токены | ~0 |
| Воспроизводимость | Зависит от AI | Детерминирован |

---

## ⚙️ Зависимости

```
# python_ast — встроен
# tree-sitter для C#/C++
tree-sitter>=0.20
tree-sitter-languages>=1.9.2

# Остальное из текущего requirements.txt
drawpyo
pyyaml
```

---

## 📋 Открытые вопросы

- [ ] Как обрабатывать ошибки парсинга исходного кода?
- [ ] Нужна ли валидация AST перед парсингом?
- [ ] Как обновлять `modes.yaml` без перезапуска?
- [ ] Нужны ли версии режимов (v1, v2)?

---

**Версия плана:** 1.0  
**Автор:** Copilot  
**Согласовано:** ✓
