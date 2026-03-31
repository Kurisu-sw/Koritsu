import os
import reflex as rx
from starlette.staticfiles import StaticFiles

from koritsu.pages.home           import home_page
from koritsu.pages.fragmos        import fragmos_page
from koritsu.pages.engrafo        import engrafo_page
from koritsu.pages.engrafo_editor import engrafo_editor_page
from koritsu.pages.profile        import profile_page, profile_files_page, profile_referral_page
from koritsu.pages.ref_page       import ref_page, RefPageState          # noqa: F401
from koritsu.pages.admin_panel    import admin_panel_page

from koritsu.state.fragmos_state  import FragmosState
from koritsu.state.klassis_state  import KlassisState                    # noqa: F401
from koritsu.state.auth_state     import AuthState                       # noqa: F401
from koritsu.state.profile_state  import ProfileState                    # noqa: F401
from koritsu.state.balancer_state import BalancerState                   # noqa: F401
from koritsu.state.admin_state    import AdminState                      # noqa: F401
from koritsu.state.engrafo_state  import EngrafoState                    # noqa: F401

# ── App ────────────────────────────────────────────────────────────────────────
app = rx.App(
    style={
        "font_family": "'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif",
        "background":  "#0a0a0a",
        "margin":      "0",
        "padding":     "0",
    }
)

# ── Pages ──────────────────────────────────────────────────────────────────────

app.add_page(home_page,             route="/",
             on_load=AuthState.check_auth_query)

app.add_page(fragmos_page,          route="/fragmos",
             on_load=[AuthState.do_refresh_user, FragmosState.on_load, KlassisState.on_load])

app.add_page(engrafo_page,          route="/engrafo",
             on_load=[AuthState.do_refresh_user, EngrafoState.on_load_list])

app.add_page(engrafo_editor_page,   route="/engrafo/editor",
             on_load=[AuthState.do_refresh_user, EngrafoState.on_load_editor])

app.add_page(profile_page,          route="/profile",
             on_load=[AuthState.do_refresh_user, ProfileState.load_user_data])

app.add_page(profile_files_page,    route="/profile/files",
             on_load=[AuthState.do_refresh_user, ProfileState.load_user_data])

app.add_page(profile_referral_page, route="/profile/referral",
             on_load=[AuthState.do_refresh_user, ProfileState.load_user_data])

app.add_page(ref_page,              route="/ref/[ref_code]",
             on_load=RefPageState.on_load)

_files_dir = os.path.join(os.path.dirname(__file__), "../../../server/files")
app._api.mount("/files", StaticFiles(directory=os.path.abspath(_files_dir)), name="files")

app.add_page(admin_panel_page,      route="/sys/d7f3a1b9e2c4",
             on_load=[AuthState.do_refresh_user,
                      BalancerState.load_tasks,
                      AdminState.check_topology])
