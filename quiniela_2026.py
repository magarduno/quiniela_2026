import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import datetime
import time

# ─────────────────────────────────────────────
# 1. CONFIGURACIÓN Y ESTILOS
# ─────────────────────────────────────────────
st.set_page_config(page_title="Quiniela Mundial 2026", page_icon="🏆", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #f1f5f9; }
    .main-title { text-align:center; color:#1e3a8a; font-size:3.5rem; font-weight:900; margin-bottom:10px; letter-spacing:-1px; }
    .subtitle   { text-align:center; color:#64748b; font-size:1.2rem; margin-bottom:40px; }
    .reglas-container { background:white; padding:25px; border-radius:20px; border:1px solid #e2e8f0;
        box-shadow:0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom:30px; border-top:5px solid #3b82f6; }
    .regla-item { display:inline-block; margin:0 15px; font-weight:700; color:#1e40af; }
    .match-card         { background:white; padding:25px; border-radius:20px; margin-bottom:20px;
        box-shadow:0 10px 15px -3px rgba(0,0,0,0.08); border:1px solid #f1f5f9; transition:transform .2s; }
    .match-card:hover   { transform:translateY(-3px); }
    .match-card-cerrado { background:#f8fafc; padding:25px; border-radius:20px; margin-bottom:20px;
        box-shadow:0 2px 4px rgba(0,0,0,0.05); border:2px solid #e2e8f0; opacity:.85; }
    .elim-card { background:white; padding:25px; border-radius:20px; margin-bottom:20px;
        box-shadow:0 10px 25px -5px rgba(0,0,0,0.12); border-left:5px solid #7c3aed; }
    .elim-card-cerrado { background:#faf5ff; padding:25px; border-radius:20px; margin-bottom:20px;
        box-shadow:0 2px 4px rgba(0,0,0,0.05); border-left:5px solid #c4b5fd; opacity:.9; }
    .grupo-header { background:#1e3a8a; color:white; padding:15px 30px; border-radius:15px;
        margin:40px 0 20px 0; font-size:1.5rem; font-weight:800;
        display:flex; justify-content:space-between; align-items:center; }
    .ronda-header { background:linear-gradient(135deg,#7c3aed,#4f46e5); color:white; padding:15px 30px;
        border-radius:15px; margin:30px 0 20px 0; font-size:1.4rem; font-weight:800;
        display:flex; justify-content:space-between; align-items:center; }
    .res-fijo   { font-size:2rem; font-weight:900; color:#1e3a8a; text-align:center; background:#f8fafc;
        padding:15px; border-radius:12px; border:3px solid #e2e8f0; }
    .res-empate { font-size:2rem; font-weight:900; color:#d97706; text-align:center; background:#fffbeb;
        padding:15px; border-radius:12px; border:3px solid #fcd34d; }
    .label-equipo { font-size:.75rem; color:#94a3b8; font-weight:800; text-transform:uppercase;
        letter-spacing:1px; margin-bottom:8px; }
    .vs-text { font-size:1.3rem; font-weight:900; color:#cbd5e1; text-align:center; margin-top:35px; }
    .empate-badge     { background:#fef3c7; color:#92400e; font-size:.75rem; font-weight:700;
        padding:4px 10px; border-radius:20px; border:1px solid #fcd34d; text-align:center; margin-top:6px; }
    .cerrado-badge    { background:#fee2e2; color:#991b1b; font-size:.75rem; font-weight:700;
        padding:4px 10px; border-radius:20px; border:1px solid #fca5a5; text-align:center; margin-top:6px; }
    .sin-apuesta      { font-size:.9rem; color:#ef4444; font-weight:700; text-align:center; margin-top:10px; }
    .clasificado-badge{ background:#dcfce7; color:#166534; font-size:.8rem; font-weight:700;
        padding:4px 12px; border-radius:20px; border:1px solid #86efac; text-align:center; margin-top:6px; }
    .pendiente-badge  { background:#f1f5f9; color:#64748b; font-size:.8rem; font-weight:700;
        padding:4px 12px; border-radius:20px; border:1px solid #cbd5e1; text-align:center; margin-top:6px; }
    .stDataFrame { background:white; padding:10px; border-radius:15px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 2. BASE DE DATOS
# ─────────────────────────────────────────────
def conectar_db():
    return sqlite3.connect('quiniela_2026_pro_v5.db', check_same_thread=False)

def inicializar_db():
    conn = conectar_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
        (username TEXT PRIMARY KEY, password TEXT, fecha_registro TEXT, bloqueado INTEGER DEFAULT 0)''')
    try: c.execute("ALTER TABLE usuarios ADD COLUMN bloqueado INTEGER DEFAULT 0")
    except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS apuestas (
        usuario TEXT, partido_id TEXT, g1 INTEGER, g2 INTEGER,
        es_empate INTEGER DEFAULT 0, fecha TEXT, UNIQUE(usuario, partido_id))''')
    try: c.execute("ALTER TABLE apuestas ADD COLUMN es_empate INTEGER DEFAULT 0")
    except: pass

    c.execute('CREATE TABLE IF NOT EXISTS resultados_reales (partido_id TEXT PRIMARY KEY, r1 INTEGER, r2 INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS estados_grupos (grupo_id TEXT PRIMARY KEY, estado TEXT)')
    for g in [chr(i) for i in range(65, 77)]:
        c.execute("INSERT OR IGNORE INTO estados_grupos VALUES (?, 'abierto')", (g,))
    c.execute('CREATE TABLE IF NOT EXISTS estados_partidos (partido_id TEXT PRIMARY KEY, estado TEXT)')

    # ELIMINATORIAS
    # Cada partido tiene: id, ronda, equipo1, equipo2, slot1 (de dónde viene eq1), slot2, abierto_apuestas
    c.execute('''CREATE TABLE IF NOT EXISTS elim_partidos (
        partido_id      TEXT PRIMARY KEY,
        ronda           TEXT,
        num_partido     INTEGER DEFAULT 0,
        equipo1         TEXT DEFAULT '',
        equipo2         TEXT DEFAULT '',
        slot1           TEXT DEFAULT '',
        slot2           TEXT DEFAULT '',
        abierto_apuestas INTEGER DEFAULT 0
    )''')
    # Migración: agregar columnas si la BD ya existía con la tabla antigua
    for _col, _tipo in [
        ('num_partido',      'INTEGER DEFAULT 0'),
        ('slot1',            "TEXT DEFAULT ''"),
        ('slot2',            "TEXT DEFAULT ''"),
        ('abierto_apuestas', 'INTEGER DEFAULT 0'),
        ('equipo1',          "TEXT DEFAULT ''"),
        ('equipo2',          "TEXT DEFAULT ''"),
    ]:
        try: c.execute(f'ALTER TABLE elim_partidos ADD COLUMN {_col} {_tipo}')
        except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS elim_apuestas (
        usuario TEXT, partido_id TEXT, ganador TEXT, penales INTEGER DEFAULT 0, fecha TEXT,
        UNIQUE(usuario, partido_id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS elim_resultados (
        partido_id TEXT PRIMARY KEY, ganador TEXT, penales INTEGER DEFAULT 0)''')

    conn.commit()
    conn.close()

def partido_esta_cerrado(conn, partido_id):
    grupo_id = partido_id.split("_")[0]
    est = conn.execute("SELECT estado FROM estados_grupos WHERE grupo_id=?", (grupo_id,)).fetchone()
    if est and est[0] == 'cerrado': return True
    ep = conn.execute("SELECT estado FROM estados_partidos WHERE partido_id=?", (partido_id,)).fetchone()
    return ep and ep[0] == 'cerrado'

inicializar_db()

# ─────────────────────────────────────────────
# 3. DATOS DEL MUNDIAL
# ─────────────────────────────────────────────
banderas = {
    "México":"mx","Sudáfrica":"za","Corea del Sur":"kr","República Checa":"cz",
    "Canadá":"ca","Bosnia":"ba","Catar":"qa","Suiza":"ch",
    "Brasil":"br","Marruecos":"ma","Haití":"ht","Escocia":"gb-sct",
    "Estados Unidos":"us","Paraguay":"py","Australia":"au","Turquía":"tr",
    "Alemania":"de","Curazao":"cw","Costa de Marfil":"ci","Ecuador":"ec",
    "Países Bajos":"nl","Japón":"jp","Suecia":"se","Túnez":"tn",
    "Bélgica":"be","Egipto":"eg","Irán":"ir","Nueva Zelanda":"nz",
    "España":"es","Arabia Saudita":"sa","Cabo Verde":"cv","Uruguay":"uy",
    "Francia":"fr","Senegal":"sn","Irak":"iq","Noruega":"no",
    "Argentina":"ar","Argelia":"dz","Austria":"at","Jordania":"jo",
    "Portugal":"pt","RD Congo":"cd","Uzbekistán":"uz","Colombia":"co",
    "Inglaterra":"gb-eng","Ghana":"gh","Croacia":"hr","Panamá":"pa",
}

grupos = {
    "A":["México","Sudáfrica","Corea del Sur","República Checa"],
    "B":["Canadá","Bosnia","Catar","Suiza"],
    "C":["Brasil","Marruecos","Haití","Escocia"],
    "D":["Estados Unidos","Paraguay","Australia","Turquía"],
    "E":["Alemania","Curazao","Costa de Marfil","Ecuador"],
    "F":["Países Bajos","Japón","Suecia","Túnez"],
    "G":["Bélgica","Egipto","Irán","Nueva Zelanda"],
    "H":["España","Arabia Saudita","Cabo Verde","Uruguay"],
    "I":["Francia","Senegal","Irak","Noruega"],
    "J":["Argentina","Argelia","Austria","Jordania"],
    "K":["Portugal","RD Congo","Uzbekistán","Colombia"],
    "L":["Inglaterra","Ghana","Croacia","Panamá"],
}

RONDAS = ["32avos","Octavos","Cuartos","Semifinales","Tercer Lugar","Final"]

RONDA_LABEL = {
    "32avos":      "🔵 32avos de Final — 16 partidos",
    "Octavos":     "🟣 Octavos de Final — 8 partidos",
    "Cuartos":     "🟠 Cuartos de Final — 4 partidos",
    "Semifinales": "🔴 Semifinales — 2 partidos",
    "Tercer Lugar":"🥉 Tercer Lugar — 1 partido",
    "Final":       "🏆 Gran Final",
}

N_PARTIDOS = {"32avos":16,"Octavos":8,"Cuartos":4,"Semifinales":2,"Tercer Lugar":1,"Final":1}

# Mapa de avance automático:
# Cuando se graba el resultado del partido X de ronda R,
# el ganador va al slot correspondiente de la siguiente ronda.
# Formato: (ronda_origen, num_partido) -> (ronda_destino, num_partido_destino, slot)
LLAVE = {}
# 32avos -> Octavos (ganador partido N va a Octavos partido ceil(N/2), slot 1 o 2)
for i in range(1,17):
    dest = (i+1)//2
    slot = 1 if i%2==1 else 2
    LLAVE[("32avos",i)] = ("Octavos", dest, slot)
# Octavos -> Cuartos
for i in range(1,9):
    dest = (i+1)//2
    slot = 1 if i%2==1 else 2
    LLAVE[("Octavos",i)] = ("Cuartos", dest, slot)
# Cuartos -> Semifinales
for i in range(1,5):
    dest = (i+1)//2
    slot = 1 if i%2==1 else 2
    LLAVE[("Cuartos",i)] = ("Semifinales", dest, slot)
# Semifinales -> Final (ganadores) y Tercer Lugar (perdedores)
LLAVE[("Semifinales",1)] = ("Final", 1, 1)
LLAVE[("Semifinales",2)] = ("Final", 1, 2)
# Tercer lugar se llena con los perdedores de semis — Miguel los define manualmente

# ─────────────────────────────────────────────
# 4. LÓGICA
# ─────────────────────────────────────────────
def hash_pass(p): return hashlib.sha256(p.encode()).hexdigest()

def calcular_puntos_grupo(g1, g2, r1, r2):
    if g1==r1 and g2==r2: return 3
    if (g1>g2 and r1>r2) or (g1<g2 and r1<r2): return 2
    if g1==g2 and r1==r2: return 1
    return 0

def calcular_puntos_elim(ganador_ap, penales_ap, ganador_real, penales_real):
    if ganador_ap != ganador_real: return 0
    return 3 if int(penales_ap)==int(penales_real) else 2

def get_tabla_grupo(grupo_id):
    conn = conectar_db()
    lista = grupos[grupo_id]
    df_res = pd.read_sql("SELECT * FROM resultados_reales WHERE partido_id LIKE ?",
                         conn, params=(f"{grupo_id}_%",))
    conn.close()
    stats = {e:{"PJ":0,"G":0,"E":0,"P":0,"GF":0,"GC":0,"DG":0,"Pts":0} for e in lista}
    for i,(i1,i2) in enumerate([(0,1),(2,3),(0,2),(1,3),(0,3),(1,2)]):
        m = df_res[df_res['partido_id']==f"{grupo_id}_{i}"]
        if not m.empty:
            r1,r2=int(m.iloc[0]['r1']),int(m.iloc[0]['r2'])
            e1,e2=lista[i1],lista[i2]
            for e,gf,gc in [(e1,r1,r2),(e2,r2,r1)]:
                stats[e]["PJ"]+=1; stats[e]["GF"]+=gf; stats[e]["GC"]+=gc
                if gf>gc: stats[e]["Pts"]+=3; stats[e]["G"]+=1
                elif gf==gc: stats[e]["Pts"]+=1; stats[e]["E"]+=1
                else: stats[e]["P"]+=1
                stats[e]["DG"]=stats[e]["GF"]-stats[e]["GC"]
    return pd.DataFrame.from_dict(stats,orient='index').sort_values(by=["Pts","DG","GF"],ascending=False)

def get_clasificados():
    tablas={g:get_tabla_grupo(g) for g in grupos}
    primeros,segundos,terceros=[],[],[]
    for g,df in tablas.items():
        if len(df)>=1: primeros.append(df.index[0])
        if len(df)>=2: segundos.append(df.index[1])
        if len(df)>=3:
            row=df.iloc[2]
            terceros.append({"grupo":g,"equipo":df.index[2],"Pts":row["Pts"],"DG":row["DG"],"GF":row["GF"]})
    t_df=pd.DataFrame(terceros).sort_values(by=["Pts","DG","GF"],ascending=False) if terceros else pd.DataFrame()
    mejores=[r["equipo"] for _,r in t_df.head(8).iterrows()] if not t_df.empty else []
    return {"primeros":primeros,"segundos":segundos,"terceros":mejores}

def avanzar_ganador(conn, ronda_origen, num_partido, ganador):
    """
    Cuando Miguel graba un resultado, llama esta función.
    Automáticamente pone al ganador en el partido correspondiente
    de la siguiente ronda (si existe en la llave).
    """
    key = (ronda_origen, num_partido)
    if key not in LLAVE:
        return  # Final y Tercer Lugar no avanzan a nada

    ronda_dest, num_dest, slot = LLAVE[key]
    pid_dest = f"ELIM_{ronda_dest[:3].upper()}_{num_dest:02d}"

    # Crear el partido destino si no existe
    conn.execute("""INSERT OR IGNORE INTO elim_partidos
        (partido_id, ronda, num_partido, equipo1, equipo2, slot1, slot2, abierto_apuestas)
        VALUES (?,?,?,?,?,?,?,0)""",
        (pid_dest, ronda_dest, num_dest, '','','',''))

    # Poner al ganador en el slot correcto
    if slot == 1:
        conn.execute("UPDATE elim_partidos SET equipo1=? WHERE partido_id=?", (ganador, pid_dest))
    else:
        conn.execute("UPDATE elim_partidos SET equipo2=? WHERE partido_id=?", (ganador, pid_dest))
    conn.commit()

def calcular_ranking_global():
    conn = conectar_db()
    df_users    = pd.read_sql("SELECT username FROM usuarios WHERE username!='Miguel'", conn)
    df_ap_grupo = pd.read_sql("SELECT * FROM apuestas WHERE usuario!='Miguel'", conn)
    df_reales   = pd.read_sql("SELECT * FROM resultados_reales", conn)
    df_ap_elim  = pd.read_sql("SELECT * FROM elim_apuestas WHERE usuario!='Miguel'", conn)
    df_res_elim = pd.read_sql("SELECT * FROM elim_resultados", conn)
    conn.close()

    cols=["Puntos Totales","🎯 Exactos","🏆 Ganadores","🤝 Empates","⚽ Aciertos Elim"]
    ranking={u:{c:0 for c in cols} for u in df_users['username']}

    for _,ap in df_ap_grupo.iterrows():
        rr=df_reales[df_reales['partido_id']==ap['partido_id']]
        if not rr.empty and ap['usuario'] in ranking:
            pts=calcular_puntos_grupo(int(ap['g1']),int(ap['g2']),int(rr.iloc[0]['r1']),int(rr.iloc[0]['r2']))
            ranking[ap['usuario']]["Puntos Totales"]+=pts
            if pts==3: ranking[ap['usuario']]["🎯 Exactos"]+=1
            elif pts==2: ranking[ap['usuario']]["🏆 Ganadores"]+=1
            elif pts==1: ranking[ap['usuario']]["🤝 Empates"]+=1

    for _,ap in df_ap_elim.iterrows():
        rr=df_res_elim[df_res_elim['partido_id']==ap['partido_id']]
        if not rr.empty and ap['usuario'] in ranking:
            pts=calcular_puntos_elim(ap['ganador'],int(ap['penales']),rr.iloc[0]['ganador'],int(rr.iloc[0]['penales']))
            ranking[ap['usuario']]["Puntos Totales"]+=pts
            if pts>0: ranking[ap['usuario']]["⚽ Aciertos Elim"]+=1

    rows=[{"Usuario":u,**v} for u,v in ranking.items()]
    df=pd.DataFrame(rows)
    if df.empty: return pd.DataFrame(columns=["Usuario"]+cols)
    return df.sort_values("Puntos Totales",ascending=False)

# ─────────────────────────────────────────────
# 5. SESIÓN Y CABECERA
# ─────────────────────────────────────────────
if 'user' not in st.session_state: st.session_state.user=None

st.markdown('<h1 class="main-title">🏆 MUNDIAL 2026 PRO</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Sistema de Quinielas — Grupos + Eliminatorias</p>', unsafe_allow_html=True)
st.markdown("""<div class="reglas-container"><div style="text-align:center">
  <span class="regla-item">🎯 EXACTO: 3 PTS</span>
  <span class="regla-item">🏆 GANADOR: 2 PTS</span>
  <span class="regla-item">🤝 EMPATE: 1 PT</span>
  <span class="regla-item" style="color:#7c3aed">⚽ ELIM GANADOR+PENALES: 3 PTS</span>
  <span class="regla-item" style="color:#7c3aed">⚽ ELIM SOLO GANADOR: 2 PTS</span>
</div></div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 6. LOGIN
# ─────────────────────────────────────────────
if not st.session_state.user:
    _,col_log,_=st.columns([1,1.5,1])
    with col_log:
        st.markdown('<div style="background:white;padding:40px;border-radius:25px;box-shadow:0 25px 50px -12px rgba(0,0,0,0.25)">', unsafe_allow_html=True)
        opcion=st.radio("Acceso al Sistema",["Ingresar","Registrarse"],horizontal=True)
        if opcion=="Ingresar":
            u=st.text_input("Usuario"); p=st.text_input("Contraseña",type="password")
            if st.button("ACCEDER",use_container_width=True):
                if u=="Miguel" and p=="MGmundial26":
                    st.session_state.user="Miguel"; st.rerun()
                else:
                    conn=conectar_db(); row=conn.execute(
                        "SELECT password,bloqueado FROM usuarios WHERE username=?",(u,)).fetchone(); conn.close()
                    if row and row[0]==hash_pass(p):
                        if row[1]==1: st.error("❌ Cuenta bloqueada. Contacta al administrador.")
                        else: st.session_state.user=u; st.rerun()
                    else: st.error("Credenciales inválidas")
        else:
            nu=st.text_input("Nuevo Usuario"); np=st.text_input("Nueva Contraseña",type="password")
            if st.button("CREAR CUENTA",use_container_width=True):
                if not nu.strip(): st.error("Nombre vacío.")
                elif not np.strip(): st.error("Contraseña vacía.")
                elif nu.strip().lower()=="miguel": st.error("Nombre reservado.")
                else:
                    conn=conectar_db()
                    try:
                        if conn.execute("SELECT 1 FROM usuarios WHERE username=?",(nu.strip(),)).fetchone():
                            st.error(f"'{nu.strip()}' ya existe.")
                        else:
                            conn.execute("INSERT INTO usuarios VALUES(?,?,?,?)",
                                (nu.strip(),hash_pass(np),str(datetime.datetime.now()),0))
                            conn.commit(); st.success(f"¡Bienvenido, {nu.strip()}!"); time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
                    finally: conn.close()
        st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 7. PANEL PRINCIPAL
# ─────────────────────────────────────────────
else:
    with st.sidebar:
        st.markdown(f"### 🏟️ {st.session_state.user}")
        if st.button("🔄 Refrescar",use_container_width=True): st.rerun()
        if st.button("🚪 Salir",use_container_width=True): st.session_state.user=None; st.rerun()
        st.divider()
        st.info("Los partidos se bloquean antes del inicio del juego.")

    # ══════════════════════════════════════════
    # USUARIO NORMAL
    # ══════════════════════════════════════════
    if st.session_state.user != "Miguel":
        tabs=st.tabs(["📝 GRUPOS","📊 POSICIONES","🏆 ELIMINATORIAS","🌟 RANKING"])

        # ── GRUPOS ────────────────────────────
        with tabs[0]:
            conn=conectar_db()
            for g_id,eqs in grupos.items():
                est_g=conn.execute("SELECT estado FROM estados_grupos WHERE grupo_id=?",(g_id,)).fetchone()[0]
                st.markdown(f"""<div class="grupo-header"><span>GRUPO {g_id}</span>
                    <span style="font-size:1rem;opacity:.8">{'🔒 CERRADO' if est_g=='cerrado' else '🔓 ABIERTO'}</span>
                </div>""", unsafe_allow_html=True)
                for idx,(p1,p2) in enumerate([(0,1),(2,3),(0,2),(1,3),(0,3),(1,2)]):
                    pid=f"{g_id}_{idx}"; tl,tv=eqs[p1],eqs[p2]
                    cerrado=partido_esta_cerrado(conn,pid)
                    ap=conn.execute("SELECT g1,g2,es_empate FROM apuestas WHERE usuario=? AND partido_id=?",
                        (st.session_state.user,pid)).fetchone()
                    rr=conn.execute("SELECT r1,r2 FROM resultados_reales WHERE partido_id=?",(pid,)).fetchone()
                    st.markdown(f'<div class="{"match-card-cerrado" if cerrado else "match-card"}">', unsafe_allow_html=True)
                    if not cerrado and not ap:
                        cp1,cp2=st.columns(2)
                        g1=cp1.number_input(f"⚽ {tl}",0,15,value=0,key=f"g1_{pid}")
                        g2=cp2.number_input(f"⚽ {tv}",0,15,value=0,key=f"g2_{pid}")
                    cl,cv,cr=st.columns([4,2,4])
                    with cl:
                        st.markdown('<p class="label-equipo">Local</p>', unsafe_allow_html=True)
                        st.image(f"https://flagcdn.com/w160/{banderas[tl]}.png",width=60)
                        st.subheader(tl)
                        if ap:
                            css="res-empate" if ap[2]==1 else "res-fijo"
                            st.markdown(f'<div class="{css}">{ap[0]}</div>', unsafe_allow_html=True)
                        elif cerrado: st.markdown('<div class="sin-apuesta">Sin apuesta</div>', unsafe_allow_html=True)
                    with cv:
                        st.markdown('<p class="vs-text">VS</p>', unsafe_allow_html=True)
                        if not cerrado and not ap:
                            if st.button("💾 GUARDAR",key=f"btn_{pid}",use_container_width=True):
                                conn.execute("INSERT INTO apuestas VALUES(?,?,?,?,?,?)",
                                    (st.session_state.user,pid,g1,g2,0,str(datetime.datetime.now())))
                                conn.commit(); st.rerun()
                            if st.button("🤝 EMPATE",key=f"btn_emp_{pid}",use_container_width=True,
                                         help="Cualquier empate = 1 pt"):
                                conn.execute("INSERT INTO apuestas VALUES(?,?,?,?,?,?)",
                                    (st.session_state.user,pid,g1,g1,1,str(datetime.datetime.now())))
                                conn.commit(); st.rerun()
                        elif ap and ap[2]==1:
                            st.markdown('<div class="empate-badge">🤝 EMPATE</div>', unsafe_allow_html=True)
                        if rr:
                            st.markdown(f"""<div style="text-align:center;margin-top:8px;color:#16a34a;font-weight:700;font-size:.75rem">
                                ✅ OFICIAL<br><span style="font-size:1.6rem;font-weight:900">{rr[0]}-{rr[1]}</span></div>""",
                                unsafe_allow_html=True)
                        elif cerrado: st.markdown('<div class="cerrado-badge">🔒 Cerrado</div>', unsafe_allow_html=True)
                    with cr:
                        st.markdown('<p class="label-equipo">Visitante</p>', unsafe_allow_html=True)
                        st.image(f"https://flagcdn.com/w160/{banderas[tv]}.png",width=60)
                        st.subheader(tv)
                        if ap:
                            css="res-empate" if ap[2]==1 else "res-fijo"
                            st.markdown(f'<div class="{css}">{ap[1]}</div>', unsafe_allow_html=True)
                        elif cerrado: st.markdown('<div class="sin-apuesta">Sin apuesta</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            conn.close()
        
        # ── POSICIONES ────────────────────────
        with tabs[1]:
            st.header("Tablas de Posiciones por Grupo")
            g_sel=st.selectbox("Grupo:",list(grupos.keys()))
            st.table(get_tabla_grupo(g_sel))
            st.divider()
            st.subheader("🏅 Clasificados actuales")
            cl=get_clasificados()
            ca,cb,cc=st.columns(3)
            ca.write("**1° de grupo:**")
            for e in cl["primeros"]: ca.write(f"• {e}")
            cb.write("**2° de grupo:**")
            for e in cl["segundos"]: cb.write(f"• {e}")
            cc.write("**Mejores 3°:**")
            for e in cl["terceros"]: cc.write(f"• {e}")
            
            # ── ELIMINATORIAS (USUARIO) ────────────
        with tabs[2]:
            conn=conectar_db()
            for ronda in RONDAS:
                partidos=conn.execute(
                    "SELECT partido_id,equipo1,equipo2,abierto_apuestas FROM elim_partidos WHERE ronda=? ORDER BY COALESCE(num_partido,0),partido_id",
                    (ronda,)).fetchall()

                st.markdown(f'<div class="ronda-header"><span>{RONDA_LABEL[ronda]}</span>'
                    f'<span style="font-size:.9rem;opacity:.8">'
                    f'{"⏳ Pendiente" if not partidos else f"{len(partidos)} partidos"}'
                    f'</span></div>', unsafe_allow_html=True)

                if not partidos:
                    st.info("Esta ronda se habilitará cuando avancen los equipos clasificados.")
                    continue

                for pid_e,eq1,eq2,abierto in partidos:
                    ambos_definidos = bool(eq1 and eq2)
                    ap_e=conn.execute("SELECT ganador,penales FROM elim_apuestas WHERE usuario=? AND partido_id=?",
                        (st.session_state.user,pid_e)).fetchone()
                    res_e=conn.execute("SELECT ganador,penales FROM elim_resultados WHERE partido_id=?",(pid_e,)).fetchone()

                    card="elim-card" if (abierto and not res_e) else "elim-card-cerrado"
                    st.markdown(f'<div class="{card}">', unsafe_allow_html=True)
                    ce1,cvm,ce2=st.columns([4,3,4])

                    with ce1:
                        st.markdown('<p class="label-equipo">Equipo 1</p>', unsafe_allow_html=True)
                        if eq1 and eq1 in banderas:
                            st.image(f"https://flagcdn.com/w160/{banderas[eq1]}.png",width=60)
                        st.subheader(eq1 if eq1 else "⏳ Por definir")
                        if ap_e and ap_e[0]==eq1:
                            st.markdown('<div class="clasificado-badge">✅ Mi apuesta</div>', unsafe_allow_html=True)

                    with cvm:
                        st.markdown('<p class="vs-text">VS</p>', unsafe_allow_html=True)
                        if abierto and not ap_e and ambos_definidos:
                            penales_sel=st.checkbox("¿Va a penales?",key=f"pen_{pid_e}")
                            if st.button(f"✅ {eq1}",key=f"ev1_{pid_e}",use_container_width=True):
                                conn.execute("INSERT INTO elim_apuestas VALUES(?,?,?,?,?)",
                                    (st.session_state.user,pid_e,eq1,int(penales_sel),str(datetime.datetime.now())))
                                conn.commit(); st.rerun()
                            if st.button(f"✅ {eq2}",key=f"ev2_{pid_e}",use_container_width=True):
                                conn.execute("INSERT INTO elim_apuestas VALUES(?,?,?,?,?)",
                                    (st.session_state.user,pid_e,eq2,int(penales_sel),str(datetime.datetime.now())))
                                conn.commit(); st.rerun()
                        elif not ambos_definidos:
                            st.markdown('<div class="pendiente-badge">⏳ Equipos por definir</div>', unsafe_allow_html=True)
                        elif ap_e:
                            pen_txt=" (penales)" if ap_e[1]==1 else ""
                            st.markdown(f'<div style="text-align:center;font-weight:700;color:#7c3aed;margin-top:10px">'
                                f'Aposté: <b>{ap_e[0]}</b>{pen_txt}</div>', unsafe_allow_html=True)
                        if res_e:
                            pen_txt=" 🥅 Penales" if res_e[1]==1 else ""
                            st.markdown(f"""<div style="text-align:center;margin-top:8px;color:#16a34a;font-weight:700;font-size:.75rem">
                                ✅ CLASIFICÓ<br><span style="font-size:1.3rem;font-weight:900">{res_e[0]}{pen_txt}</span></div>""",
                                unsafe_allow_html=True)
                        elif not abierto and ambos_definidos:
                            st.markdown('<div class="cerrado-badge">🔒 Apuestas cerradas</div>', unsafe_allow_html=True)

                    with ce2:
                        st.markdown('<p class="label-equipo">Equipo 2</p>', unsafe_allow_html=True)
                        if eq2 and eq2 in banderas:
                            st.image(f"https://flagcdn.com/w160/{banderas[eq2]}.png",width=60)
                        st.subheader(eq2 if eq2 else "⏳ Por definir")
                        if ap_e and ap_e[0]==eq2:
                            st.markdown('<div class="clasificado-badge">✅ Mi apuesta</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            conn.close()

        # ── RANKING ───────────────────────────
        with tabs[3]:
            st.header("🌟 Ranking General")
            df_rank=calcular_ranking_global()
            if not df_rank.empty: df_rank.insert(0,"Pos",range(1,len(df_rank)+1))
            st.dataframe(df_rank,use_container_width=True,hide_index=True)

    # ══════════════════════════════════════════
    # ADMINISTRADOR
    # ══════════════════════════════════════════
    else:
        st.title("🛠️ PANEL DE CONTROL MAESTRO")
        a_tabs=st.tabs([
            "🔒 ACCESO GRUPOS",
            "⚽ RESULTADOS GRUPOS",
            "🏆 ELIMINATORIAS",
            "📊 RANKING",
            "👥 USUARIOS",
            "📜 AUDITORÍA",
        ])
        conn=conectar_db()

        # ── ACCESO GRUPOS ─────────────────────
        with a_tabs[0]:
            st.subheader("Cierre Manual por Grupo")
            cadm=st.columns(4)
            for i,gid in enumerate(grupos.keys()):
                est=conn.execute("SELECT estado FROM estados_grupos WHERE grupo_id=?",(gid,)).fetchone()[0]
                lbl=f"🔓 ABRIR {gid}" if est=='cerrado' else f"🔒 CERRAR {gid}"
                if cadm[i%4].button(lbl,key=f"adm_lock_{gid}"):
                    conn.execute("UPDATE estados_grupos SET estado=? WHERE grupo_id=?",
                        ('cerrado' if est=='abierto' else 'abierto',gid))
                    conn.commit(); st.rerun()

        # ── RESULTADOS GRUPOS ─────────────────
        with a_tabs[1]:
            st.subheader("Ingresar Marcadores Oficiales")
            st.info("⚠️ Al grabar, ese partido se cierra automáticamente.")
            sel_g=st.selectbox("Grupo:",list(grupos.keys()))
            for idx,(i1,i2) in enumerate([(0,1),(2,3),(0,2),(1,3),(0,3),(1,2)]):
                pid=f"{sel_g}_{idx}"; teams=grupos[sel_g]
                res_ex=conn.execute("SELECT r1,r2 FROM resultados_reales WHERE partido_id=?",(pid,)).fetchone()
                ep=conn.execute("SELECT estado FROM estados_partidos WHERE partido_id=?",(pid,)).fetchone()
                ya_c=ep and ep[0]=='cerrado'
                st.write(f"**{teams[i1]} vs {teams[i2]}** — {'🔒 Cerrado' if ya_c else '🔓 Abierto'}")
                ca1,ca2,ca3=st.columns([3,3,2])
                r1v=ca1.number_input(f"Goles {teams[i1]}",0,15,value=res_ex[0] if res_ex else 0,key=f"adm1_{pid}")
                r2v=ca2.number_input(f"Goles {teams[i2]}",0,15,value=res_ex[1] if res_ex else 0,key=f"adm2_{pid}")
                if ca3.button("Grabar",key=f"adm_sv_{pid}"):
                    conn.execute("INSERT OR REPLACE INTO resultados_reales VALUES(?,?,?)",(pid,r1v,r2v))
                    conn.execute("INSERT OR REPLACE INTO estados_partidos VALUES(?,'cerrado')",(pid,))
                    conn.commit()
                    tipo="🤝 Empate" if r1v==r2v else "⚽ Resultado"
                    st.success(f"✅ {tipo}: {teams[i1]} {r1v}-{r2v} {teams[i2]} — 🔒 Cerrado")
                st.divider()

        # ── ELIMINATORIAS (ADMIN) ─────────────
        with a_tabs[2]:
            st.subheader("Gestión de Fase Eliminatoria")
            st.info("""
            **Flujo automático:**
            1. Define los 16 enfrentamientos de 32avos manualmente.
            2. Al grabar cada resultado, el ganador pasa automáticamente al partido correcto de la siguiente ronda.
            3. Cuando un partido de Octavos/Cuartos/Semis ya tiene los 2 equipos, activa las apuestas con el botón 🔓.
            4. Graba el resultado y el sistema vuelve a avanzar al ganador.
            5. El **Tercer Lugar** se llena manualmente con los dos perdedores de semis.
            """)

            elim_tabs=st.tabs(RONDAS)
            for ti,ronda in enumerate(RONDAS):
                with elim_tabs[ti]:
                    st.markdown(f"#### {RONDA_LABEL[ronda]}")
                    n=N_PARTIDOS[ronda]
                    partidos_act=conn.execute(
                        "SELECT partido_id,num_partido,equipo1,equipo2,abierto_apuestas FROM elim_partidos WHERE ronda=? ORDER BY COALESCE(num_partido,0),partido_id",
                        (ronda,)).fetchall()

                    # ── 32avos: Miguel los define manualmente ──
                    if ronda=="32avos" and len(partidos_act)<n:
                        cl_data=get_clasificados()
                        todos=cl_data["primeros"]+cl_data["segundos"]+cl_data["terceros"]
                        with st.expander(f"📋 Clasificados disponibles ({len(todos)})"):
                            c1,c2,c3=st.columns(3)
                            c1.write("**1°:**"); [c1.write(f"• {e}") for e in cl_data["primeros"]]
                            c2.write("**2°:**"); [c2.write(f"• {e}") for e in cl_data["segundos"]]
                            c3.write("**Mejores 3°:**"); [c3.write(f"• {e}") for e in cl_data["terceros"]]

                        st.write("**Define los 16 enfrentamientos:**")
                        with st.form("form_32avos"):
                            nuevos=[]
                            ids_existentes={p[1] for p in partidos_act}
                            for ni in range(1,n+1):
                                if ni not in ids_existentes:
                                    cn1,cn2=st.columns(2)
                                    e1n=cn1.text_input(f"Partido {ni} — Equipo 1",key=f"e1_{ni}")
                                    e2n=cn2.text_input(f"Partido {ni} — Equipo 2",key=f"e2_{ni}")
                                    nuevos.append((ni,e1n,e2n))
                            if st.form_submit_button("💾 Guardar enfrentamientos"):
                                for ni,e1n,e2n in nuevos:
                                    if e1n.strip() and e2n.strip():
                                        pid_new=f"ELIM_32A_{ni:02d}"
                                        conn.execute("""INSERT OR IGNORE INTO elim_partidos
                                            (partido_id,ronda,num_partido,equipo1,equipo2,abierto_apuestas)
                                            VALUES(?,?,?,?,?,0)""",
                                            (pid_new,"32avos",ni,e1n.strip(),e2n.strip()))
                                conn.commit(); st.rerun()

                    # ── Tercer Lugar: también manual ──
                    elif ronda=="Tercer Lugar" and len(partidos_act)==0:
                        st.write("Define los dos perdedores de semifinales:")
                        with st.form("form_tercer"):
                            cn1,cn2=st.columns(2)
                            e1t=cn1.text_input("Perdedor Semifinal 1")
                            e2t=cn2.text_input("Perdedor Semifinal 2")
                            if st.form_submit_button("💾 Guardar"):
                                if e1t.strip() and e2t.strip():
                                    conn.execute("""INSERT OR IGNORE INTO elim_partidos
                                        (partido_id,ronda,num_partido,equipo1,equipo2,abierto_apuestas)
                                        VALUES(?,?,?,?,?,0)""",
                                        ("ELIM_TER_01","Tercer Lugar",1,e1t.strip(),e2t.strip()))
                                    conn.commit(); st.rerun()

                    # ── Mostrar partidos existentes ──
                    for p in partidos_act:
                        pid_e,num_p,eq1,eq2,abierto=p
                        res_e=conn.execute(
                            "SELECT ganador,penales FROM elim_resultados WHERE partido_id=?",(pid_e,)).fetchone()
                        ambos=bool(eq1 and eq2)

                        eq1_txt=eq1 if eq1 else "⏳ Por definir"
                        eq2_txt=eq2 if eq2 else "⏳ Por definir"
                        estado_txt="🔒 Resultado grabado" if res_e else ("🔓 Apuestas abiertas" if abierto else "⏸️ Apuestas cerradas")
                        st.write(f"**Partido {num_p}: {eq1_txt} vs {eq2_txt}** — {estado_txt}")

                        if res_e:
                            pen_txt=" (penales)" if res_e[1]==1 else ""
                            st.success(f"✅ Clasificó: **{res_e[0]}**{pen_txt}")
                            if st.button("✏️ Corregir resultado",key=f"corr_{pid_e}"):
                                conn.execute("DELETE FROM elim_resultados WHERE partido_id=?",(pid_e,))
                                conn.execute("UPDATE elim_partidos SET abierto_apuestas=1 WHERE partido_id=?",(pid_e,))
                                conn.commit(); st.rerun()
                        else:
                            # Botón para abrir/cerrar apuestas manualmente
                            if ambos:
                                col_ab,col_res1,col_res2,col_res3=st.columns([2,3,2,2])
                                lbl_ab="⏸️ Cerrar apuestas" if abierto else "🔓 Abrir apuestas"
                                if col_ab.button(lbl_ab,key=f"ab_{pid_e}",use_container_width=True):
                                    conn.execute("UPDATE elim_partidos SET abierto_apuestas=? WHERE partido_id=?",
                                        (0 if abierto else 1,pid_e))
                                    conn.commit(); st.rerun()
                                ganador_sel=col_res1.selectbox("Ganador",["",eq1,eq2],key=f"gan_{pid_e}")
                                penales_sel=col_res2.checkbox("¿Penales?",key=f"pen_{pid_e}")
                                if col_res3.button("Grabar resultado",key=f"gsv_{pid_e}",use_container_width=True):
                                    if ganador_sel:
                                        # Guardar resultado y cerrar apuestas
                                        conn.execute("INSERT OR REPLACE INTO elim_resultados VALUES(?,?,?)",
                                            (pid_e,ganador_sel,int(penales_sel)))
                                        conn.execute("UPDATE elim_partidos SET abierto_apuestas=0 WHERE partido_id=?",(pid_e,))
                                        conn.commit()
                                        # Avanzar ganador automáticamente a la siguiente ronda
                                        avanzar_ganador(conn,ronda,num_p,ganador_sel)
                                        st.success(f"✅ Clasificó {ganador_sel} — ganador avanzado automáticamente")
                                        st.rerun()
                                    else: st.warning("Selecciona el ganador.")
                            else:
                                st.caption("⏳ Esperando que avancen los equipos de la ronda anterior.")
                        st.divider()

        # ── RANKING ───────────────────────────
        with a_tabs[3]:
            st.subheader("Ranking General")
            if st.button("🔄 Actualizar"): st.rerun()
            df_rank=calcular_ranking_global()
            if not df_rank.empty: df_rank.insert(0,"Pos",range(1,len(df_rank)+1))
            st.dataframe(df_rank,use_container_width=True,hide_index=True)

        # ── USUARIOS ──────────────────────────
        with a_tabs[4]:
            st.subheader("Gestión de Usuarios")
            df_us=pd.read_sql(
                "SELECT username,fecha_registro,bloqueado FROM usuarios WHERE username!='Miguel' ORDER BY fecha_registro DESC",conn)
            if df_us.empty: st.info("No hay usuarios registrados.")
            else:
                st.caption(f"Total: **{len(df_us)}** participantes")
                for _,row in df_us.iterrows():
                    uname=row['username']; bloq=int(row['bloqueado'])
                    fecha=row['fecha_registro'][:10] if row['fecha_registro'] else "—"
                    n_ap=conn.execute("SELECT COUNT(*) FROM apuestas WHERE usuario=?",(uname,)).fetchone()[0]
                    n_el=conn.execute("SELECT COUNT(*) FROM elim_apuestas WHERE usuario=?",(uname,)).fetchone()[0]
                    ci,cb2,cd=st.columns([5,2,2])
                    with ci:
                        st.markdown(f"**{uname}** — {'🔴 Bloqueado' if bloq else '🟢 Activo'} "
                            f'<span style="color:#94a3b8;font-size:.8rem">| {fecha} | Grupos:{n_ap} | Elim:{n_el}</span>',
                            unsafe_allow_html=True)
                    with cb2:
                        if st.button("🔓 Desbloquear" if bloq else "🚫 Bloquear",key=f"blq_{uname}",use_container_width=True):
                            conn.execute("UPDATE usuarios SET bloqueado=? WHERE username=?",(0 if bloq else 1,uname))
                            conn.commit(); st.rerun()
                    with cd:
                        if st.button("🗑️ Eliminar",key=f"del_{uname}",use_container_width=True):
                            st.session_state[f"cdel_{uname}"]=True; st.rerun()
                    if st.session_state.get(f"cdel_{uname}"):
                        st.warning(f"⚠️ ¿Eliminar a **{uname}** permanentemente?")
                        cs1,cs2=st.columns(2)
                        if cs1.button("✅ Sí",key=f"csi_{uname}",use_container_width=True):
                            try:
                                cd2=conectar_db()
                                cd2.execute("DELETE FROM usuarios WHERE username=?",(uname,))
                                cd2.execute("DELETE FROM apuestas WHERE usuario=?",(uname,))
                                cd2.execute("DELETE FROM elim_apuestas WHERE usuario=?",(uname,))
                                cd2.commit(); cd2.close()
                                cv2=sqlite3.connect('quiniela_2026_pro_v5.db')
                                cv2.execute("VACUUM"); cv2.close()
                                del st.session_state[f"cdel_{uname}"]
                                st.success(f"✅ {uname} eliminado."); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")
                        if cs2.button("❌ No",key=f"cno_{uname}",use_container_width=True):
                            del st.session_state[f"cdel_{uname}"]; st.rerun()
                    st.divider()

        # ── AUDITORÍA ─────────────────────────
        with a_tabs[5]:
            st.subheader("Auditoría de Apuestas")
            tg,te=st.tabs(["Fase de Grupos","Eliminatorias"])
            with tg:
                df_aud=pd.read_sql("SELECT usuario,partido_id,g1,g2,es_empate,fecha FROM apuestas ORDER BY fecha DESC",conn)
                df_aud['Tipo']=df_aud['es_empate'].apply(lambda x:"🤝 Empate" if x==1 else "🎯 Marcador")
                st.dataframe(df_aud.drop(columns=['es_empate']),use_container_width=True)
            with te:
                df_ae=pd.read_sql("SELECT usuario,partido_id,ganador,penales,fecha FROM elim_apuestas ORDER BY fecha DESC",conn)
                if not df_ae.empty:
                    df_ae['penales']=df_ae['penales'].apply(lambda x:"Sí" if x==1 else "No")
                    df_ae.columns=["Usuario","Partido","Ganador apostado","Penales","Fecha"]
                st.dataframe(df_ae,use_container_width=True)
        conn.close()