import sqlite3 

class Login:
    def __init__(self, db):
        self.db = db
        self.conexion = sqlite3.connect(self.db)
        self.conexion.executescript('''CREATE TABLE IF NOT EXISTS admin
                                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                  usuario TEXT NOT NULL UNIQUE,
                                  password TEXT NOT NULL);
                                CREATE TABLE IF NOT EXISTS users(
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                usuario TEXT NOT NULL UNIQUE,
                                password TEXT NOT NULL);''')
        self.conexion.commit()
        self.conexion.close()

    def verificar_user(self, user: str, password: str, tabla: str):
        self.conexion = sqlite3.connect(self.db)
        cursor = self.conexion.cursor()
        cursor.execute(f"SELECT * FROM {tabla} WHERE usuario = ? AND password = ?", (user, password))
        result = cursor.fetchone()
        self.conexion.close()
        return result is not None
    
    def obtener_tipo_usuario(self, user: str, password: str):
        """Retorna el tipo de usuario (admin/user) o None si no existe"""
        self.conexion = sqlite3.connect(self.db)
        cursor = self.conexion.cursor()
        
        cursor.execute("SELECT * FROM admin WHERE usuario = ? AND password = ?", (user, password))
        if cursor.fetchone():
            self.conexion.close()
            return "admin"
        
        cursor.execute("SELECT * FROM users WHERE usuario = ? AND password = ?", (user, password))
        if cursor.fetchone():
            self.conexion.close()
            return "user"
        
        self.conexion.close()
        return None
    
    def usuario_existe(self, user: str):
        """Verifica si un usuario existe en cualquier tabla"""
        self.conexion = sqlite3.connect(self.db)
        cursor = self.conexion.cursor()
        
        cursor.execute("SELECT * FROM admin WHERE usuario = ?", (user,))
        if cursor.fetchone():
            self.conexion.close()
            return True
        
        cursor.execute("SELECT * FROM users WHERE usuario = ?", (user,))
        if cursor.fetchone():
            self.conexion.close()
            return True
        
        self.conexion.close()
        return False
    
    def agregar_usuario(self, user: str, password: str, tabla: str):
        """Agrega un usuario. Retorna True si es exitoso, False si ya existe"""
        try:
            self.conexion = sqlite3.connect(self.db)
            cursor = self.conexion.cursor()
            cursor.execute(f"INSERT INTO {tabla} (usuario, password) VALUES (?, ?)", (user, password))
            self.conexion.commit()
            self.conexion.close()
            return True
        except sqlite3.IntegrityError:
            self.conexion.close()
            return False
        except Exception as e:
            self.conexion.close()
            return False

    def obtener_usuarios(self, tabla: str):
        self.conexion = sqlite3.connect(self.db)
        cursor = self.conexion.cursor()
        cursor.execute(f"SELECT usuario FROM {tabla}")
        result = cursor.fetchall()
        self.conexion.close()
        return [r[0] for r in result]

    def eliminar_usuario(self, username: str, tabla: str):
        self.conexion = sqlite3.connect(self.db)
        cursor = self.conexion.cursor()
        cursor.execute(f"DELETE FROM {tabla} WHERE usuario = ?", (username,))
        self.conexion.commit()
        self.conexion.close()

class Citas:
    def __init__(self, db_path: str):
        self.db = db_path
        self._inicializar_db()

    def _asegurar_columna(self, conn, tabla, columna, definicion):
        columnas = {row[1] for row in conn.execute(f"PRAGMA table_info({tabla})").fetchall()}
        if columna not in columnas:
            conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")

    def obtener_configuracion(self) -> dict:
        """Obtiene la configuración de citas."""
        with sqlite3.connect(self.db) as conn:
            row = conn.execute("SELECT duracion_cita_minutos, intervalo_minimo_minutos FROM configuracion WHERE id = 1").fetchone()
            if row:
                return {"duracion": row[0], "intervalo": row[1]}
            return {"duracion": 30, "intervalo": 30}

    def actualizar_configuracion(self, duracion: int, intervalo: int) -> bool:
        """Actualiza la configuración de citas."""
        try:
            with sqlite3.connect(self.db) as conn:
                conn.execute(
                    "UPDATE configuracion SET duracion_cita_minutos = ?, intervalo_minimo_minutos = ? WHERE id = 1",
                    (duracion, intervalo)
                )
            return True
        except sqlite3.Error as e:
            print(f"Error actualizando configuración: {e}")
            return False

    def validar_conflicto_horario(self, nombre: str, fecha: str, hora: str) -> tuple[bool, str]:
        """
        Valida si se puede agendar una cita sin conflictos.
        Retorna (válido, mensaje)
        """
        try:
            config = self.obtener_configuracion()
            duracion = config["duracion"]
            intervalo = config["intervalo"]
            
            with sqlite3.connect(self.db) as conn:
                # Convertir hora a minutos
                h, m = map(int, hora.split(':'))
                hora_minutos = h * 60 + m
                
                # Obtener todas las citas de ese día
                citas_dia = conn.execute(
                    "SELECT hora FROM citas WHERE fecha = ? ORDER BY hora",
                    (fecha,)
                ).fetchall()
                
                for (hora_existente,) in citas_dia:
                    h_ex, m_ex = map(int, hora_existente.split(':'))
                    hora_existente_minutos = h_ex * 60 + m_ex
                    
                    # Rango ocupado de la cita existente
                    inicio_existente = hora_existente_minutos
                    fin_existente = hora_existente_minutos + duracion
                    
                    # Rango de la nueva cita
                    inicio_nueva = hora_minutos
                    fin_nueva = hora_minutos + duracion
                    
                    # Verificar solapamiento con intervalo
                    inicio_bloqueado = inicio_existente - intervalo
                    fin_bloqueado = fin_existente + intervalo
                    
                    if not (fin_nueva <= inicio_bloqueado or inicio_nueva >= fin_bloqueado):
                        inicio_disponible = fin_existente + intervalo
                        h_disp = (inicio_disponible // 60) % 24
                        m_disp = inicio_disponible % 60
                        return False, f"Conflicto de horario. Próxima disponibilidad: {h_disp:02d}:{m_disp:02d}"
                
                return True, "OK"
        except Exception as e:
            print(f"Error validando conflicto: {e}")
            return False, f"Error: {str(e)}"


    def _inicializar_db(self):
        try:
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            
            # Crear tabla citas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS citas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    notas TEXT DEFAULT ''
                )
            ''')
            
            # Crear tabla dias_bloqueados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dias_bloqueados (
                    fecha TEXT PRIMARY KEY
                )
            ''')
            
            # Crear tabla configuracion
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configuracion (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    duracion_cita_minutos INTEGER DEFAULT 30,
                    intervalo_minimo_minutos INTEGER DEFAULT 30
                )
            ''')
            
            # Inicializar configuración si no existe
            cursor.execute('''
                INSERT OR IGNORE INTO configuracion (id, duracion_cita_minutos, intervalo_minimo_minutos)
                VALUES (1, 30, 30)
            ''')
            
            conn.commit()
            conn.close()
            print(f"Base de datos {self.db} inicializada correctamente")
        except Exception as e:
            print(f"Error inicializando base de datos: {e}")

    def guardar_cita(self, nombre: str, fecha: str, hora: str, notas: str = "") -> tuple[bool, str]:
        """
        Guarda una cita validando conflictos de horario.
        Retorna (éxito, mensaje)
        """
        # Validar conflicto primero
        valido, mensaje = self.validar_conflicto_horario(nombre, fecha, hora)
        if not valido:
            return False, mensaje
        
        try:
            with sqlite3.connect(self.db) as conn:
                conn.execute(
                    "INSERT INTO citas (nombre, fecha, hora, notas) VALUES (?, ?, ?, ?)",
                    (nombre, fecha, hora, notas.strip() if notas else "")
                )
            return True, "Cita agendada"
        except sqlite3.Error as e:
            print(f"Error guardando cita: {e}")
            return False, f"Error: {str(e)}"

    def obtener_cantidad_citas(self, nombre: str) -> int:
        with sqlite3.connect(self.db) as conn:
            return conn.execute("SELECT COUNT(*) FROM citas WHERE nombre = ?", (nombre,)).fetchone()[0]

    def obtener_citas_mes(self, nombre: str) -> list:
        with sqlite3.connect(self.db) as conn:
            return conn.execute("SELECT fecha, hora, notas FROM citas WHERE nombre = ?", (nombre,)).fetchall()

    def obtener_todas_citas(self) -> list:
        with sqlite3.connect(self.db) as conn:
            rows = conn.execute("SELECT nombre, fecha, hora, notas FROM citas ORDER BY fecha, hora").fetchall()
        return [{"id": i+1, "nombre": r[0], "fecha": r[1], "hora": r[2], "notas": r[3] or "-"} for i, r in enumerate(rows)]

    def obtener_dias_bloqueados(self) -> set:
        with sqlite3.connect(self.db) as conn:
            rows = conn.execute("SELECT fecha FROM dias_bloqueados").fetchall()
        return {r[0] for r in rows}

    def bloquear_dia(self, fecha: str) -> bool:
        try:
            with sqlite3.connect(self.db) as conn:
                conn.execute("INSERT OR IGNORE INTO dias_bloqueados (fecha) VALUES (?)", (fecha,))
            return True
        except sqlite3.Error:
            return False

    def desbloquear_dia(self, fecha: str) -> bool:
        try:
            with sqlite3.connect(self.db) as conn:
                conn.execute("DELETE FROM dias_bloqueados WHERE fecha = ?", (fecha,))
            return True
        except sqlite3.Error:
            return False