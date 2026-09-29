from playwright.sync_api import expect

NAME = "daridev"
EMAIL = "me@darideveloper.com"
MESSAGE = "this is a periodic check of the contact form. If you STOPPED getting these messages, let me know asap."


def check(page):
    page.goto("https://granadago.com/")
    page.get_by_role("link", name="Contacto").click()
    page.get_by_role("textbox", name="Nombre").fill(NAME)
    page.get_by_role("textbox", name="Correo electrónico").fill(EMAIL)
    page.get_by_role("textbox", name="Mensaje").fill(MESSAGE)
    page.get_by_role("button", name="Enviar").click()
    expect(page.locator("#srfm-success-message-page-327")).to_be_visible(timeout=15000)
