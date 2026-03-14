import json


# ═══════════════════════════════════════════════════════════════════════════
# ПАРСЕР JSON-формата .frg
# ═══════════════════════════════════════════════════════════════════════════

_JSON_TYPE_MAP = {
    'S':  'start',
    'E':  'stop',
    'X':  'execute',
    'P':  'process',
    'IO': 'io',
    'LS': 'loop_limit_start',
    'LE': 'loop_limit_end',
    'IF': 'if',
    'W':  'while',
    'F':  'for_default',
}


def parse_frg_json(text, base_cfg=None):
    """
    Парсит JSON-текст .frg файла.
    Возвращает (cfg, nodes) — cfg из DEFAULT_CFG (конфиг задаётся через UI).
    """
    from builder import DEFAULT_CFG
    cfg = dict(base_cfg or DEFAULT_CFG)
    raw = _load_json_repaired(text.strip())
    nodes = _convert_json_nodes(raw)
    return cfg, nodes


def parse_frg_json_file(path, base_cfg=None):
    """Читает .json файл и парсит его."""
    with open(path, encoding='utf-8') as f:
        return parse_frg_json(f.read(), base_cfg)


# ── Восстановление JSON с дублирующимися ключами ─────────────────────────

def _load_json_repaired(text):
    """
    Загружает JSON, исправляя ошибку нейронки: когда два узла случайно
    сливаются в один объект из-за дублирующегося ключа "t".

    Пример бага:
      {"t":"F","c":[...],"t":"E","v":"stop"}
    После исправления:
      {"t":"F","c":[...]}, {"t":"E","v":"stop"}
    """
    def _pairs_hook(pairs):
        seen = set()
        split_at = None
        for i, (k, _) in enumerate(pairs):
            if k == 't' and k in seen:
                split_at = i
                break
            seen.add(k)

        if split_at is None:
            return dict(pairs)

        node1 = dict(pairs[:split_at])
        node2 = dict(pairs[split_at:])
        return {'__split__': [node1, node2]}

    raw = json.loads(text, object_pairs_hook=_pairs_hook)
    return _expand_splits(raw)


def _expand_splits(lst):
    """Рекурсивно разворачивает маркеры __split__ в списках узлов."""
    result = []
    for item in lst:
        if isinstance(item, dict) and '__split__' in item:
            for sub in item['__split__']:
                result.append(_expand_node(sub))
        else:
            result.append(_expand_node(item))
    return result


def _expand_node(node):
    """Рекурсивно обходит узел, разворачивая __split__ во вложенных списках."""
    if not isinstance(node, dict):
        return node
    result = {}
    for k, v in node.items():
        result[k] = _expand_splits(v) if isinstance(v, list) else v
    return result


# ── Конвертация в формат builder ─────────────────────────────────────────

def _convert_json_nodes(raw_list):
    nodes = []
    for item in raw_list:
        t_code = item['t']
        t = _JSON_TYPE_MAP.get(t_code)
        if t is None:
            raise ValueError(f"Неизвестный тип узла: {t_code!r}")
        v = item['v']
        if t == 'if':
            nodes.append({
                'type': 'if',
                'value': v,
                'children':      _convert_json_nodes(item.get('y', [])),
                'else_children': _convert_json_nodes(item.get('n', [])),
            })
        elif t in ('while', 'for_default'):
            nodes.append({
                'type': t,
                'value': v,
                'children': _convert_json_nodes(item.get('c', [])),
            })
        else:
            nodes.append({'type': t, 'value': v})
    return nodes
