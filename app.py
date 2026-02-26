import streamlit as st
import json, os, requests, re, time, random, string
from fractions import Fraction

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

# ---------- CONFIG ----------
SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"

# ---------- HELPERS ----------
def new_id():
    return "r_" + str(int(time.time())) + "_" + "".join(random.choices(string.ascii_lowercase+string.digits, k=4))

def parse_bool(val):
    # SheetDB vrací vše jako text, musíme boolean převést správně
    if isinstance(val, bool): return val
    if isinstance(val, str): return val.lower() == "true"
    return False

# ---------- DATABASE API (SheetDB) ----------
def load_db():
    try:
        r = requests.get(SDB_URL, timeout=5)
        if r.status_code == 200:
            data = r.json()
            # Pokud API vrátí dict s chybou místo seznamu receptů
            if isinstance(data, dict) and "error" in data:
                return []
            for x in data:
                x["portions"] = int(x.get("portions", 4))
                x["fav"] = parse_bool(x.get("fav", False))
            return data
    except Exception:
        pass
    return []

def api_add(recipe):
    try: 
        # Zabalíme recept do [] - SheetDB to má raději
        r = requests.post(SDB_URL, json={"data": [recipe]}, timeout=5)
        if r.status_code not in (200, 201):
            st.error(f"Chyba při ukládání: {r.text}")
    except Exception as e: 
        st.error(f"Chyba připojení při ukládání: {e}")

def api_update(recipe_id, updated_data):
    try: 
        requests.put(f"{SDB_URL}/id/{recipe_id}", json={"data": updated_data}, timeout=5)
    except Exception: pass

def api_delete(recipe_id):
    try: 
        requests.delete(f"{SDB_URL}/id/{recipe_id}", timeout=5)
    except Exception: pass

def migrate_local_to_cloud(local_data):
    try: 
        r = requests.post(SDB_URL, json={"data": local_data}, timeout=10)
        if r.status_code in (200, 201):
            st.success("Tvoje staré recepty byly úspěšně překopírovány do Google Tabulky! 🎉")
        else:
            st.error(f"Nepodařilo se přesunout staré recepty: {r.text}")
    except Exception as e: 
        st.error(f"Chyba při komunikaci s tabulkou: {e}")

# ---------- INITIALIZATION & MIGRATION ----------
if "recipes" not in st.session_state:
    cloud_data = load_db()
    
    # Pokud je cloud prázdný, zkusíme načíst lokální JSON a nahrát ho tam
    if not cloud_data and os.path.exists(LOCAL_FILE):
        try:
            with open(LOCAL_FILE, "r", encoding="utf8") as f:
                local_data = json.load(f)
            if local_data:
                migrate_local_to_cloud(local_data)
                cloud_data = local_data
        except Exception:
            pass
            
    st.session_state.recipes = cloud_data

if "show_new" not in st.session_state: st.session_state.show_new = False
if "show_search" not in st.session_state: st.session_state.show_search = False

# ---------- STYLE ----------
st.markdown("""
<style>
/* Odstranění horní mezery, headeru a zbytečných linek */
header, hr, [data-testid="stHeader"] {display:none!important;}
.block-container {padding-top: 1rem !important;}

body, [data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at bottom, #000428, #004e92);
    color: white;
}

.title {
    font-size: 28px;
    text-align: center;
    color: #00ccff;
    margin-bottom: 20px;
    font-weight: 700;
}

.topbar {
    display: flex;
    justify-content: flex-start;
    gap: 10px;
    margin-bottom: 15px;
}

button {
    border-radius: 10px !important;
    transition: .15s;
}
button:hover {transform: scale(1.05)}

.ingredients p {
    margin: 0;
    line-height: 1.2;
    font-size: 15px;
}
</style>
""", unsafe_allow_html=True)

# ---------- TOP UI ----------
st.markdown('<div class="topbar">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 1, 4])
with c1:
    if st.button("➕ Nový"): st.session_state.show_new = not st.session_state.show_new
with c2:
    if st.button("🔍 Hledat"): st.session_state.show_search = not st.session_state.show_search
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="title">Márova kuchařka</div>', unsafe_allow_html=True)

# ---------- SEARCH ----------
search = ""
if st.session_state.show_search:
    search = st.text_input("Hledat recept podle názvu nebo ingredience:").lower()

# ---------- CONVERSION (Zobrazování) ----------
unit_map = {"ml":1, "l":1000, "g":1, "kg":1000, "lžíce":15, "lžička":5, "hrnek":240, "cup":240}
density = {"voda":1, "mléko":1.03, "olej":0.92, "med":1.42}
ignore_units = ["ks", "kus", "vejce", "špetka", "trochu"]

def parse_qty(q):
    try: return float(sum(Fraction(x) for x in q.replace(",",".").split()))
    except Exception:
        try: return float(q)
        except Exception: return None

def convert_line(line):
    line = line.strip()
    m = re.match(r"([\d\/\.,\s]+)\s*([^\d\s]+)?\s*(.*)", line)
    if not m: return line
    qty, unit, name = m.groups()
    val = parse_qty(qty)
    if val is None: return line
    if unit and unit.lower() in ignore_units: return line
    coef = unit_map.get((unit or "").lower(), 1)
    coef *= density.get(name.lower().strip(), 1)
    if coef == 1: return line
    return f"**{round(val*coef)} g** {name.strip()} *(původně: {line})*" # Ukáže i původní hodnotu

def convert_text(t):
    return "\n".join(convert_line(l) for l in t.splitlines() if l.strip())

# ---------- ACTION HANDLERS ----------
def toggle_fav(recipe):
    recipe["fav"] = not recipe.get("fav", False)
    api_update(recipe["id"], {"fav": recipe["fav"]})

def delete_recipe(recipe):
    st.session_state.recipes.remove(recipe)
    api_delete(recipe["id"])

# ---------- NEW RECIPE FORM ----------
if st.session_state.show_new:
    st.markdown("### 📝 Nový recept")
    with st.form("new_recipe_form", clear_on_submit=True):
        n = st.text_input("Název")
        typ = st.radio("Typ", ["sladké", "slané"], horizontal=True)
        por = st.number_input("Porce", 1, 20, 4)
        ing = st.text_area("Ingredience (co řádek, to položka)")
        steps = st.text_area("Postup")
        
        if st.form_submit_button("✅ Uložit recept"):
            new_r = {
                "id": new_id(),
                "name": n or "Bez názvu",
                "type": typ,
                "portions": por,
                "ingredients": ing, # Ukládáme originální text!
                "steps": steps,
                "fav": False
            }
            st.session_state.recipes.insert(0, new_r)
            api_add(new_r)
            st.session_state.show_new = False
            st.rerun()

# ---------- SORT ----------
recipes_sorted = sorted(
    st.session_state.recipes,
    key=lambda x: (not x.get("fav", False), x.get("name", ""))
)

# ---------- DISPLAY ----------
for r in recipes_sorted:
    text = (r.get("name","") + r.get("ingredients","") + r.get("type","")).lower()
    if search and search not in text:
        continue

    title = ("⭐ " + r.get("name", "")) if r.get("fav") else r.get("name", "")

    with st.expander(title):
        # Unikátní klíč pro uchování stavu editace konkrétního receptu
        edit_key = f"edit_{r['id']}"
        if edit_key not in st.session_state:
            st.session_state[edit_key] = False

        if st.session_state[edit_key]:
            # EDITOVACÍ FORMULÁŘ
            with st.form(f"form_{r['id']}"):
                en = st.text_input("Název", r.get("name", ""))
                et = st.radio("Typ", ["sladké", "slané"], index=0 if r.get("type")=="sladké" else 1)
                ep = st.number_input("Porce", 1, 20, int(r.get("portions", 4)))
                ei = st.text_area("Ingredience", r.get("ingredients", ""))
                es = st.text_area("Postup", r.get("steps", ""))

                if st.form_submit_button("💾 Uložit změny"):
                    r.update({"name": en, "type": et, "portions": ep, "ingredients": ei, "steps": es})
                    api_update(r["id"], r)
                    st.session_state[edit_key] = False
                    st.rerun()
                    
            if st.button("❌ Zrušit úpravy", key=f"cancel_{r['id']}"):
                st.session_state[edit_key] = False
                st.rerun()

        else:
            # ZOBRAZENÍ RECEPTU
            st.markdown("**Ingredience:**")
            html = "<div class='ingredients'>"
            for l in convert_text(r.get("ingredients", "")).splitlines():
                html += f"<p>• {l}</p>"
            html += "</div><br>"
            st.markdown(html, unsafe_allow_html=True)

            st.markdown("**Postup:**")
            for l in r.get("steps", "").splitlines():
                if l.strip():
                    st.markdown(l)

            st.divider()
            
            # Tlačítka pro akce
            c1, c2, c3 = st.columns(3)
            with c1:
                fav_label = "Odstranit z oblíbených" if r.get("fav") else "⭐ Přidat do oblíbených"
                if st.button(fav_label, key=r["id"]+"f"):
                    toggle_fav(r)
                    st.rerun()
            with c2:
                if st.button("✏️ Upravit", key=r["id"]+"e"):
                    st.session_state[edit_key] = True
                    st.rerun()
            with c3:
                if st.button("🗑 Smazat", key=r["id"]+"d"):
                    delete_recipe(r)
                    st.rerun()
