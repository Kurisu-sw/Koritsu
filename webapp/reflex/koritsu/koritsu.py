import reflex as rx

from koritsu.pages.home import home_page
from koritsu.pages.fragmos import fragmos_page
from koritsu.pages.engrafo import engrafo_page
from koritsu.state.fragmos_state import FragmosState
from koritsu.state.auth_state import AuthState  # noqa: F401

app = rx.App(
    style={
        "font_family": "'Segoe UI', system-ui, sans-serif",
        "background": "#0d1117",
        "margin": "0",
        "padding": "0",
    }
)

app.add_page(home_page,    route="/")
app.add_page(fragmos_page, route="/fragmos", on_load=[AuthState.do_refresh_user, FragmosState.on_load])
app.add_page(engrafo_page, route="/engrafo")
