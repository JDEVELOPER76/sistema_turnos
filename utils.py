from datetime import datetime
import calendar
from collections import defaultdict

def construir_calendario_mensual(citas_mes, dias_bloqueados=None):
    hoy = datetime.now()
    year, month = hoy.year, hoy.month
    total_dias = calendar.monthrange(year, month)[1]
    primer_dia = calendar.monthrange(year, month)[0]
    dias_bloqueados = dias_bloqueados or set()

    citas_por_fecha = defaultdict(list)
    for fecha, hora, notas, nombre in citas_mes:
        fecha_limpia = fecha.strip() if fecha else ""
        citas_por_fecha[fecha_limpia].append({
            "hora": hora.strip() if hora else "",
            "notas": notas.strip() if notas else "",
            "nombre": nombre.strip() if nombre else "N/A"
        })

    celdas = [{"vacio": True} for _ in range(primer_dia)]

    for dia in range(1, total_dias + 1):
        fecha_iso = f"{year}-{month:02d}-{dia:02d}"
        citas_dia = sorted(citas_por_fecha.get(fecha_iso, []), key=lambda x: x["hora"])

        if fecha_iso in dias_bloqueados:
            estado = "bloqueado"
        elif len(citas_dia) > 0:
            estado = "ocupado"
        else:
            estado = "disponible"

        celdas.append({
            "vacio": False,
            "dia": dia,
            "fecha": fecha_iso,
            "estado": estado,
            "citas": len(citas_dia),
            "citas_detalle": citas_dia,
        })
    return celdas