from playwright.sync_api import expect

NAME = "daridev"
CLINICA = "test hospital"
TELEFONO = "4493402622"
CIUDAD = "hidalgo"
EMAIL = "me@darideveloper.com"
MESSAGE = "this is a periodic check of the contact form. If you STOPPED getting these messages, let me know asap."


def check(page):
    page.goto("https://vetoxzyncomercial.mx/")
    page.locator("#contacto-formulario").scroll_into_view_if_needed()
    page.get_by_role("textbox", name="Nombre").fill(NAME)
    page.get_by_role("textbox", name="Clínica / Hospital").fill(CLINICA)
    page.get_by_role("textbox", name="Teléfono / WhatsApp").fill(TELEFONO)
    page.get_by_role("textbox", name="Ciudad / estado").fill(CIUDAD)
    page.get_by_role("textbox", name="Correo electrónico").fill(EMAIL)
    page.locator("#contacto-formulario").get_by_text("Higiene vinculada al paciente").click()
    page.get_by_text("Correo", exact=True).click()
    page.get_by_text("Quiero informarme más").click()
    page.get_by_role("textbox", name="Mensaje personalizado").fill(MESSAGE)
    page.get_by_role("button", name="Enviar mi solicitud").click()
    expect(page.get_by_text("Gracias — tu mensaje fue registrado")).to_be_visible(timeout=15000)
