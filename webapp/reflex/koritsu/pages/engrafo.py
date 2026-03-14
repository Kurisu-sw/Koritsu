import reflex as rx


def engrafo_page() -> rx.Component:
    return rx.box(
        rx.text("Engrafo", color="white"),
        background="#0d1117",
        min_height="100vh",
    )
