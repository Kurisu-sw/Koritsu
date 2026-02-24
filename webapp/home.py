import streamlit as st
from pathlib import Path
from pages.modules import *

PAGES = [
    {"title": "Генератор отчётов",  "desc": "Создавайте Jinja-шаблоны и генерируйте готовые документы автоматически.", "color": "#58a6ff", "page": "pages/Template.py"},
    {"title": "Генератор блоксхем", "desc": "Постройте блок-схему любого процесса с помощью AI за несколько секунд.",  "color": "#a371f7", "page": "pages/SchemeAI.py"},
    {"title": "Баг репорт",         "desc": "Отправить баг репорт",                                                       "color": "#ff7b72", "page": "pages/page3.py"},
]

PLANS = [
    {
        "name": "Beginner", "price": "100 ₽", "period": "в месяц", "accent": "#58a6ff",
        "features": ["1000 UAT Tokens", "Создание блок схем с AI", "Генератор отчетов с AI (максимум 5 в месяц)", "Конвертатор PDF/DOCX"],
        "cta": "Выбрать Beginner", "disabled": False, "badge": "Популярный",
    },
    {
        "name": "Pro", "price": "250 ₽", "period": "в месяц", "accent": "#a371f7",
        "features": ["Всё из Beginner", "3000 UAT Tokens", "Приоритетные AI запросы", "Генератор отчётов с AI агентом (50 в месяц)"],
        "cta": "Выбрать Pro", "disabled": False, "badge": "Выгодно",
    },
    {
        "name": "Support", "price": "500 ₽", "period": "в месяц", "accent": "#ff0000",
        "features": ["Всё из Pro", "6500 UAT Tokens", "БОЛЕЕ приоритетные AI запросы","Генератор отчётов с AI агентом (без ограничений)"],
        "cta": "Выбрать Support", "disabled": False, "badge": "Максимум мощи",
    },
]

TOKEN_PACKS = [
    {"tokens": 500,   "bonus": 0,  "price_per_1k": 150, "label": "500"},
    {"tokens": 1000,  "bonus": 0,  "price_per_1k": 150, "label": "1 000"},
    {"tokens": 2500,  "bonus": 2,  "price_per_1k": 150, "label": "2 500"},
    {"tokens": 5000,  "bonus": 5, "price_per_1k": 150,  "label": "5 000"},
    {"tokens": 10000, "bonus": 10, "price_per_1k": 150,  "label": "10 000"},
    {"tokens": 25000, "bonus": 15, "price_per_1k": 150,  "label": "25 000"},
    {"tokens": 50000, "bonus": 20, "price_per_1k": 150,  "label": "50 000"},
]


def load_css():
    css_path = Path(__file__).parent / "static" / "css" / "home.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def fmt(n):
    return f"{n:,}".replace(",", "\u00a0")


def render_page_cards():
    cards_html = '<div class="cards-grid">'
    for p in PAGES:
        cards_html += (
            f'<a class="page-card" href="?nav={p["page"]}" style="--card-accent:{p["color"]}">'
            f'<div class="spin-border"></div>'
            f'<div class="card-inner">'
            f'<div class="page-card__title">{p["title"]}</div>'
            f'<div class="page-card__desc">{p["desc"]}</div>'
            f'<div class="page-card__arrow">\u2192</div>'
            f'</div></a>'
        )
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)


def render_plan_cards():
    cols = st.columns(3, gap="medium")
    for col, plan in zip(cols, PLANS):
        with col:
            st.markdown(
                f'<div class="plan-card" style="--plan-accent:{plan["accent"]}">'
                f'<div class="spin-border"></div></div>',
                unsafe_allow_html=True,
            )
            with st.container():
                st.markdown(
                    f'<div class="plan-container" style="--plan-accent:{plan["accent"]}">',
                    unsafe_allow_html=True,
                )
                if plan.get("badge"):
                    st.markdown(f'<div class="plan-badge">{plan["badge"]}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="plan-name">{plan["name"]}</div>'
                    f'<div class="plan-price"><div class="plan-amount">{plan["price"]}</div>'
                    f'<div class="plan-period">/{plan["period"]}</div></div>',
                    unsafe_allow_html=True,
                )
                for feature in plan["features"]:
                    if feature:
                        st.markdown(
                            f'<div class="plan-feature">'
                            f'<div class="check-dot" style="background:{plan["accent"]}"></div>'
                            f'{feature}</div>',
                            unsafe_allow_html=True,
                        )
                st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
                btn_disabled = plan["disabled"]
                if st.button(plan["cta"], key=f"plan_{plan['name']}", use_container_width=True, disabled=btn_disabled):
                    st.toast(f"{plan['name']}")
                st.markdown('</div>', unsafe_allow_html=True)


def render_token_purchase():
    # Заголовок секции — отдельный markdown вне контейнера
    st.markdown(
        '<div class="token-header">'
        '<div class="token-title-row">'
        '<span class="token-icon">\u26a1</span>'
        '<span class="token-title">Купить UAT Токены</span>'
        '</div>'
        '<p class="token-subtitle">Пополните баланс в любое время. Чем больше \u2014 тем выгоднее.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Синхронизация слайдера и числового поля
    if "token_val" not in st.session_state:
        st.session_state["token_val"] = 2500

    def _on_slider():
        st.session_state["token_val"] = st.session_state["token_slider"]

    def _on_input():
        v = st.session_state["token_input"]
        st.session_state["token_val"] = max(500, min(50000, round(v / 10) * 10))

    col_slider, col_input = st.columns([5, 1], gap="small")
    with col_slider:
        st.slider(
            label="tokens",
            min_value=500,
            max_value=50000,
            value=st.session_state["token_val"],
            step=10,
            key="token_slider",
            label_visibility="collapsed",
            on_change=_on_slider,
        )
    with col_input:
        st.number_input(
            label="кол-во",
            min_value=500,
            max_value=50000,
            value=st.session_state["token_val"],
            step=10,
            key="token_input",
            label_visibility="collapsed",
            on_change=_on_input,
        )

    base_tokens = st.session_state["token_val"]

    # Вычисления — берём ступень из TOKEN_PACKS по порогу
    pack = TOKEN_PACKS[0]
    for p in TOKEN_PACKS:
        if base_tokens >= p["tokens"]:
            pack = p
    price_per_1k = pack["price_per_1k"]
    bonus_pct    = pack["bonus"]

    bonus_tokens = int(base_tokens * bonus_pct / 100)
    total_tokens = base_tokens + bonus_tokens
    price = max(1, round(base_tokens * price_per_1k / 1000))

    # Чип-подсветка
    selected_idx = TOKEN_PACKS.index(pack)

    # Summary — строим как единую переменную, потом один вызов markdown
    bonus_part = ""
    if bonus_pct > 0:
        bonus_part = (
            '<div class="token-bonus">'
            f'+{bonus_pct}% \u0431\u043e\u043d\u0443\u0441\u00a0\u2014 '
            f'<b>+{fmt(bonus_tokens)}\u00a0\u0442\u043e\u043a\u0435\u043d\u043e\u0432 \u0431\u0435\u0441\u043f\u043b\u0430\u0442\u043d\u043e</b>'
            '</div>'
        )

    summary = (
        '<div class="token-summary">'
          '<div class="token-summary-left">'
            f'<div class="token-summary-amount">{fmt(total_tokens)}\u00a0UAT</div>'
            f'{bonus_part}'
            f'<div class="token-summary-rate">{price_per_1k}\u00a0\u20bd\u00a0/\u00a01\u00a0000\u00a0\u0442\u043e\u043a\u0435\u043d\u043e\u0432</div>'
          '</div>'
          f'<div class="token-summary-price">{fmt(price)}\u00a0\u20bd</div>'
        '</div>'
    )
    st.markdown(summary, unsafe_allow_html=True)

    # Кнопка — нативный виджет
    if st.button("\u26a1 Купить токены", key="buy_tokens"):
        st.toast(f"Переход к оплате {fmt(price)} \u20bd за {fmt(total_tokens)} UAT...")

    # Чипы — всё в одном markdown
    chips = '<div class="token-packs-row">'
    for i, p in enumerate(TOKEN_PACKS):
        cls = "token-pack-chip token-pack-chip--active" if i == selected_idx else "token-pack-chip"
        badge = f'<span class="chip-bonus">+{p["bonus"]}%</span>' if p["bonus"] > 0 else ""
        chips += f'<div class="{cls}">{p["label"]}{badge}</div>'
    chips += '</div>'
    st.markdown(chips, unsafe_allow_html=True)


# ── APP ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Главная", layout="wide", initial_sidebar_state="expanded")
util_sidebar()
load_css()

params = st.query_params
if "nav" in params:
    st.switch_page(params["nav"])

st.markdown(
    '<div class="hero"><h1>Добро пожаловать \U0001f44b</h1>'
    '<p>Выберите инструмент ниже или перейдите через боковое меню.</p>'
    '<div class="hero-divider"></div></div>',
    unsafe_allow_html=True,
)

st.markdown('<p class="section-label">Инструменты</p>', unsafe_allow_html=True)
render_page_cards()
st.markdown('<div style="height:36px"></div>', unsafe_allow_html=True)

st.markdown('<p class="section-label">Подписки</p>', unsafe_allow_html=True)
render_plan_cards()
st.markdown('<div style="height:36px"></div>', unsafe_allow_html=True)

st.markdown('<p class="section-label">Пополнение токенов</p>', unsafe_allow_html=True)
render_token_purchase()