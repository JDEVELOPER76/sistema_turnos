from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse ,JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from data_base import Login, Citas
from clave import CLAVE
from datetime import datetime
from utils import construir_calendario_mensual

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
login = Login("usuarios.db")
citas = Citas("citas.db")
app.add_middleware(SessionMiddleware, secret_key=CLAVE)



@app.exception_handler(500)
def error_500(request: Request, exc):
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)

@app.exception_handler(404)
def error_404(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.get("/")
def inicio(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/login")
def iniciar_sesion_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "mensaje": None, "exito": None})

@app.post("/login")
def iniciar_sesion(request: Request, username: str = Form(...), password: str = Form(...)):
    tipo = login.obtener_tipo_usuario(username, password)
    
    if tipo == "user":
        request.session["username"] = username
        request.session["tipo"] = "user"
        return RedirectResponse(url="/dashboard", status_code=302)
    elif tipo == "admin":
        request.session["username"] = username
        request.session["tipo"] = "admin"
        return RedirectResponse(url="/admin", status_code=302)
    
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "mensaje": "Credenciales inválidas", "exito": False},
        status_code=401,
    )

@app.get("/register")
def registrar_pagina(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "mensaje": None, "exito": None})

@app.post("/register")
def registrar_usuario(request: Request, username: str = Form(...), password: str = Form(...)):
    # Verificar que el nombre no exista en admin
    if login.usuario_existe(username):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "mensaje": "Nombre usado", "exito": False},
            status_code=400,
        )
    
    if login.agregar_usuario(username, password, "users"):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "mensaje": "Registro exitoso", "exito": True},
        )
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "mensaje": "Error al registrar", "exito": False},
        status_code=400,
    )

@app.get("/dashboard")
def dashboard(request: Request):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=302)

    hoy = datetime.now()
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_actual = f"{meses[hoy.month - 1]} {hoy.year}"

    cantidad_citas = citas.obtener_cantidad_citas(username)
    # IMPORTANTE: Necesitamos los datos crudos para el JS
    citas_mes_raw = citas.obtener_citas_mes(username) 
    dias_bloqueados = citas.obtener_dias_bloqueados()

    # Agregar nombre del usuario a cada cita (todas son del usuario actual)
    citas_mes_con_nombre = [(c[0], c[1], c[2], username) for c in citas_mes_raw]
    calendario_mensual = construir_calendario_mensual(citas_mes_con_nombre, dias_bloqueados)

    # Convertimos citas_mes_raw a una lista de diccionarios para el JSON del template
    citas_mes_json = [{"fecha": c[0], "hora": c[1], "notas": c[2], "nombre": username} for c in citas_mes_raw]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "nombre": username,
            "mes_actual": mes_actual,
            "cantidad_citas": cantidad_citas,
            "calendario_mensual": calendario_mensual,
            "citas_mes": citas_mes_json, # <--- Ahora se envía correctamente
            "dias_semana": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
        },
    )

@app.post("/dashboard_save")
async def guardar_cita(
    request: Request,
    fecha: str = Form(...),
    hora: str = Form(...),
    notas: str = Form(""),
):
    username = request.session.get("username")
    if not username:
        return JSONResponse(status_code=403, content={"error": "No autorizado"})

    exito, mensaje = citas.guardar_cita(username, fecha.strip(), hora.strip(), notas.strip())
    if exito:
        return JSONResponse(content={"status": "success", "message": mensaje})
    
    return JSONResponse(status_code=400, content={"status": "error", "message": mensaje})

@app.get("/admin")
def panel_admin(request: Request):
    username = request.session.get("username")
    tipo = request.session.get("tipo")
    if not username or tipo != "admin":
        return RedirectResponse(url="/login", status_code=302)

    hoy = datetime.now()
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    usuarios = login.obtener_usuarios("users")
    us = [{"id": i+1, "username": u} for i, u in enumerate(usuarios)]
    citas_todas = citas.obtener_todas_citas()
    dias_bloqueados = citas.obtener_dias_bloqueados()
    config = citas.obtener_configuracion()
    
    # Convertir diccionarios a tuplas para construir_calendario_mensual
    citas_para_calendario = [(c["fecha"], c["hora"], c["notas"], c["nombre"]) for c in citas_todas]
    calendario = construir_calendario_mensual(citas_para_calendario, dias_bloqueados)

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "total_usuarios": len(usuarios),
        "total_citas": len(citas_todas),
        "dias_bloqueados_count": len(dias_bloqueados),
        "usuarios": us,
        "citas_todas": citas_todas,
        "mes_actual": f"{meses[hoy.month - 1]} {hoy.year}",
        "calendario_mensual": calendario,
        "dias_semana": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
        "duracion_cita": config["duracion"],
        "intervalo_minimo": config["intervalo"]
    })

@app.post("/admin/toggle_day")
async def toggle_dia_admin(request: Request, fecha: str = Form(...), estado: str = Form(...)):
    if request.session.get("tipo") != "admin":
        return {"error": "No autorizado"}, 403

    fecha = fecha.strip()
    if estado == "bloqueado":
        citas.bloquear_dia(fecha)
    else:
        citas.desbloquear_dia(fecha)
    return {"status": "ok"}

@app.post("/admin/delete_user")
async def eliminar_usuario(request: Request, username: str = Form(...)):
    if request.session.get("tipo") != "admin":
        return RedirectResponse(url="/login", status_code=302)
    login.eliminar_usuario(username, "users")
    return RedirectResponse(url="/admin", status_code=302)

@app.get("/admin/config")
async def obtener_config_admin(request: Request):
    if request.session.get("tipo") != "admin":
        return JSONResponse(status_code=403, content={"error": "No autorizado"})
    
    config = citas.obtener_configuracion()
    return JSONResponse(content=config)

@app.post("/admin/config")
async def actualizar_config_admin(request: Request, duracion: int = Form(...), intervalo: int = Form(...)):
    if request.session.get("tipo") != "admin":
        return JSONResponse(status_code=403, content={"error": "No autorizado"})
    
    # Validaciones básicas
    if duracion < 15 or intervalo < 0:
        return JSONResponse(status_code=400, content={"error": "Valores inválidos"})
    
    if citas.actualizar_configuracion(duracion, intervalo):
        return JSONResponse(content={"status": "ok", "message": "Configuración actualizada"})
    
    return JSONResponse(status_code=400, content={"error": "Error al actualizar"})