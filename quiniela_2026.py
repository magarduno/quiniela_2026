import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import datetime
import time
from datetime import timedelta

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
    .match-card         { background:white; padding:15px; border-radius:20px; margin-bottom:20px;
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
        padding:0px; border-radius:12px; border:3px solid #e2e8f0; }
    .res-empate { font-size:2rem; font-weight:900; color:#d97706; text-align:center; background:#fffbeb;
        padding:0px; border-radius:12px; border:3px solid #fcd34d; }
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
    
     /* HEADER DE GRUPO */
    .grupo-header {
        background: var(--secondary-background-color);
        color: var(--text-color);
        padding:12px 20px; border-radius:10px;
        margin:28px 0 14px 0; font-size:clamp(1rem,4vw,1.3rem);
        font-family:'Bebas Neue',sans-serif; letter-spacing:3px;
        display:flex; justify-content:space-between; align-items:center;
        border:1px solid rgba(128,128,128,0.2);
    }
    .grupo-estado {
        font-size:clamp(.6rem,2vw,.75rem); font-family:'Inter',sans-serif;
        font-weight:600; letter-spacing:1px;
        color: var(--text-color); opacity:.5;
    }

    /* TARJETA DE PARTIDO */
    .match-card {
        background: var(--secondary-background-color);
        border-radius:12px; margin-bottom:14px;
        border:1px solid rgba(128,128,128,0.2); overflow:hidden;
    }
    .match-card-cerrado {
        background: var(--secondary-background-color);
        border-radius:12px; margin-bottom:14px;
        border:1px solid rgba(128,128,128,0.1);
        opacity:.55; overflow:hidden;
    }
    .match-band {
        background: var(--background-color);
        padding:7px 16px; font-size:.65rem; font-weight:700;
        color: var(--text-color); opacity:.4;
        letter-spacing:1.5px; text-transform:uppercase;
        border-bottom:1px solid rgba(128,128,128,0.15);
    }
    .match-inner { padding:16px; }
    .teams-row {
        display:flex; align-items:center; justify-content:space-between;
        gap:8px; margin-bottom:12px;
    }
    .team-block { flex:1; text-align:center; min-width:0; }
    .team-flag  { width:48px; height:32px; object-fit:cover; border-radius:4px; margin-bottom:6px; }
    .team-name  {
        font-weight:700; font-size:clamp(.75rem,3vw,.88rem);
        color: var(--text-color); line-height:1.2;
        overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
    }
    .score-box {
        font-size:clamp(1.4rem,6vw,2rem); font-weight:800;
        color: var(--text-color);
        background: var(--background-color);
        border:1px solid rgba(128,128,128,0.3);
        border-radius:8px; padding:6px 14px; min-width:48px;
        text-align:center; line-height:1;
    }
    .score-box-empate { color:#c49a28; border-color:rgba(196,154,40,0.3); }
    .vs-badge {
        font-size:.7rem; font-weight:700;
        color: var(--text-color); opacity:.4;
        background: var(--background-color);
        border:1px solid rgba(128,128,128,0.2);
        border-radius:6px; padding:4px 8px; flex-shrink:0;
    }

    /* Resultado oficial */
    .result-oficial {
        text-align:center;
        background: rgba(34,197,94,0.08);
        border:1px solid rgba(34,197,94,0.3);
        border-radius:8px; padding:8px; margin-top:10px;
        font-weight:700; color:#4ade80; font-size:1rem;
    }
    .result-oficial small { display:block; font-size:.62rem; color:#4ade80; opacity:.7; font-weight:600; margin-bottom:2px; }

    /* Badges */
    .badge-empate {
        display:inline-block;
        background:rgba(196,154,40,0.12); color:#c49a28;
        font-size:.68rem; font-weight:700; padding:3px 10px;
        border-radius:6px; border:1px solid rgba(196,154,40,0.3);
    }
    .badge-cerrado {
        display:inline-block;
        background:rgba(248,113,113,0.1); color:#f87171;
        font-size:.68rem; font-weight:700; padding:3px 10px;
        border-radius:6px; border:1px solid rgba(248,113,113,0.2);
    }
    .badge-sin-apuesta {
        display:inline-block;
        background: var(--background-color);
        color: var(--text-color); opacity:.4;
        font-size:.68rem; font-weight:600; padding:3px 10px;
        border-radius:6px; border:1px solid rgba(128,128,128,0.2);
    }
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
        (username TEXT PRIMARY KEY, password TEXT, nombre_completo TEXT DEFAULT '',
         telefono TEXT DEFAULT '', fecha_registro TEXT,
         bloqueado INTEGER DEFAULT 0, pagado INTEGER DEFAULT 0)''')
    for _col, _tipo in [("bloqueado","INTEGER DEFAULT 0"),("pagado","INTEGER DEFAULT 0"),
                        ("nombre_completo","TEXT DEFAULT ''"),("telefono","TEXT DEFAULT ''"),
                        ("puede_cambiar_pass","INTEGER DEFAULT 0")]:
        try: c.execute(f"ALTER TABLE usuarios ADD COLUMN {_col} {_tipo}")
        except: pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS apuestas (
        usuario TEXT, partido_id TEXT, g1 INTEGER, g2 INTEGER,
        es_empate INTEGER DEFAULT 0, pagado INTEGER DEFAULT 0, fecha TEXT,
        UNIQUE(usuario, partido_id))''')
    for _col,_tipo in [("es_empate","INTEGER DEFAULT 0"),("pagado","INTEGER DEFAULT 0")]:
        try: c.execute(f"ALTER TABLE apuestas ADD COLUMN {_col} {_tipo}")
        except: pass

    c.execute('CREATE TABLE IF NOT EXISTS resultados_reales (partido_id TEXT PRIMARY KEY, r1 INTEGER, r2 INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS estados_grupos (grupo_id TEXT PRIMARY KEY, estado TEXT)')
    for g in [chr(i) for i in range(65, 77)]:
        c.execute("INSERT OR IGNORE INTO estados_grupos VALUES (?, 'abierto')", (g,))
    c.execute('CREATE TABLE IF NOT EXISTS estados_partidos (partido_id TEXT PRIMARY KEY, estado TEXT)')

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
        usuario TEXT, partido_id TEXT, ganador TEXT, penales INTEGER DEFAULT 0,
        pagado INTEGER DEFAULT 0, fecha TEXT,
        UNIQUE(usuario, partido_id))''')
    try: c.execute("ALTER TABLE elim_apuestas ADD COLUMN pagado INTEGER DEFAULT 0")
    except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS elim_resultados (
        partido_id TEXT PRIMARY KEY, ganador TEXT, penales INTEGER DEFAULT 0)''')

    try:
        c.execute("UPDATE elim_partidos SET num_partido=CAST(partido_id AS INTEGER) WHERE num_partido IS NULL OR num_partido=0")
    except: pass

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

MATCH_DESC = {
    73:  "2°A vs 2°B",
    74:  "1°E vs Mejor 3°(ABCDF)",
    75:  "1°F vs 2°C",
    76:  "1°C vs 2°F",
    77:  "1°I vs Mejor 3°(CDFGH)",
    78:  "2°E vs 2°I",
    79:  "1°A vs Mejor 3°(CEFHI)",
    80:  "1°L vs Mejor 3°(EHIJK)",
    81:  "1°D vs Mejor 3°(BEFIJ)",
    82:  "1°G vs Mejor 3°(AEHIJ)",
    83:  "2°K vs 2°L",
    84:  "1°H vs 2°J",
    85:  "1°B vs Mejor 3°(EFGIJ)",
    86:  "1°J vs 2°H",
    87:  "1°K vs Mejor 3°(DEIJL)",
    88:  "2°D vs 2°G",
    89:  "W74 vs W77",
    90:  "W73 vs W75",
    91:  "W76 vs W78",
    92:  "W79 vs W80",
    93:  "W83 vs W84",
    94:  "W81 vs W82",
    95:  "W86 vs W88",
    96:  "W85 vs W87",
    97:  "W89 vs W90",
    98:  "W93 vs W94",
    99:  "W91 vs W92",
    100: "W95 vs W96",
    101: "W97 vs W98",
    102: "W99 vs W100",
    103: "RU101 vs RU102",
    104: "W101 vs W102",
}

RONDA_POR_MATCH = {
    **{m: "32avos"      for m in range(73, 89)},
    **{m: "Octavos"     for m in range(89, 97)},
    **{m: "Cuartos"     for m in range(97, 101)},
    **{m: "Semifinales" for m in range(101, 103)},
    103: "Tercer Lugar",
    104: "Final",
}

N_PARTIDOS = {"32avos":16,"Octavos":8,"Cuartos":4,"Semifinales":2,"Tercer Lugar":1,"Final":1}

MATCHES_POR_RONDA = {
    "32avos":       list(range(73, 89)),
    "Octavos":      list(range(89, 97)),
    "Cuartos":      list(range(97, 101)),
    "Semifinales":  [101, 102],
    "Tercer Lugar": [103],
    "Final":        [104],
}

LLAVE_AVANCE = {
    74:  (89,  1),
    77:  (89,  2),
    73:  (90,  1),
    75:  (90,  2),
    83:  (93,  1),
    84:  (93,  2),
    81:  (94,  1),
    82:  (94,  2),
    76:  (91,  1),
    78:  (91,  2),
    79:  (92,  1),
    80:  (92,  2),
    86:  (95,  1),
    88:  (95,  2),
    85:  (96,  1),
    87:  (96,  2),
    89:  (97,  1),
    90:  (97,  2),
    93:  (98,  1),
    94:  (98,  2),
    91:  (99,  1),
    92:  (99,  2),
    95:  (100, 1),
    96:  (100, 2),
    97:  (101, 1),
    98:  (101, 2),
    99:  (102, 1),
    100: (102, 2),
    101: (104, 1),
    102: (104, 2),
}

LLAVE_PERDEDOR = {
    101: (103, 1),
    102: (103, 2),
}

RONDAS = ["32avos", "Octavos", "Cuartos", "Semifinales", "Tercer Lugar", "Final"]

RONDA_LABEL = {
    "32avos":       "🔵 Ronda de 32 — P73 al P88",
    "Octavos":      "🟣 Ronda de 16 — P89 al P96",
    "Cuartos":      "🟠 Cuartos de Final — P97 al P100",
    "Semifinales":  "🔴 Semifinales — P101 y P102",
    "Tercer Lugar": "🥉 Tercer Lugar — P103",
    "Final":        "🏆 Gran Final — P104",
}

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
    """
    Reglas de puntuacion eliminatorias:
    - Aciertas ganador, NO marcaste penales NO hubo penales  -> 2 pts
    - Aciertas ganador + marcaste penales + hubo pen         -> 3 pts  (2 + 1 bonus)
    - Aciertas ganador no marcaste penales + hubo pen        -> 1 pt
    - Aciertas ganador + marcaste penales pero NO hubo pen   -> 1 pt
    - Ganador incorrecto + no marcaste penales               -> 0 pts
    - Ganador incorrecto + marcaste penales + hubo pen       -> 2 pts (no adivinaste ganador)
    """
    penales_ap   = int(penales_ap)
    penales_real = int(penales_real)
    acerto_ganador = (ganador_ap == ganador_real)

    # Marcaste penales pero NO hubo penales -> 0 pt
    if penales_ap == 1 and penales_real == 0:
        return 0

    # Marcaste penales Y hubo penales
    if penales_ap == 1 and penales_real == 1:
        return 3 if acerto_ganador else 2

    # No marcaste penales
    # penales_ap == 0
    if acerto_ganador:
        return 2 if penales_real == 0 else 1   # si hubo penales pero no los marcaste -> 1 pt
    return 0

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

def avanzar_ganador(conn, match_id_origen, ganador, perdedor=None):
    if match_id_origen in LLAVE_AVANCE:
        match_dest, slot = LLAVE_AVANCE[match_id_origen]
        ronda_dest = RONDA_POR_MATCH[match_dest]
        conn.execute("""INSERT OR IGNORE INTO elim_partidos
            (partido_id, ronda, num_partido, equipo1, equipo2, abierto_apuestas)
            VALUES (?,?,?,?,?,0)""",
            (match_dest, ronda_dest, match_dest, '', ''))
        col = "equipo1" if slot==1 else "equipo2"
        conn.execute(f"UPDATE elim_partidos SET {col}=? WHERE partido_id=?",
                     (ganador, match_dest))

    if perdedor and match_id_origen in LLAVE_PERDEDOR:
        match_dest, slot = LLAVE_PERDEDOR[match_id_origen]
        conn.execute("""INSERT OR IGNORE INTO elim_partidos
            (partido_id, ronda, num_partido, equipo1, equipo2, abierto_apuestas)
            VALUES (?,?,?,?,?,0)""",
            (match_dest, "Tercer Lugar", match_dest, '', ''))
        col = "equipo1" if slot==1 else "equipo2"
        conn.execute(f"UPDATE elim_partidos SET {col}=? WHERE partido_id=?",
                     (perdedor, match_dest))

    conn.commit()

def calcular_ranking_global():
    conn = conectar_db()
    df_users    = pd.read_sql("SELECT username FROM usuarios WHERE username!='ADMIN' AND pagado=1", conn)
    df_ap_grupo = pd.read_sql("SELECT * FROM apuestas WHERE usuario!='ADMIN'", conn)
    df_reales   = pd.read_sql("SELECT * FROM resultados_reales", conn)
    df_ap_elim  = pd.read_sql("SELECT * FROM elim_apuestas WHERE usuario!='ADMIN'", conn)
    df_res_elim = pd.read_sql("SELECT * FROM elim_resultados", conn)
    conn.close()
    # Grupos: Exacto(3pts) | Ganador(2pts) | Empate(1pt)
    # Elim:   Ganador+Penales(3pts) | Ganador sin penales(2pts) | Penales/no hubo(1pt)
    cols=["Pts","Exacto","Ganador","Empate","Elim G+Pen","Elim Ganador","Elim Pen/No"]
    ranking={u:{c:0 for c in cols} for u in df_users['username']}
    for _,ap in df_ap_grupo.iterrows():
        rr=df_reales[df_reales['partido_id']==ap['partido_id']]
        if not rr.empty and ap['usuario'] in ranking:
            pts=calcular_puntos_grupo(int(ap['g1']),int(ap['g2']),int(rr.iloc[0]['r1']),int(rr.iloc[0]['r2']))
            ranking[ap['usuario']]["Pts"]+=pts
            if pts==3: ranking[ap['usuario']]["Exacto"]+=1
            elif pts==2: ranking[ap['usuario']]["Ganador"]+=1
            elif pts==1: ranking[ap['usuario']]["Empate"]+=1
    for _,ap in df_ap_elim.iterrows():
        rr=df_res_elim[df_res_elim['partido_id']==ap['partido_id']]
        if not rr.empty and ap['usuario'] in ranking:
            _p_ap   = int(ap['penales'])         if ap['penales']         is not None and str(ap['penales'])         != 'nan' else 0
            _p_real = int(rr.iloc[0]['penales']) if rr.iloc[0]['penales'] is not None and str(rr.iloc[0]['penales']) != 'nan' else 0
            pts=calcular_puntos_elim(ap['ganador'],_p_ap,rr.iloc[0]['ganador'],_p_real)
            ranking[ap['usuario']]["Pts"]+=pts
            if pts==3: ranking[ap['usuario']]["Elim G+Pen"]+=1
            elif pts==2: ranking[ap['usuario']]["Elim Ganador"]+=1
            elif pts==1: ranking[ap['usuario']]["Elim Pen/No"]+=1
    rows=[{"Usuario":u,**v} for u,v in ranking.items()]
    df=pd.DataFrame(rows)
    if df.empty: return pd.DataFrame(columns=["Usuario"]+cols)
    return df.sort_values("Pts",ascending=False)


def _partido_cerrado_para_vista(conn, partido_id):
    rr = conn.execute(
        "SELECT 1 FROM resultados_reales WHERE partido_id=?", (partido_id,)).fetchone()
    if rr: return True
    grupo_id = partido_id.split("_")[0]
    eg = conn.execute(
        "SELECT estado FROM estados_grupos WHERE grupo_id=?", (grupo_id,)).fetchone()
    return eg and eg[0] == 'cerrado'

def flag_url(equipo):
    code = banderas.get(equipo, "un")
    return f"https://flagcdn.com/w80/{code}.png"

def render_auditoria_grupos(conn, usuario_filtro=None):
    es_admin = usuario_filtro is None
    st.markdown("#### 📋 Apuestas por Grupo")

    grupo_sel = st.selectbox("Ver grupo:", ["Todos"] + list(grupos.keys()),
                              key=f"aud_grupo_{usuario_filtro or 'admin'}")
    grupos_a_mostrar = list(grupos.keys()) if grupo_sel == "Todos" else [grupo_sel]

    for g_id in grupos_a_mostrar:
        eqs = grupos[g_id]
        partidos_idx = [(0,1),(2,3),(0,2),(1,3),(0,3),(1,2)]
        bloques = []

        for idx,(p1,p2) in enumerate(partidos_idx):
            pid = f"{g_id}_{idx}"
            tl, tv = eqs[p1], eqs[p2]
            cerrado = _partido_cerrado_para_vista(conn, pid)
            rr = conn.execute(
                "SELECT r1,r2 FROM resultados_reales WHERE partido_id=?",(pid,)).fetchone()

            if es_admin:
                aps = conn.execute(
                    "SELECT usuario,g1,g2,es_empate,fecha FROM apuestas WHERE partido_id=? ORDER BY fecha DESC",
                    (pid,)).fetchall()
            else:
                if cerrado:
                    aps = conn.execute(
                        "SELECT usuario,g1,g2,es_empate,fecha FROM apuestas WHERE partido_id=? ORDER BY fecha DESC",
                        (pid,)).fetchall()
                else:
                    aps = conn.execute(
                        "SELECT usuario,g1,g2,es_empate,fecha FROM apuestas WHERE usuario=? AND partido_id=?",
                        (usuario_filtro, pid)).fetchall()

            filas = []
            for ap in aps:
                uname, g1, g2, es_empate, fecha = ap
                es_yo = (uname == usuario_filtro)
                pronostico = f"{g1} - {g2}" + (" (empate)" if es_empate==1 else "")
                tipo = "🤝 Empate" if es_empate==1 else "🎯 Marcador"
                fecha = fecha [:16]

                if rr:
                    r1,r2 = int(rr[0]),int(rr[1])
                    pts = calcular_puntos_grupo(g1,g2,r1,r2)
                    resultado = f"{r1} - {r2}"
                    pts_txt = {3:"🎯 3 pts",2:"🏆 2 pts",1:"🤝 1 pt",0:"❌ 0 pts"}[pts]
                else:
                    resultado = "⏳ Pendiente"
                    pts_txt = "—"

                fila = {"Partido": f"{tl} vs {tv}"}
                if not es_admin and cerrado:
                    fila["Quién"] = f"{'👤 Yo' if es_yo else uname}"
                elif es_admin:
                    fila["Usuario"] = uname
                fila["Pronóstico"] = pronostico
                fila["Tipo"] = tipo
                fila["Resultado oficial"] = resultado
                fila["Puntos"] = pts_txt
                fila["Fecha de apuesta"] = fecha
                filas.append(fila)

            nombre_partido = f"{tl} vs {tv}"
            bloques.append((nombre_partido, filas, cerrado))

        tiene_algo = any(f for _,f,_ in bloques)
        if not tiene_algo and grupo_sel != "Todos":
            st.info(f"No hay apuestas en el Grupo {g_id}.")
            continue

        header = f"**Grupo {g_id}**"
        expanded = (grupo_sel != "Todos")

        with st.expander(header, expanded=expanded):
            for nombre_partido, filas, cerrado in bloques:
                if not filas:
                    continue
                estado_icon = "🔒" if cerrado else "🔓"
                st.markdown(f"**{estado_icon} {nombre_partido}**"
                    + ("" if cerrado else " — *Las apuestas del resto se revelan al cerrar el partido*"),
                    unsafe_allow_html=False)
                st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
                st.markdown("---")


def render_auditoria_eliminatorias(conn, usuario_filtro=None):
    es_admin = usuario_filtro is None
    st.markdown("#### ⚽ Apuestas Eliminatorias")

    ronda_sel = st.selectbox("Ver ronda:", ["Todas"] + RONDAS,
                              key=f"aud_ronda_{usuario_filtro or 'admin'}")
    rondas_a_mostrar = RONDAS if ronda_sel == "Todas" else [ronda_sel]

    for ronda in rondas_a_mostrar:
        partidos = conn.execute(
            "SELECT partido_id,equipo1,equipo2 FROM elim_partidos WHERE ronda=? ORDER BY COALESCE(num_partido,0),partido_id",
            (ronda,)).fetchall()
        if not partidos: continue

        bloques = []
        for pid_e,eq1,eq2 in partidos:
            res_e = conn.execute(
                "SELECT ganador,penales FROM elim_resultados WHERE partido_id=?",(pid_e,)).fetchone()
            cerrado = res_e is not None

            if es_admin:
                aps = conn.execute(
                    "SELECT usuario,ganador,penales,fecha FROM elim_apuestas WHERE partido_id=? ORDER BY fecha DESC",
                    (pid_e,)).fetchall()
            else:
                if cerrado:
                    aps = conn.execute(
                        "SELECT usuario,ganador,penales,fecha FROM elim_apuestas WHERE partido_id=? ORDER BY fecha DESC",
                        (pid_e,)).fetchall()
                else:
                    aps = conn.execute(
                        "SELECT usuario,ganador,penales,fecha FROM elim_apuestas WHERE usuario=? AND partido_id=?",
                        (usuario_filtro, pid_e)).fetchall()

            filas = []
            for ap in aps:
                uname, ganador_ap, penales_ap, fecha = ap
                es_yo = (uname == usuario_filtro)
                pen_ap = "Sí" if penales_ap==1 else "No"
                fecha = fecha [:16]

                if res_e:
                    ganador_real, penales_real = res_e
                    pts = calcular_puntos_elim(ganador_ap, penales_ap, ganador_real, int(penales_real))
                    resultado = f"{ganador_real}{' (penales)' if penales_real==1 else ''}"
                    pts_txt = {3:"🎯 3 pts",2:"🏆 2 pts",1:"🎲 1 pt",0:"❌ 0 pts"}[pts]
                else:
                    resultado = "⏳ Pendiente"
                    pts_txt = "—"

                fila = {"Partido": f"{eq1} vs {eq2}"}
                if not es_admin and cerrado:
                    fila["Quién"] = f"{'👤 Yo' if es_yo else uname}"
                elif es_admin:
                    fila["Usuario"] = uname
                fila["Aposté avanza"] = ganador_ap
                fila["¿Penales?"] = pen_ap
                fila["Resultado oficial"] = resultado
                fila["Puntos"] = pts_txt
                fila["Fecha de apuesta"] = fecha
                filas.append(fila)

            bloques.append((f"{eq1} vs {eq2}", filas, cerrado))

        tiene_algo = any(f for _,f,_ in bloques)
        if not tiene_algo: continue

        expanded = (ronda_sel != "Todas")
        with st.expander(f"**{RONDA_LABEL[ronda]}**", expanded=expanded):
            for nombre, filas, cerrado in bloques:
                if not filas: continue
                estado_icon = "🔒" if cerrado else "🔓"
                st.markdown(f"**{estado_icon} {nombre}**"
                    + ("" if cerrado else " — *Se revelan al publicar el resultado*"))
                st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
                st.markdown("---")


# ─────────────────────────────────────────────
# 5. SESIÓN Y CABECERA
# ─────────────────────────────────────────────
if 'user' not in st.session_state: st.session_state.user=None

st.markdown('<h1 class="main-title">🏆 QUINIELA MUNDIAL 2026</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Sistema de Quinielas — Grupos + Eliminatorias</p>', unsafe_allow_html=True)
st.markdown("""<div class="reglas-container"><div style="text-align:center">
  <span class="regla-item">🎯 EXACTO: 3 PTS</span>
  <span class="regla-item">🏆 GANADOR: 2 PTS</span>
  <span class="regla-item">🤝 EMPATE: 1 PT</span>
  <span class="regla-item" style="color:#7c3aed">⚽ 2a F. GANADOR+PENALES: 3 PTS</span>
  <span class="regla-item" style="color:#7c3aed">⚽ 2a F. GANADOR O EMPATE(PENALES): 2 PTS</span>
  <span class="regla-item" style="color:#7c3aed">🎲 2a F. GANADOR EN PENALES: 1 PT</span>
</div></div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 6. LOGIN
# ─────────────────────────────────────────────
if not st.session_state.user:
    _,col_log,_=st.columns([1,2,1])
    with col_log:
        st.markdown("""<div style="background:linear-gradient(145deg,#1e293b,#0f172a);
            padding:15px 28px;border-radius:24px;border:1px solid #D5D9E0;
            box-shadow:0 25px 50px rgba(0,0,0,0.5)">""", unsafe_allow_html=True)
        opcion=st.radio("",["🔑 Ingresar","📝 Registrarse","🔓 C. Password"],horizontal=True)
        if "Ingresar" in opcion:
            u=st.text_input("Usuario"); p=st.text_input("Contraseña",type="password")
            if st.button("ACCEDER →",use_container_width=True,type="primary"):
                if u=="ADMIN" and p=="MG2026mundial":
                    st.session_state.user="ADMIN"; st.rerun()
                else:
                    conn=conectar_db()
                    row=conn.execute("SELECT password,bloqueado FROM usuarios WHERE username=?",(u,)).fetchone()
                    conn.close()
                    if row and row[0]==hash_pass(p):
                        if row[1]==1: st.error("❌ La cuenta se encuentra bloqueada.")
                        else: st.session_state.user=u; st.rerun()
                    else: st.error("❌ Credenciales inválidas")
        elif "Registrarse" in opcion:
            nu=st.text_input("Nombre corto (Para mostrar e Iniciar Sesión)*"); np=st.text_input("Contraseña (mín. 8 caracteres) *",type="password")
            np2=st.text_input("Confirmar contraseña *",type="password")
            nombre_completo=st.text_input("Nombre completo *"); telefono=st.text_input("Teléfono *")
            if st.button("CREAR CUENTA →",use_container_width=True,type="primary"):
                if not nu.strip(): st.error("⚠️ Usuario obligatorio.")
                elif nu.strip().lower()=="ADMIN": st.error("⚠️ Nombre reservado.")
                elif len(np)<8: st.error("⚠️ Contraseña mínimo 8 caracteres.")
                elif np!=np2: st.error("⚠️ Las contraseñas no coinciden.")
                elif not nombre_completo.strip(): st.error("⚠️ Nombre completo obligatorio.")
                elif not telefono.strip(): st.error("⚠️ Teléfono obligatorio.")
                else:
                    conn=conectar_db()
                    try:
                        if conn.execute("SELECT 1 FROM usuarios WHERE username=?",(nu.strip(),)).fetchone():
                            st.error(f"⚠️ Usuario '{nu.strip()}' ya existe.")
                        else:
                            conn.execute("INSERT INTO usuarios(username,password,nombre_completo,telefono,fecha_registro,bloqueado,pagado,puede_cambiar_pass) VALUES(?,?,?,?,?,0,0,0)",
                                (nu.strip(),hash_pass(np),nombre_completo.strip(),telefono.strip(),str(datetime.datetime.now())))
                            conn.commit()
                            st.success(f"✅ ¡Registro exitoso! Bienvenido, {nombre_completo.strip().split()[0]}!")
                            time.sleep(5); st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
                    finally: conn.close()
        elif "Password" in opcion:
            st.markdown("#### 🔓 Cambiar Contraseña")
            mensaje = st.empty()
            mensaje.warning("⚠️ Para realizar el cambio de contraseña se debe solicitar la autorización del administrador. "
                           "Si ya lo solicitaste, puedes realizar el cambio en esta sección.")
            u_reset = st.text_input("Tu usuario")
            if u_reset:
                conn_r = conectar_db()
                row_r = conn_r.execute(
                    "SELECT puede_cambiar_pass FROM usuarios WHERE username=?", (u_reset.strip(),)
                ).fetchone()
                conn_r.close()
                if not row_r:
                    st.error("❌ Usuario no encontrado.")
                elif row_r[0] != 1:
                    st.warning("⛔ El administrador aún no te ha habilitado el cambio de contraseña.")
                else:
                    st.success("✅ Acceso autorizado. Ingresa tu nueva contraseña.")
                    np1 = st.text_input("Nueva contraseña (mín. 8)", type="password", key="npass1")
                    np2 = st.text_input("Confirmar nueva contraseña", type="password", key="npass2")
                    if st.button("💾 GUARDAR NUEVA CONTRASEÑA", use_container_width=True, type="primary"):
                        mensaje.empty()
                        if len(np1) < 8:
                            st.error("⚠️ Mínimo 8 caracteres.")
                        elif np1 != np2:
                            st.error("⚠️ Las contraseñas no coinciden.")
                        else:
                            conn_r2 = conectar_db()
                            conn_r2.execute(
                                "UPDATE usuarios SET password=?, puede_cambiar_pass=0 WHERE username=?",
                                (hash_pass(np1), u_reset.strip())
                            )
                            conn_r2.commit(); conn_r2.close()
                            st.success("✅ Contraseña actualizada. Ya puedes volver a ingresar.")
                            time.sleep(5); st.rerun()
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
        st.info("Los partidos se bloquean una hora antes de comenzar el encuentro.")
        st.info("Depósitos Banco Azteca 💳 \n Tarjeta: 4027665885774530 \n MIGUEL ANGEL GARDUÑO LOPEZ")    
        conn_usp=conectar_db()                
        df_us=pd.read_sql(
            "SELECT username FROM usuarios WHERE username!='ADMIN'",conn_usp)
        conn_usp.close()
        if df_us.empty: st.info("No hay usuarios registrados.")
        else:
                 total_p = len(df_us) * 100
                 p1 = total_p * 50 / 100
                 p2 = total_p * 30 / 100
                 p3 = total_p * 20 / 100
                 st.markdown(f"""<div class="reglas-container"><div style="text-align:center">
                    <span class="regla-item"> PREMIOS POSIBLES AL MOMENTO: </span>
                    <span class="regla-item" style="color:#2E8B57;font-size:16px"> 🥇 1°: ${format(p1, ",.2f")} </span>
                    <span class="regla-item" style="color:#2E8B57;font-size:16px"> 🥈 2°: ${format(p2, ",.2f")} </span>
                    <span class="regla-item" style="color:#2E8B57;font-size:16px"> 🥉 3°: ${format(p3, ",.2f")} </span>
                    </div></div>""", unsafe_allow_html=True)
        
        
    # ══════════════════════════════════════════
    # USUARIO NORMAL
    # ══════════════════════════════════════════
    if st.session_state.user != "ADMIN":
        tabs=st.tabs(["📝 GRUPOS","📊 POSICIONES","🏆 ELIMINATORIAS","🌟 RANKING","📋 PRONÓSTICOS"])

        # ── GRUPOS ────────────────────────────
        
        with tabs[0]:
            conn=conectar_db()
            for g_id,eqs in grupos.items():
                est_g=conn.execute("SELECT estado FROM estados_grupos WHERE grupo_id=?",(g_id,)).fetchone()[0]
                cerrado_grupo = est_g == 'cerrado'
                st.markdown(f"""<div class="grupo-header">
                    <span>GRUPO {g_id}</span>
                    <span class="grupo-estado">{'🔒 CERRADO' if cerrado_grupo else '🔓 ABIERTO'}</span>
                </div>""", unsafe_allow_html=True)

                for idx,(p1,p2) in enumerate([(0,1),(2,3),(0,2),(1,3),(0,3),(1,2)]):
                    pid=f"{g_id}_{idx}"; tl,tv=eqs[p1],eqs[p2]
                    cerrado=partido_esta_cerrado(conn,pid)
                    rr=conn.execute("SELECT r1,r2 FROM resultados_reales WHERE partido_id=?",(pid,)).fetchone()
                    ap=conn.execute("SELECT g1,g2,es_empate FROM apuestas WHERE usuario=? AND partido_id=?",
                        (st.session_state.user,pid)).fetchone()
                    corrigiendo = st.session_state.get(f"corrigiendo_{pid}", False)

                    card_class = "match-card-cerrado" if cerrado else "match-card"
                    flag_tl = flag_url(tl)
                    flag_tv = flag_url(tv)

                    # Scores a mostrar
                    score_tl = str(ap[0]) if ap else ""
                    score_tv = str(ap[1]) if ap else ""
                    es_emp = ap[2]==1 if ap else False
                    score_class = "score-box score-box-empate" if es_emp else "score-box"

                    # Pre-calcular bloques HTML condicionales (concatenación pura, sin f-strings con llaves)
                    if ap:
                        html_score_tl = '<div class="' + score_class + '" style="margin:6px auto 0;width:fit-content">' + score_tl + '</div>'
                        html_score_tv = '<div class="' + score_class + '" style="margin:6px auto 0;width:fit-content">' + score_tv + '</div>'
                    elif cerrado:
                        html_score_tl = '<div class="badge-sin-apuesta">Sin apuesta</div>'
                        html_score_tv = '<div class="badge-sin-apuesta">Sin apuesta</div>'
                    else:
                        html_score_tl = ''
                        html_score_tv = ''

                    if ap and es_emp and not corrigiendo:
                        html_empate_badge = '<div style="text-align:center;margin-bottom:8px"><span class="badge-empate">🤝 APOSTASTE EMPATE</span></div>'
                    else:
                        html_empate_badge = ''

                    if rr:
                        html_resultado = '<div class="result-oficial"><small>✅ RESULTADO OFICIAL</small>' + str(rr[0]) + ' — ' + str(rr[1]) + '</div>'
                    elif cerrado:
                        html_resultado = '<div style="text-align:center"><span class="badge-cerrado">🔒 Sin resultado aún</span></div>'
                    else:
                        html_resultado = ''

                    banda_estado = '🔒 CERRADO' if cerrado else '🔓 ABIERTO'

                    html_card = (
                        '<div class="' + card_class + '">'
                        + '<div class="match-band">' + banda_estado + ' · ' + tl + ' vs ' + tv + '</div>'
                        + '<div class="match-inner">'
                        + '<div class="teams-row">'
                        + '<div class="team-block">'
                        + '<img src="' + flag_tl + '" class="team-flag">'
                        + '<div class="team-name">' + tl + '</div>'
                        + html_score_tl
                        + '</div>'
                        + '<div class="vs-badge">VS</div>'
                        + '<div class="team-block">'
                        + '<img src="' + flag_tv + '" class="team-flag">'
                        + '<div class="team-name">' + tv + '</div>'
                        + html_score_tv
                        + '</div>'
                        + '</div>'
                        + html_empate_badge
                        + html_resultado
                        + '</div>'
                        + '</div>'
                    )
                    st.markdown(html_card, unsafe_allow_html=True)

                    # Formulario de apuesta (fuera del HTML para que Streamlit lo renderice)
                    if not cerrado and (not ap or corrigiendo):
                        c1,c2=st.columns(2)
                        default_g1 = int(ap[0]) if (ap and corrigiendo) else 0
                        default_g2 = int(ap[1]) if (ap and corrigiendo) else 0
                        g1=c1.number_input(f"⚽ {tl}",0,15,value=default_g1,key=f"g1_{pid}")
                        g2=c2.number_input(f"⚽ {tv}",0,15,value=default_g2,key=f"g2_{pid}")
                        if corrigiendo:
                            ca,cb,cc=st.columns([2,2,2])
                            if ca.button("💾 ACTUALIZAR",key=f"btn_{pid}",use_container_width=True,type="primary"):
                                conn.execute("DELETE FROM apuestas WHERE usuario=? AND partido_id=?",(st.session_state.user,pid))
                                conn.execute("INSERT INTO apuestas VALUES(?,?,?,?,?,?,?)",(st.session_state.user,pid,g1,g2,0,0,str(datetime.datetime.now()-timedelta(hours=6))))
                                conn.commit(); st.session_state.pop(f"corrigiendo_{pid}",None); st.rerun()
                            if cb.button("🤝 Empate",key=f"btn_emp_{pid}",use_container_width=True):
                                conn.execute("DELETE FROM apuestas WHERE usuario=? AND partido_id=?",(st.session_state.user,pid))
                                conn.execute("INSERT INTO apuestas VALUES(?,?,?,?,?,?,?)",(st.session_state.user,pid,g1,g1,1,0,str(datetime.datetime.now()-timedelta(hours=6))))
                                conn.commit(); st.session_state.pop(f"corrigiendo_{pid}",None); st.rerun()
                            if cc.button("❌ Cancelar",key=f"btn_cancel_{pid}",use_container_width=True):
                                st.session_state.pop(f"corrigiendo_{pid}",None); st.rerun()
                        else:
                            ca,cb=st.columns(2)
                            if ca.button("💾 GUARDAR",key=f"btn_{pid}",use_container_width=True,type="primary"):
                                conn.execute("INSERT INTO apuestas VALUES(?,?,?,?,?,?,?)",(st.session_state.user,pid,g1,g2,0,0,str(datetime.datetime.now()-timedelta(hours=6))))
                                conn.commit(); st.rerun()
                            if cb.button("🤝 Apostar Empate",key=f"btn_emp_{pid}",use_container_width=True):
                                conn.execute("INSERT INTO apuestas VALUES(?,?,?,?,?,?,?)",(st.session_state.user,pid,g1,g1,1,0,str(datetime.datetime.now()-timedelta(hours=6))))
                                conn.commit(); st.rerun()

                    elif ap and not cerrado and not corrigiendo:
                        if st.button("✏️ Corregir pronóstico",key=f"btn_corr_{pid}",use_container_width=True):
                            st.session_state[f"corrigiendo_{pid}"] = True; st.rerun()

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
            ca.write("**🥇 1° de grupo:**")
            for e in cl["primeros"]: ca.write(f"• {e}")
            cb.write("**🥈 2° de grupo:**")
            for e in cl["segundos"]: cb.write(f"• {e}")
            cc.write("**🥉 Mejores 3°:**")
            for e in cl["terceros"]: cc.write(f"• {e}")

# ── ELIMINATORIAS (USUARIO) ────────────
        with tabs[2]:
            conn_el=conectar_db()
            st.markdown("### 🏆 Bracket FIFA 2026")
            st.warning("⚠️ Importante: Para apostar al EMPATE en partido primero debes elegir la casilla 'Penales' y después eliges al equipo que avanza ⚠️")

            for ronda in RONDAS:
                matches_ronda = MATCHES_POR_RONDA[ronda]
                _raw = conn_el.execute(
                    "SELECT partido_id,equipo1,equipo2,abierto_apuestas FROM elim_partidos WHERE ronda=?",
                    (ronda,)).fetchall()
                partidos_bd = {}
                for _r in _raw:
                    try: partidos_bd[int(_r[0])] = _r
                    except (ValueError, TypeError): pass

                st.markdown(f'<div class="ronda-header"><span>{RONDA_LABEL[ronda]}</span>'
                    f'<span style="font-size:.9rem;opacity:.8">{len(partidos_bd)}/{len(matches_ronda)} definidos</span>'
                    f'</div>', unsafe_allow_html=True)

                cols_ronda = st.columns(min(len(matches_ronda), 4))
                for ci, mid in enumerate(matches_ronda):
                    with cols_ronda[ci % min(len(matches_ronda), 4)]:
                        if mid in partidos_bd:
                            _,eq1,eq2,abierto = partidos_bd[mid]
                        else:
                            eq1,eq2,abierto = "","",0

                        ambos = bool(eq1 and eq2)
                        ap_e = conn_el.execute(
                            "SELECT ganador,penales FROM elim_apuestas WHERE usuario=? AND partido_id=?",
                            (st.session_state.user, mid)).fetchone()
                        res_e = conn_el.execute(
                            "SELECT ganador,penales FROM elim_resultados WHERE partido_id=?",(mid,)).fetchone()

                        if res_e:
                            border,bg = "#16a34a","#f0fdf4"
                        elif abierto and ambos:
                            border,bg = "#7c3aed","#faf5ff"
                        elif ambos:
                            border,bg = "#f59e0b","#fffbeb"
                        else:
                            border,bg = "#cbd5e1","#f8fafc"

                        res_html = ""
                        if res_e:
                            pen_icon = " 🥅" if res_e[1] else ""
                            res_html = f'<div style="font-size:.7rem;color:#16a34a;font-weight:700;margin-top:4px">✅ {res_e[0]}{pen_icon}</div>'
                        ap_html = ""
                        if ap_e:
                            pen_icon = " 🥅" if ap_e[1] else ""
                            ap_html = f'<div style="font-size:.65rem;color:#7c3aed;margin-top:4px">Aposté: {ap_e[0]}{pen_icon}</div>'

                        st.markdown(f"""
                        <div style="border:2px solid {border};background:{bg};border-radius:12px;
                            padding:12px;margin-bottom:8px;text-align:center;">
                            <div style="font-size:.65rem;font-weight:800;color:#64748b;margin-bottom:4px;">
                                M{mid}
                            </div>
                            <div style="font-size:.85rem;font-weight:700;color:#1e3a8a;">
                                {eq1 if eq1 else "⏳ TBD"}
                            </div>
                            <div style="font-size:.7rem;color:#94a3b8;margin:2px 0;">vs</div>
                            <div style="font-size:.85rem;font-weight:700;color:#1e3a8a;">
                                {eq2 if eq2 else "⏳ TBD"}
                            </div>
                            {res_html}{ap_html}
                        </div>
                        """, unsafe_allow_html=True)

                        if abierto and ambos and not ap_e and not res_e:
                            pen_sel = st.checkbox("¿Penales?(Empate)", key=f"pen_{mid}")
                            if st.button(f"✅ {eq1}", key=f"ev1_{mid}", use_container_width=True):
                                conn_el.execute("INSERT INTO elim_apuestas VALUES(?,?,?,?,?,?)",
                                    (st.session_state.user,mid,eq1,int(pen_sel),0,str(datetime.datetime.now()-timedelta(hours=6))))
                                conn_el.commit(); st.rerun()
                            if st.button(f"✅ {eq2}", key=f"ev2_{mid}", use_container_width=True):
                                conn_el.execute("INSERT INTO elim_apuestas VALUES(?,?,?,?,?,?)",
                                    (st.session_state.user,mid,eq2,int(pen_sel),0,str(datetime.datetime.now()-timedelta(hours=6))))
                                conn_el.commit(); st.rerun()
            conn_el.close()

        # ── RANKING ───────────────────────────
        with tabs[3]:
            st.header("🌟 Ranking General")
            conn_pago=conectar_db()
            row_pago=conn_pago.execute(
                "SELECT pagado FROM usuarios WHERE username=?",(st.session_state.user,)).fetchone()
            conn_pago.close()
            if row_pago and row_pago[0]==0:
                st.warning("⚠️ Tu inscripción aún no ha sido confirmada como pagada. "
                           "Tus puntos no aparecerán en el ranking hasta que el administrador confirme tu pago.")
            else:
                conn_usp=conectar_db()                
                df_usp=pd.read_sql(
                    "SELECT pagado FROM usuarios WHERE username!='ADMIN' and pagado==1",conn_usp)
                conn_usp.close()
                if df_usp.empty: st.info("No hay usuarios registrados.")
                else:
                 total_p = len(df_usp) * 100
                 p1 = total_p * 50 / 100
                 p2 = total_p * 30 / 100
                 p3 = total_p * 20 / 100
                 st.markdown(f"""<div class="reglas-container"><div style="text-align:center">
                    <span class="regla-item"> QUINIELAS PAGADAS:-> </span>
                    <span class="regla-item" style="color:#228B22;font-size:18px"> {len(df_usp)}</span>
                    <span class="regla-item"> PREMIO ASEGURADO: </span>
                    <span class="regla-item" style="color:#2E8B57;font-size:16px"> 🥇 1°: ${format(p1, ",.2f")} </span>
                    <span class="regla-item" style="color:#2E8B57;font-size:16px"> 🥈 2°: ${format(p2, ",.2f")} </span>
                    <span class="regla-item" style="color:#2E8B57;font-size:16px"> 🥉 3°: ${format(p3, ",.2f")} </span>
                    </div></div>""", unsafe_allow_html=True)
                 st.caption(f"Total: **{len(df_usp)}** participantes")
            df_rank=calcular_ranking_global()
            if not df_rank.empty:
                # Tabla HTML completa
                rows_html=""
                ranking = {}
                pos = 0
                ptsA = None
                for i,(_,row) in enumerate(df_rank.iterrows()):
                    pts = row["Pts"]
                    if ptsA is None or pts != ptsA: 
                        pos += 1
                        ptsA = pts
                    medal={1:"🥇",2:"🥈",3:"🥉"}.get(pos,str(pos))
                    es_yo = row["Usuario"] == st.session_state.user
                    bg = "background:#B5C9DE;" if es_yo else ""
                    yo_badge = " 👤" if es_yo else ""
                    rows_html+=f"""<tr style="{bg}">
                      <td style="text-align:center;font-weight:900;font-size:1rem">{medal}</td>
                      <td style="text-align:left;font-weight:800; font-size:1.0rem;color:#2E4D6B;white-space:nowrap">{row["Usuario"]}{yo_badge}</td>
                      <td style="text-align:center;font-weight:900;color:#3b82f6;font-size:1.1rem">{row["Pts"]}</td>
                      <td style="text-align:center;color:#3b82f6;font-size:1.0rem">{row.get("Exacto",0)}</td>
                      <td style="text-align:center;color:#3b82f6;font-size:1.0rem">{row.get("Ganador",0)}</td>
                      <td style="text-align:center;color:#3b82f6;font-size:1.0rem">{row.get("Empate",0)}</td>
                      <td style="text-align:center;color:#7c3aed;font-size:1.0rem">{row.get("Elim G+Pen",0)}</td>
                      <td style="text-align:center;color:#7c3aed;font-size:1.0rem">{row.get("Elim Ganador",0)}</td>
                      <td style="text-align:center;color:#7c3aed;font-size:1.0rem">{row.get("Elim Pen/No",0)}</td>
                    </tr>"""

                st.markdown(f"""
                <div style="overflow-x:auto;background:#EDF2F7;border-radius:16px;
                    border:1px solid #334155;padding:4px;">
                  <table style="width:100%;border-collapse:collapse;font-size:.8rem;color:#4E5B5C;">
                    <thead>
                      <tr style="border-bottom:2px solid #334155;">
                        <th style="padding:10px 8px;text-align:center;color:#64748b;font-size:.80rem;letter-spacing:1px;white-space:nowrap">POS</th>
                        <th style="padding:10px 8px;text-align:left;color:#64748b;font-size:.80rem;letter-spacing:1px">JUGADOR</th>
                        <th style="padding:10px 8px;text-align:center;color:#3b82f6;font-size:.80rem;letter-spacing:1px">PTS</th>
                        <th style="padding:10px 6px;text-align:center;color:#3b82f6;font-size:.7rem;white-space:nowrap">🎯<br>Exacto<br><span style="color:#475569">3pts</span></th>
                        <th style="padding:10px 6px;text-align:center;color:#3b82f6;font-size:.7rem;white-space:nowrap">🏆<br>Ganador<br><span style="color:#475569">2pts</span></th>
                        <th style="padding:10px 6px;text-align:center;color:#3b82f6;font-size:.7rem;white-space:nowrap">🤝<br>Empate<br><span style="color:#475569">1pt</span></th>
                        <th style="padding:10px 6px;text-align:center;color:#7c3aed;font-size:.7rem;white-space:nowrap">⚽<br>2F G+Pen<br><span style="color:#475569">3pts</span></th>
                        <th style="padding:10px 6px;text-align:center;color:#7c3aed;font-size:.7rem;white-space:nowrap">⚽<br>2F Ganador<br><span style="color:#475569">2pts</span></th>
                        <th style="padding:10px 6px;text-align:center;color:#7c3aed;font-size:.7rem;white-space:nowrap">🎲<br>2F G. Pen<br><span style="color:#475569">1pt</span></th>
                      </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                  </table>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Aún no hay puntos registrados.")

        # ── MIS APUESTAS ──────────────────────
        with tabs[4]:
            st.header("📋 Pronósticos")
            conn_ap=conectar_db()
            tab_mg, tab_me = st.tabs(["⚽ Fase de Grupos","🏆 Eliminatorias"])
            with tab_mg:
                render_auditoria_grupos(conn_ap, usuario_filtro=st.session_state.user)
            with tab_me:
                render_auditoria_eliminatorias(conn_ap, usuario_filtro=st.session_state.user)
            conn_ap.close()

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
            st.subheader("🏆 Gestión del Bracket FIFA 2026")
            st.info("""
            **Flujo automático de nodos:**
            1. En **32avos** defines los 16 equipos (1 por slot) — son los clasificados de grupos.
            2. Al grabar cada resultado, el sistema **inyecta al ganador** en el nodo correcto de la siguiente ronda.
            3. Activa apuestas con 🔓 cuando quieras abrir cada partido.
            4. **Semifinales**: el perdedor se inyecta automáticamente en el M103 (Tercer Lugar).
            """)

            elim_tabs = st.tabs(RONDAS)
            for ti, ronda in enumerate(RONDAS):
                with elim_tabs[ti]:
                    st.markdown(f"#### {RONDA_LABEL[ronda]}")
                    matches_ronda = MATCHES_POR_RONDA[ronda]

                    for mid in matches_ronda:
                        p = conn.execute(
                            "SELECT partido_id,equipo1,equipo2,abierto_apuestas FROM elim_partidos WHERE CAST(partido_id AS INTEGER)=?",
                            (int(mid),)).fetchone()

                        if p:
                            _,eq1,eq2,abierto = p
                        else:
                            eq1,eq2,abierto = "","",0

                        res_e = conn.execute(
                            "SELECT ganador,penales FROM elim_resultados WHERE partido_id=?",(mid,)).fetchone()

                        desc = MATCH_DESC.get(mid, f"Partido {mid}")
                        estado = "🔒 Resultado grabado" if res_e else ("🔓 Apuestas abiertas" if abierto else "⏸️ Cerrado")
                        st.markdown(f"**M{mid}: {desc}** — {estado}")

                        if ronda == "32avos" and not res_e:
                            c_e1, c_e2 = st.columns(2)
                            eq1_inp = c_e1.text_input(f"Equipo 1 (M{mid})", value=eq1, key=f"inp_e1_{mid}")
                            eq2_inp = c_e2.text_input(f"Equipo 2 (M{mid})", value=eq2, key=f"inp_e2_{mid}")
                            if st.button(f"💾 Guardar equipos M{mid}", key=f"save_eq_{mid}"):
                                conn.execute("""INSERT OR IGNORE INTO elim_partidos
                                    (partido_id,ronda,num_partido,equipo1,equipo2,abierto_apuestas)
                                    VALUES(?,?,?,?,?,0)""", (mid,ronda,mid,eq1_inp.strip(),eq2_inp.strip()))
                                conn.execute("UPDATE elim_partidos SET equipo1=?,equipo2=? WHERE partido_id=?",
                                             (eq1_inp.strip(),eq2_inp.strip(),mid))
                                conn.commit(); st.rerun()

                        if res_e:
                            pen_txt = " (penales)" if res_e[1]==1 else ""
                            st.success(f"✅ Clasificó: **{res_e[0]}**{pen_txt}")
                            if st.button(f"✏️ Corregir M{mid}", key=f"corr_{mid}"):
                                if mid in LLAVE_AVANCE:
                                    mdest, slot = LLAVE_AVANCE[mid]
                                    col = "equipo1" if slot==1 else "equipo2"
                                    conn.execute(f"UPDATE elim_partidos SET {col}='' WHERE partido_id=?", (mdest,))
                                if mid in LLAVE_PERDEDOR:
                                    mdest, slot = LLAVE_PERDEDOR[mid]
                                    col = "equipo1" if slot==1 else "equipo2"
                                    conn.execute(f"UPDATE elim_partidos SET {col}='' WHERE partido_id=?", (mdest,))
                                conn.execute("DELETE FROM elim_resultados WHERE partido_id=?",(mid,))
                                conn.execute("UPDATE elim_partidos SET abierto_apuestas=1 WHERE partido_id=?",(mid,))
                                conn.commit(); st.rerun()
                        elif eq1 and eq2:
                            c_ab, c_g, c_p, c_sv = st.columns([2,3,2,2])
                            lbl_ab = "⏸️ Cerrar apuestas" if abierto else "🔓 Abrir apuestas"
                            if c_ab.button(lbl_ab, key=f"ab_{mid}", use_container_width=True):
                                conn.execute("""INSERT OR IGNORE INTO elim_partidos
                                    (partido_id,ronda,num_partido,equipo1,equipo2,abierto_apuestas)
                                    VALUES(?,?,?,?,?,0)""", (mid,ronda,mid,eq1,eq2))
                                conn.execute("UPDATE elim_partidos SET abierto_apuestas=? WHERE partido_id=?",
                                             (0 if abierto else 1, mid))
                                conn.commit(); st.rerun()
                            gan_sel = c_g.selectbox("Ganador", ["",eq1,eq2], key=f"gan_{mid}")
                            pen_sel = c_p.checkbox("¿Penales?", key=f"pen_{mid}")
                            if c_sv.button("Grabar resultado", key=f"gsv_{mid}", use_container_width=True):
                                if gan_sel:
                                    perdedor = eq2 if gan_sel==eq1 else eq1
                                    conn.execute("INSERT OR REPLACE INTO elim_resultados VALUES(?,?,?)",
                                                 (mid,gan_sel,int(pen_sel)))
                                    conn.execute("UPDATE elim_partidos SET abierto_apuestas=0 WHERE partido_id=?",(mid,))
                                    conn.commit()
                                    avanzar_ganador(conn, mid, gan_sel, perdedor)
                                    st.success(f"✅ M{mid}: Clasificó **{gan_sel}** → nodo siguiente actualizado")
                                    st.rerun()
                                else:
                                    st.warning("Selecciona el ganador.")
                        else:
                            st.caption("⏳ Esperando equipos de la ronda anterior.")
                        st.divider()

        # ── RANKING ───────────────────────────
        with a_tabs[3]:
            st.subheader("Ranking General")
            if st.button("🔄 Actualizar"): st.rerun()
            conn_usp=conectar_db()                
            df_usp=pd.read_sql(
                    "SELECT pagado FROM usuarios WHERE username!='ADMIN' and pagado==1",conn_usp)
            conn_usp.close()
            if df_usp.empty: st.info("No hay usuarios registrados.")
            else:
                 total_p = len(df_usp) * 100
                 p1 = total_p * 50 / 100
                 p2 = total_p * 30 / 100
                 p3 = total_p * 20 / 100
                 st.markdown(f"""<div class="reglas-container"><div style="text-align:center">
                    <span class="regla-item"> QUINIELAS PAGADAS:-> </span>
                    <span class="regla-item" style="color:#228B22;font-size:18px"> {len(df_usp)}</span>
                    <span class="regla-item"> PREMIO ASEGURADO: </span>
                    <span class="regla-item" style="color:#2E8B57;font-size:16px"> 🥇 1°: ${format(p1, ",.2f")} </span>
                    <span class="regla-item" style="color:#2E8B57;font-size:16px"> 🥈 2°: ${format(p2, ",.2f")} </span>
                    <span class="regla-item" style="color:#2E8B57;font-size:16px"> 🥉 3°: ${format(p3, ",.2f")} </span>
                    </div></div>""", unsafe_allow_html=True)
                 st.caption(f"Total: **{len(df_usp)}** participantes")
            df_rank=calcular_ranking_global()
            if not df_rank.empty:
                # Tabla HTML completa
                rows_html=""
                ranking = {}
                pos = 0
                ptsA = None
                for i,(_,row) in enumerate(df_rank.iterrows()):
                    pts = row["Pts"]
                    if ptsA is None or pts != ptsA: 
                        pos += 1
                        ptsA = pts
                    medal={1:"🥇",2:"🥈",3:"🥉"}.get(pos,str(pos))
                    es_yo = row["Usuario"] == st.session_state.user
                    bg = "background:#B5C9DE;" if es_yo else ""
                    yo_badge = " 👤" if es_yo else ""
                    rows_html+=f"""<tr style="{bg}">
                      <td style="text-align:center;font-weight:900;font-size:1rem">{medal}</td>
                      <td style="text-align:left;font-weight:800;color:#2E4D6B;white-space:nowrap">{row["Usuario"]}{yo_badge}</td>
                      <td style="text-align:center;font-weight:900;color:#3b82f6;font-size:1.1rem">{row["Pts"]}</td>
                      <td style="text-align:center;color:#3b82f6;font-size:1.0rem">{row.get("Exacto",0)}</td>
                      <td style="text-align:center;color:#3b82f6;font-size:1.0rem">{row.get("Ganador",0)}</td>
                      <td style="text-align:center;color:#3b82f6;font-size:1.0rem">{row.get("Empate",0)}</td>
                      <td style="text-align:center;color:#7c3aed;font-size:1.0rem">{row.get("Elim G+Pen",0)}</td>
                      <td style="text-align:center;color:#7c3aed;font-size:1.0rem">{row.get("Elim Ganador",0)}</td>
                      <td style="text-align:center;color:#7c3aed;font-size:1.0rem">{row.get("Elim Pen/No",0)}</td>
                    </tr>"""

                st.markdown(f"""
                <div style="overflow-x:auto;background:#EDF2F7;border-radius:16px;
                    border:1px solid #334155;padding:4px;">
                  <table style="width:100%;border-collapse:collapse;font-size:.8rem;color:#cbd5e1;">
                    <thead>
                      <tr style="border-bottom:2px solid #334155;">
                        <th style="padding:10px 8px;text-align:center;color:#64748b;font-size:.80rem;letter-spacing:1px;white-space:nowrap">POS</th>
                        <th style="padding:10px 8px;text-align:left;color:#64748b;font-size:.80rem;letter-spacing:1px">JUGADOR</th>
                        <th style="padding:10px 8px;text-align:center;color:#3b82f6;font-size:.80rem;letter-spacing:1px">PTS</th>
                        <th style="padding:10px 6px;text-align:center;color:#3b82f6;font-size:.6rem;white-space:nowrap">🎯<br>Exacto<br><span style="color:#475569">3pts</span></th>
                        <th style="padding:10px 6px;text-align:center;color:#3b82f6;font-size:.6rem;white-space:nowrap">🏆<br>Ganador<br><span style="color:#475569">2pts</span></th>
                        <th style="padding:10px 6px;text-align:center;color:#3b82f6;font-size:.6rem;white-space:nowrap">🤝<br>Empate<br><span style="color:#475569">1pt</span></th>
                        <th style="padding:10px 6px;text-align:center;color:#7c3aed;font-size:.6rem;white-space:nowrap">⚽<br>2F G+Pen<br><span style="color:#475569">3pts</span></th>
                        <th style="padding:10px 6px;text-align:center;color:#7c3aed;font-size:.6rem;white-space:nowrap">⚽<br>2F Ganador<br><span style="color:#475569">2pts</span></th>
                        <th style="padding:10px 6px;text-align:center;color:#7c3aed;font-size:.6rem;white-space:nowrap">🎲<br>2F G. Pen<br><span style="color:#475569">1pt</span></th>
                      </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                  </table>
                </div>
                """, unsafe_allow_html=True)                  
            else:
                st.info("Aún no hay puntos registrados.")
        # ── USUARIOS ──────────────────────────
        with a_tabs[4]:
            st.subheader("Gestión de Usuarios")
            df_us=pd.read_sql(
                "SELECT username,nombre_completo,telefono,fecha_registro,bloqueado,pagado,puede_cambiar_pass FROM usuarios WHERE username!='ADMIN' ORDER BY fecha_registro DESC",conn)
            if df_us.empty: st.info("No hay usuarios registrados.")
            else:
                st.caption(f"Total: **{len(df_us)}** participantes")
                for _,row in df_us.iterrows():
                    uname=row['username']
                    nombre_c=row.get('nombre_completo','') or ''
                    telefono_c=row.get('telefono','') or ''
                    bloq=int(row['bloqueado']); pagado=int(row.get('pagado',0)); reseteo=int(row.get('puede_cambiar_pass',0))
                    fecha=row['fecha_registro'][:10] if row['fecha_registro'] else "—"
                    n_ap=conn.execute("SELECT COUNT(*) FROM apuestas WHERE usuario=?",(uname,)).fetchone()[0]
                    n_el=conn.execute("SELECT COUNT(*) FROM elim_apuestas WHERE usuario=?",(uname,)).fetchone()[0]
                    ci,cb2,cp,cd,cpw=st.columns([4,2,2,2,2])
                    with ci:
                        estado_acc  = "🔴 Bloqueado" if bloq   else "🟢 Activo"
                        estado_pago = "💰 Pagado"    if pagado else "⏳ Sin pagar"
                        st.markdown(
                            f"**{uname}** — {estado_acc} — {estado_pago}<br>"
                            f'<span style="color:#475569;font-size:.85rem">'
                            f"👤 {nombre_c} &nbsp;|&nbsp; 📱 {telefono_c}</span><br>"
                            f'<span style="color:#94a3b8;font-size:.75rem">'
                            f"Registro: {fecha} | Grupos:{n_ap} | Elim:{n_el}</span>",
                            unsafe_allow_html=True)
                    with cb2:
                        if st.button("🔓 Desbloquear" if bloq else "🚫 Bloquear",
                                     key=f"blq_{uname}",use_container_width=True):
                            conn.execute("UPDATE usuarios SET bloqueado=? WHERE username=?",
                                         (0 if bloq else 1,uname))
                            conn.commit(); st.rerun()
                    with cp:
                        lbl_pago = "❌ Quitar pago" if pagado else "💰 Marcar pagado"
                        if st.button(lbl_pago,key=f"pag_{uname}",use_container_width=True):
                            conn.execute("UPDATE usuarios SET pagado=? WHERE username=?",
                                         (0 if pagado else 1,uname))
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
                            
                    with cpw:
                        lbl_pass = "❌ Quitar reset" if reseteo else "🔐 Reset Pass"
                        if st.button(lbl_pass,key=f"respw_{uname}",use_container_width=True):
                            conn.execute("UPDATE usuarios SET puede_cambiar_pass=? WHERE username=?",
                                         (0 if reseteo else 1,uname))
                            conn.commit(); st.rerun()
                            
                    st.divider()

        # ── AUDITORÍA ─────────────────────────
        with a_tabs[5]:
            st.subheader("Auditoría de Apuestas")
            tg,te=st.tabs(["Fase de Grupos","Eliminatorias"])
            with tg:
                render_auditoria_grupos(conn, usuario_filtro=None)
            with te:
                render_auditoria_eliminatorias(conn, usuario_filtro=None)
        conn.close()
