import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import datetime
import time

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="Quiniela Mundial 2026 - Master Edition", page_icon="🏆", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #f1f5f9; }

    .main-title { text-align: center; color: #1e3a8a; font-size: 3.5rem; font-weight: 900; margin-bottom: 10px; letter-spacing: -1px; }
    .subtitle { text-align: center; color: #64748b; font-size: 1.2rem; margin-bottom: 40px; }

    .reglas-container { background: white; padding: 25px; border-radius: 20px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 30px; border-top: 5px solid #3b82f6; }
    .regla-item { display: inline-block; margin: 0 20px; font-weight: 700; color: #1e40af; }

    .match-card { background: white; padding: 30px; border-radius: 25px; margin-bottom: 25px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); transition: transform 0.2s; border: 1px solid #f1f5f9; }
    .match-card:hover { transform: translateY(-5px); }
    .match-card-cerrado { background: #f8fafc; padding: 30px; border-radius: 25px; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 2px solid #e2e8f0; opacity: 0.85; }

    .grupo-header { background: #1e3a8a; color: white; padding: 15px 30px; border-radius: 15px; margin: 40px 0 20px 0; font-size: 1.5rem; font-weight: 800; display: flex; justify-content: space-between; align-items: center; }

    .res-fijo { font-size: 2.5rem; font-weight: 900; color: #1e3a8a; text-align: center; background: #f8fafc; padding: 20px; border-radius: 15px; border: 3px solid #e2e8f0; min-width: 80px; }
    .res-empate { font-size: 2.5rem; font-weight: 900; color: #d97706; text-align: center; background: #fffbeb; padding: 20px; border-radius: 15px; border: 3px solid #fcd34d; min-width: 80px; }
    .label-equipo { font-size: 0.8rem; color: #94a3b8; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
    .vs-text { font-size: 1.5rem; font-weight: 900; color: #cbd5e1; text-align: center; margin-top: 40px; }
    .empate-badge { background: #fef3c7; color: #92400e; font-size: 0.75rem; font-weight: 700; padding: 4px 10px; border-radius: 20px; border: 1px solid #fcd34d; text-align: center; margin-top: 6px; }
    .cerrado-badge { background: #fee2e2; color: #991b1b; font-size: 0.75rem; font-weight: 700; padding: 4px 10px; border-radius: 20px; border: 1px solid #fca5a5; text-align: center; margin-top: 6px; }
    .sin-apuesta { font-size: 1rem; color: #ef4444; font-weight: 700; text-align: center; margin-top: 10px; }

    .stDataFrame { background: white; padding: 10px; border-radius: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def conectar_db():
    return sqlite3.connect('quiniela_2026_pro_v5.db', check_same_thread=False)

def inicializar_db():
    conn = conectar_db()
    c = conn.cursor()

    c.execute('CREATE TABLE IF NOT EXISTS usuarios (username TEXT PRIMARY KEY, password TEXT, fecha_registro TEXT, bloqueado INTEGER DEFAULT 0)')
    # Migración: agrega bloqueado si la BD ya existía sin la columna
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN bloqueado INTEGER DEFAULT 0")
        conn.commit()
    except:
        pass

    c.execute('''CREATE TABLE IF NOT EXISTS apuestas (
        usuario    TEXT,
        partido_id TEXT,
        g1         INTEGER,
        g2         INTEGER,
        es_empate  INTEGER DEFAULT 0,
        fecha      TEXT,
        UNIQUE(usuario, partido_id)
    )''')
    # Migración: agrega es_empate si la BD ya existía sin ella
    try:
        c.execute("ALTER TABLE apuestas ADD COLUMN es_empate INTEGER DEFAULT 0")
        conn.commit()
    except:
        pass

    c.execute('CREATE TABLE IF NOT EXISTS resultados_reales (partido_id TEXT PRIMARY KEY, r1 INTEGER, r2 INTEGER)')

    # Estado por GRUPO (cierre masivo manual del admin)
    c.execute('CREATE TABLE IF NOT EXISTS estados_grupos (grupo_id TEXT PRIMARY KEY, estado TEXT)')
    for g in [chr(i) for i in range(65, 77)]:
        c.execute("INSERT OR IGNORE INTO estados_grupos VALUES (?, 'abierto')", (g,))

    # Estado por PARTIDO (se cierra automáticamente al publicar resultado)
    c.execute('CREATE TABLE IF NOT EXISTS estados_partidos (partido_id TEXT PRIMARY KEY, estado TEXT)')

    conn.commit()
    conn.close()

def partido_esta_cerrado(conn, partido_id):
    """
    Un partido está cerrado si:
      1. Su grupo está cerrado (cierre masivo del admin), O
      2. El partido específico tiene resultado publicado (cierre automático)
    """
    grupo_id = partido_id.split("_")[0]
    est_grupo = conn.execute(
        "SELECT estado FROM estados_grupos WHERE grupo_id=?", (grupo_id,)
    ).fetchone()[0]
    if est_grupo == 'cerrado':
        return True

    est_partido = conn.execute(
        "SELECT estado FROM estados_partidos WHERE partido_id=?", (partido_id,)
    ).fetchone()
    if est_partido and est_partido[0] == 'cerrado':
        return True

    return False

inicializar_db()

# --- 3. LÓGICA DE PUNTUACIÓN ---
def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def calcular_puntos(g1, g2, r1, r2):
    """
    3 pts → marcador exacto (g1==r1 y g2==r2)
    2 pts → ganador/perdedor correcto
    1 pt  → empate correcto: usuario apostó marcadores iguales (g1==g2)
             y el resultado real también es empate (r1==r2).
             El número específico no importa: 0-0, 1-1, 2-2... todos valen 1 pt.
    0 pts → ninguna de las anteriores
    """
    if g1 == r1 and g2 == r2:
        return 3
    if (g1 > g2 and r1 > r2) or (g1 < g2 and r1 < r2):
        return 2
    if g1 == g2 and r1 == r2:
        return 1
    return 0

def calcular_ranking_global():
    conn = conectar_db()
    df_users    = pd.read_sql("SELECT username FROM usuarios WHERE username != 'Miguel'", conn)
    df_apuestas = pd.read_sql("SELECT * FROM apuestas WHERE usuario != 'Miguel'", conn)
    df_reales   = pd.read_sql("SELECT * FROM resultados_reales", conn)
    conn.close()

    ranking = {u: {"Puntos Totales": 0, "🎯 Exactos": 0, "🏆 Ganadores": 0, "🤝 Empates": 0}
               for u in df_users['username']}

    for _, ap in df_apuestas.iterrows():
        res_real = df_reales[df_reales['partido_id'] == ap['partido_id']]
        if not res_real.empty and ap['usuario'] in ranking:
            r1, r2 = int(res_real.iloc[0]['r1']), int(res_real.iloc[0]['r2'])
            g1, g2 = int(ap['g1']), int(ap['g2'])
            pts = calcular_puntos(g1, g2, r1, r2)
            ranking[ap['usuario']]["Puntos Totales"] += pts
            if pts == 3:   ranking[ap['usuario']]["🎯 Exactos"]   += 1
            elif pts == 2: ranking[ap['usuario']]["🏆 Ganadores"] += 1
            elif pts == 1: ranking[ap['usuario']]["🤝 Empates"]   += 1

    rows = [{"Usuario": u, **v} for u, v in ranking.items()]
    df_final = pd.DataFrame(rows)
    if df_final.empty:
        return pd.DataFrame(columns=["Usuario", "Puntos Totales", "🎯 Exactos", "🏆 Ganadores", "🤝 Empates"])
    return df_final.sort_values(by="Puntos Totales", ascending=False)

def generar_tabla_posiciones(grupo_id, lista_equipos):
    conn = conectar_db()
    df_res = pd.read_sql("SELECT * FROM resultados_reales WHERE partido_id LIKE ?",
                         conn, params=(f"{grupo_id}_%",))
    conn.close()

    stats = {e: {"PJ": 0, "G": 0, "E": 0, "P": 0, "GF": 0, "GC": 0, "DG": 0, "Pts": 0}
             for e in lista_equipos}
    indices_partidos = [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]

    for i, (idx1, idx2) in enumerate(indices_partidos):
        match = df_res[df_res['partido_id'] == f"{grupo_id}_{i}"]
        if not match.empty:
            r1, r2 = int(match.iloc[0]['r1']), int(match.iloc[0]['r2'])
            e1, e2 = lista_equipos[idx1], lista_equipos[idx2]
            for e, g_f, g_c in [(e1, r1, r2), (e2, r2, r1)]:
                stats[e]["PJ"] += 1
                stats[e]["GF"] += g_f
                stats[e]["GC"] += g_c
                if g_f > g_c:    stats[e]["Pts"] += 3; stats[e]["G"] += 1
                elif g_f == g_c: stats[e]["Pts"] += 1; stats[e]["E"] += 1
                else:            stats[e]["P"] += 1
                stats[e]["DG"] = stats[e]["GF"] - stats[e]["GC"]

    return pd.DataFrame.from_dict(stats, orient='index').sort_values(
        by=["Pts", "DG", "GF"], ascending=False)

# --- 4. DATOS DEL MUNDIAL (48 EQUIPOS, 12 GRUPOS) ---
banderas = {
    "México": "mx", "Sudáfrica": "za", "Corea del Sur": "kr", "República Checa": "cz",
    "Canadá": "ca", "Bosnia": "ba", "Catar": "qa", "Suiza": "ch",
    "Brasil": "br", "Marruecos": "ma", "Haití": "ht", "Escocia": "gb-sct",
    "Estados Unidos": "us", "Paraguay": "py", "Australia": "au", "Turquía": "tr",
    "Alemania": "de", "Curazao": "cw", "Costa de Marfil": "ci", "Ecuador": "ec",
    "Países Bajos": "nl", "Japón": "jp", "Suecia": "se", "Túnez": "tn",
    "Bélgica": "be", "Egipto": "eg", "Irán": "ir", "Nueva Zelanda": "nz",
    "España": "es", "Arabia Saudita": "sa", "Cabo Verde": "cv", "Uruguay": "uy",
    "Francia": "fr", "Senegal": "sn", "Irak": "iq", "Noruega": "no",
    "Argentina": "ar", "Argelia": "dz", "Austria": "at", "Jordania": "jo",
    "Portugal": "pt", "RD Congo": "cd", "Uzbekistán": "uz", "Colombia": "co",
    "Inglaterra": "gb-eng", "Ghana": "gh", "Croacia": "hr", "Panamá": "pa",
}

grupos = {
    "A": ["México",         "Sudáfrica",      "Corea del Sur",   "República Checa"],
    "B": ["Canadá",         "Bosnia",         "Catar",           "Suiza"],
    "C": ["Brasil",         "Marruecos",      "Haití",           "Escocia"],
    "D": ["Estados Unidos", "Paraguay",       "Australia",       "Turquía"],
    "E": ["Alemania",       "Curazao",        "Costa de Marfil", "Ecuador"],
    "F": ["Países Bajos",   "Japón",          "Suecia",          "Túnez"],
    "G": ["Bélgica",        "Egipto",         "Irán",            "Nueva Zelanda"],
    "H": ["España",         "Arabia Saudita", "Cabo Verde",      "Uruguay"],
    "I": ["Francia",        "Senegal",        "Irak",            "Noruega"],
    "J": ["Argentina",      "Argelia",        "Austria",         "Jordania"],
    "K": ["Portugal",       "RD Congo",       "Uzbekistán",      "Colombia"],
    "L": ["Inglaterra",     "Ghana",          "Croacia",         "Panamá"],
}

# --- 5. SESIÓN ---
if 'user' not in st.session_state:
    st.session_state.user = None

# --- CABECERA ---
st.markdown('<h1 class="main-title">MUNDIAL 2026 PRO</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Sistema de Gestión de Quinielas y Resultados Oficiales</p>', unsafe_allow_html=True)
st.markdown("""
<div class="reglas-container">
    <div style="text-align:center">
        <span class="regla-item">🎯 EXACTO: 3 PTS</span>
        <span class="regla-item">🏆 GANADOR: 2 PTS</span>
        <span class="regla-item">🤝 EMPATE: 1 PT</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 6. LOGIN / REGISTRO ---
if not st.session_state.user:
    _, col_log, _ = st.columns([1, 1.5, 1])
    with col_log:
        st.markdown('<div style="background:white; padding:40px; border-radius:25px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25)">', unsafe_allow_html=True)
        opcion = st.radio("Acceso al Sistema", ["Ingresar", "Registrarse"], horizontal=True)

        if opcion == "Ingresar":
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.button("ACCEDER", use_container_width=True):
                if u == "Miguel" and p == "2026mundial":
                    st.session_state.user = "Miguel"; st.rerun()
                else:
                    conn = conectar_db(); c = conn.cursor()
                    c.execute("SELECT password, bloqueado FROM usuarios WHERE username=?", (u,))
                    row = c.fetchone(); conn.close()
                    if row and row[0] == hash_pass(p):
                        if row[1] == 1:
                            st.error("❌ Tu cuenta está bloqueada. Contacta al administrador.")
                        else:
                            st.session_state.user = u; st.rerun()
                    else:
                        st.error("Credenciales inválidas")
        else:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Contraseña", type="password")
            if st.button("CREAR CUENTA", use_container_width=True):
                if not nu.strip():
                    st.error("El nombre de usuario no puede estar vacío.")
                elif not np.strip():
                    st.error("La contraseña no puede estar vacía.")
                elif nu.strip().lower() == "miguel":
                    st.error("Ese nombre de usuario está reservado.")
                else:
                    conn = conectar_db(); c = conn.cursor()
                    try:
                        # Verificar si ya existe antes de intentar insertar
                        existe = c.execute(
                            "SELECT 1 FROM usuarios WHERE username=?", (nu.strip(),)
                        ).fetchone()
                        if existe:
                            st.error(f"El usuario '{nu.strip()}' ya está registrado. Elige otro nombre.")
                        else:
                            c.execute("INSERT INTO usuarios VALUES (?,?,?,?)",
                                      (nu.strip(), hash_pass(np), str(datetime.datetime.now()), 0))
                            conn.commit()
                            st.success(f"¡Cuenta creada exitosamente! Bienvenido, {nu.strip()}.")
                            time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"Error al crear la cuenta: {e}")
                    finally:
                        conn.close()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. PANEL PRINCIPAL ---
else:
    with st.sidebar:
        st.markdown(f"### 🏟️ Estadio de {st.session_state.user}")
        if st.button("🔄 Refrescar Todo", use_container_width=True): st.rerun()
        if st.button("🚪 Salir del Sistema", use_container_width=True):
            st.session_state.user = None; st.rerun()
        st.divider()
        st.info("Los partidos se bloquean automáticamente cuando el admin publica el resultado.")

    # =================================================================
    # PANEL USUARIO NORMAL
    # =================================================================
    if st.session_state.user != "Miguel":
        t_pronos, t_equipos, t_ranking = st.tabs(
            ["📝 MIS PRONÓSTICOS", "📊 POSICIONES EQUIPOS", "🌟 CLASIFICACIÓN"])

        # ---- TAB: PRONÓSTICOS ----
        with t_pronos:
            conn = conectar_db()
            for g_id, eqs in grupos.items():
                est_grupo = conn.execute(
                    "SELECT estado FROM estados_grupos WHERE grupo_id=?", (g_id,)
                ).fetchone()[0]

                st.markdown(f"""
                <div class="grupo-header">
                    <span>GRUPO {g_id}</span>
                    <span style="font-size:1rem; opacity:0.8">
                        {'🔒 CERRADO' if est_grupo == 'cerrado' else '🔓 ABIERTO'}
                    </span>
                </div>
                """, unsafe_allow_html=True)

                for idx, (p1, p2) in enumerate([(0,1),(2,3),(0,2),(1,3),(0,3),(1,2)]):
                    pid = f"{g_id}_{idx}"
                    t_local, t_visit = eqs[p1], eqs[p2]

                    # Partido cerrado si grupo cerrado O resultado ya publicado
                    cerrado = partido_esta_cerrado(conn, pid)

                    apuesta = conn.execute(
                        "SELECT g1, g2, es_empate FROM apuestas WHERE usuario=? AND partido_id=?",
                        (st.session_state.user, pid)
                    ).fetchone()

                    resultado_real = conn.execute(
                        "SELECT r1, r2 FROM resultados_reales WHERE partido_id=?", (pid,)
                    ).fetchone()

                    card_class = "match-card-cerrado" if cerrado else "match-card"
                    st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

                    # ── Inputs ANTES de las columnas para evitar NameError con g2 ──
                    if not cerrado and not apuesta:
                        col_pre1, col_pre2 = st.columns(2)
                        g1 = col_pre1.number_input(f"⚽ Goles {t_local}",  0, 15, value=0, key=f"g1_{pid}")
                        g2 = col_pre2.number_input(f"⚽ Goles {t_visit}", 0, 15, value=0, key=f"g2_{pid}")

                    c_loc, c_vs, c_vis = st.columns([4, 2, 4])

                    # ---- LOCAL ----
                    with c_loc:
                        st.markdown('<p class="label-equipo">Local</p>', unsafe_allow_html=True)
                        st.image(f"https://flagcdn.com/w160/{banderas[t_local]}.png", width=70)
                        st.subheader(t_local)
                        if apuesta:
                            css = "res-empate" if apuesta[2] == 1 else "res-fijo"
                            st.markdown(f'<div class="{css}">{apuesta[0]}</div>', unsafe_allow_html=True)
                        elif cerrado:
                            st.markdown('<div class="sin-apuesta">Sin apuesta</div>', unsafe_allow_html=True)

                    # ---- CENTRO ----
                    with c_vs:
                        st.markdown('<p class="vs-text">VS</p>', unsafe_allow_html=True)

                        if not cerrado and not apuesta:
                            # BOTÓN GUARDAR
                            if st.button("💾 GUARDAR", key=f"btn_{pid}",
                                         use_container_width=True,
                                         help="Guarda el marcador que pusiste"):
                                conn.execute(
                                    "INSERT INTO apuestas VALUES (?,?,?,?,?,?)",
                                    (st.session_state.user, pid, g1, g2, 0,
                                     str(datetime.datetime.now()))
                                )
                                conn.commit(); st.rerun()

                            # BOTÓN EMPATE
                            if st.button("🤝 EMPATE", key=f"btn_emp_{pid}",
                                         use_container_width=True,
                                         help="Apuesta a empate. Ganas 1 pt si el resultado es cualquier empate."):
                                conn.execute(
                                    "INSERT INTO apuestas VALUES (?,?,?,?,?,?)",
                                    (st.session_state.user, pid, g1, g1, 1,
                                     str(datetime.datetime.now()))
                                )
                                conn.commit(); st.rerun()

                        elif apuesta and apuesta[2] == 1:
                            st.markdown('<div class="empate-badge">🤝 EMPATE apostado</div>', unsafe_allow_html=True)

                        # Resultado oficial publicado
                        if resultado_real:
                            st.markdown(f"""
                            <div style="text-align:center; margin-top:10px; font-size:0.75rem;
                                        color:#16a34a; font-weight:700;">
                                ✅ RESULTADO OFICIAL<br>
                                <span style="font-size:1.8rem; font-weight:900;">
                                    {resultado_real[0]} - {resultado_real[1]}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        elif cerrado:
                            st.markdown('<div class="cerrado-badge">🔒 Partido cerrado</div>', unsafe_allow_html=True)

                    # ---- VISITANTE ----
                    with c_vis:
                        st.markdown('<p class="label-equipo">Visitante</p>', unsafe_allow_html=True)
                        st.image(f"https://flagcdn.com/w160/{banderas[t_visit]}.png", width=70)
                        st.subheader(t_visit)
                        if apuesta:
                            css = "res-empate" if apuesta[2] == 1 else "res-fijo"
                            st.markdown(f'<div class="{css}">{apuesta[1]}</div>', unsafe_allow_html=True)
                        elif cerrado:
                            st.markdown('<div class="sin-apuesta">Sin apuesta</div>', unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)
            conn.close()

        # ---- TAB: TABLA DE EQUIPOS ----
        with t_equipos:
            st.header("Tablas de Posiciones Reales")
            g_sel = st.selectbox("Seleccionar Grupo:", list(grupos.keys()))
            st.table(generar_tabla_posiciones(g_sel, grupos[g_sel]))

        # ---- TAB: RANKING ----
        with t_ranking:
            st.header("Ranking de la Quiniela")
            df_rank = calcular_ranking_global()
            df_rank.insert(0, "Pos", range(1, len(df_rank) + 1))
            st.dataframe(df_rank, use_container_width=True, hide_index=True)

    # =================================================================
    # PANEL ADMINISTRADOR (MIGUEL)
    # =================================================================
    else:
        st.title("🛠️ PANEL DE CONTROL MAESTRO")
        a_tabs = st.tabs([
            "🔒 CONTROL DE ACCESO",
            "⚽ CARGA DE RESULTADOS",
            "🏆 RANKING TOTAL",
            "👥 GESTIÓN DE USUARIOS",
            "📜 FEED DE APUESTAS",
        ])
        conn = conectar_db()

        # ---- TAB: CONTROL DE ACCESO (cierre masivo por grupo) ----
        with a_tabs[0]:
            st.subheader("Cierre Manual por Grupo")
            st.caption("Cierra o abre todos los partidos de un grupo de golpe. Útil antes de que empiece la jornada.")
            c_adm = st.columns(4)
            for i, gid in enumerate(grupos.keys()):
                est = conn.execute(
                    "SELECT estado FROM estados_grupos WHERE grupo_id=?", (gid,)
                ).fetchone()[0]
                label = f"🔓 ABRIR {gid}" if est == 'cerrado' else f"🔒 CERRAR {gid}"
                if c_adm[i % 4].button(label, key=f"adm_lock_{gid}"):
                    nuevo = 'cerrado' if est == 'abierto' else 'abierto'
                    conn.execute("UPDATE estados_grupos SET estado=? WHERE grupo_id=?", (nuevo, gid))
                    conn.commit(); st.rerun()

        # ---- TAB: CARGA DE RESULTADOS ----
        with a_tabs[1]:
            st.subheader("Ingresar Marcadores Oficiales")
            st.info("⚠️ Al grabar un resultado, ese partido se cierra automáticamente. Los demás partidos del grupo siguen abiertos.")
            sel_g = st.selectbox("Grupo a calificar:", list(grupos.keys()))

            for idx, (i1, i2) in enumerate([(0,1),(2,3),(0,2),(1,3),(0,3),(1,2)]):
                pid = f"{sel_g}_{idx}"
                teams_adm = grupos[sel_g]

                res_existente = conn.execute(
                    "SELECT r1, r2 FROM resultados_reales WHERE partido_id=?", (pid,)
                ).fetchone()

                est_partido = conn.execute(
                    "SELECT estado FROM estados_partidos WHERE partido_id=?", (pid,)
                ).fetchone()
                ya_cerrado = est_partido and est_partido[0] == 'cerrado'

                estado_label = "🔒 Publicado y cerrado" if ya_cerrado else "🔓 Abierto"
                st.write(f"**{teams_adm[i1]} vs {teams_adm[i2]}** — {estado_label}")

                ca1, ca2, ca3 = st.columns([3, 3, 2])
                r1_val = ca1.number_input(
                    f"Goles {teams_adm[i1]}", 0, 15,
                    value=res_existente[0] if res_existente else 0,
                    key=f"adm1_{pid}"
                )
                r2_val = ca2.number_input(
                    f"Goles {teams_adm[i2]}", 0, 15,
                    value=res_existente[1] if res_existente else 0,
                    key=f"adm2_{pid}"
                )
                if ca3.button("Grabar", key=f"adm_sv_{pid}"):
                    # Guardar resultado real
                    conn.execute(
                        "INSERT OR REPLACE INTO resultados_reales VALUES (?,?,?)",
                        (pid, r1_val, r2_val)
                    )
                    # Cerrar SOLO este partido automáticamente
                    conn.execute(
                        "INSERT OR REPLACE INTO estados_partidos VALUES (?, 'cerrado')",
                        (pid,)
                    )
                    conn.commit()
                    tipo = "🤝 Empate" if r1_val == r2_val else "⚽ Resultado"
                    st.success(f"✅ {tipo}: {teams_adm[i1]} {r1_val} - {r2_val} {teams_adm[i2]} — 🔒 Partido cerrado automáticamente")
                st.divider()

        # ---- TAB: RANKING ----
        with a_tabs[2]:
            st.subheader("Ranking General de Jugadores")
            if st.button("🔄 Actualizar Ranking"): st.rerun()
            df_rank = calcular_ranking_global()
            df_rank.insert(0, "Pos", range(1, len(df_rank) + 1))
            st.dataframe(df_rank, use_container_width=True, hide_index=True)

        # ---- TAB: GESTIÓN DE USUARIOS ----
        with a_tabs[3]:
            st.subheader("Gestión de Usuarios")

            df_usuarios = pd.read_sql(
                "SELECT username, fecha_registro, bloqueado FROM usuarios WHERE username != 'Miguel' ORDER BY fecha_registro DESC",
                conn
            )

            if df_usuarios.empty:
                st.info("No hay usuarios registrados aún.")
            else:
                st.caption(f"Total de participantes: **{len(df_usuarios)}**")

                for _, row in df_usuarios.iterrows():
                    uname     = row['username']
                    bloqueado = int(row['bloqueado'])
                    fecha     = row['fecha_registro'][:10] if row['fecha_registro'] else "—"

                    # Contar apuestas del usuario
                    n_apuestas = conn.execute(
                        "SELECT COUNT(*) FROM apuestas WHERE usuario=?", (uname,)
                    ).fetchone()[0]

                    col_info, col_blq, col_del = st.columns([5, 2, 2])

                    with col_info:
                        estado_icon = "🔴 Bloqueado" if bloqueado else "🟢 Activo"
                        st.markdown(f"""
                        **{uname}** — {estado_icon}
                        <span style="color:#94a3b8; font-size:0.8rem;">
                            &nbsp;|&nbsp; Registro: {fecha} &nbsp;|&nbsp; Apuestas: {n_apuestas}
                        </span>
                        """, unsafe_allow_html=True)

                    with col_blq:
                        lbl_blq = "🔓 Desbloquear" if bloqueado else "🚫 Bloquear"
                        if st.button(lbl_blq, key=f"blq_{uname}", use_container_width=True):
                            nuevo_estado = 0 if bloqueado else 1
                            conn.execute(
                                "UPDATE usuarios SET bloqueado=? WHERE username=?",
                                (nuevo_estado, uname)
                            )
                            conn.commit(); st.rerun()

                    with col_del:
                        if st.button("🗑️ Eliminar", key=f"del_{uname}", use_container_width=True):
                            # Guardar en session_state para pedir confirmación
                            st.session_state[f"confirmar_del_{uname}"] = True
                            st.rerun()

                    # Confirmación antes de eliminar
                    if st.session_state.get(f"confirmar_del_{uname}"):
                        st.warning(f"⚠️ ¿Eliminar a **{uname}** y todas sus apuestas? Esta acción no se puede deshacer.")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Sí, eliminar", key=f"conf_si_{uname}", use_container_width=True):
                            try:
                                # Conexión dedicada para el borrado
                                conn_del = conectar_db()
                                conn_del.execute("DELETE FROM usuarios WHERE username=?", (uname,))
                                conn_del.execute("DELETE FROM apuestas WHERE usuario=?", (uname,))
                                conn_del.commit()
                                conn_del.close()
                                # VACUUM necesita conexión propia fuera de transacción
                                conn_vac = sqlite3.connect('quiniela_2026_pro_v5.db')
                                conn_vac.execute("VACUUM")
                                conn_vac.close()
                                del st.session_state[f"confirmar_del_{uname}"]
                                st.success(f"✅ Usuario **{uname}** eliminado permanentemente de la base de datos.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al eliminar: {e}")
                        if c2.button("❌ Cancelar", key=f"conf_no_{uname}", use_container_width=True):
                            del st.session_state[f"confirmar_del_{uname}"]
                            st.rerun()

                    st.divider()

        # ---- TAB: AUDITORÍA ----
        with a_tabs[4]:
            st.subheader("Auditoría de Apuestas")
            df_auditoria = pd.read_sql(
                "SELECT usuario, partido_id, g1, g2, es_empate, fecha FROM apuestas ORDER BY fecha DESC",
                conn
            )
            df_auditoria['Tipo'] = df_auditoria['es_empate'].apply(
                lambda x: "🤝 Empate" if x == 1 else "🎯 Marcador"
            )
            df_auditoria = df_auditoria.drop(columns=['es_empate'])
            st.dataframe(df_auditoria, use_container_width=True)

        conn.close()