from playwright.sync_api import expect

NAME = "daridev"
CLINICA = "test hospital"
TELEFONO = "4493402622"
CIUDAD = "hidalgo"
EMAIL = "me@darideveloper.com"
MESSAGE = "this is a periodic check of the contact form. If you STOPPED getting these messages, let me know asap."


def check(page):
    page.goto("https://vetoxzyncomercial.mx/dr-resultados")
    page.locator("#contacto-name").scroll_into_view_if_needed()
    page.locator("#contacto-name").fill(NAME)
    page.locator("#contacto-clinica").fill(CLINICA)
    page.locator("#contacto-telefono").fill(TELEFONO)
    page.locator("#contacto-ciudad-estado").fill(CIUDAD)
    page.locator("#contacto-email").fill(EMAIL)
    page.locator("#contacto-linea-topico").check()
    page.locator("#contacto-medio-contacto-correo").check()
    page.locator("#contacto-motivo-interes-informacion").check()
    page.locator("#contacto-message").fill(MESSAGE)
    page.locator("#contacto-acepta-aviso").check()
    page.locator("form button[type=submit]", has_text="Enviar mi solicitud").click()
    expect(page.get_by_text("Gracias — tu mensaje fue registrado")).to_be_visible(timeout=15000)
