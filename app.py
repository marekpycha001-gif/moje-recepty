import streamlit as st
import json, os, re, time, random, string
import requests
from fractions import Fraction
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from bs4 import BeautifulSoup
from PIL import Image

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

# ---------- GOOGLE SHEETS PŘIPOJENÍ ----------
@st.cache_resource
def init_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    s_creds = json.loads(st.secrets["google_json"], strict=False)
    s_creds["private_key"] = s_creds["private_key"].replace("\\n", "\n")
    
    creds = Credentials.from_service_account_info(s_creds, scopes=scopes)
    client = gspread.authorize(creds)
    
    sheet = client.open("Moje Kuchařka").sheet1
    
    if not sheet.row_values(1):
        headers = ["id", "name", "type", "portions", "ingredients", "steps", "fav"]
        sheet.append_row(headers)
        
    return sheet

try:
    sheet = init_connection()
except Exception as e:
    st.error(f"Nepodařilo se připojit k tabulce. Detail chyby: {e}")
    st.stop()

# ---------- HELPERS ----------
def new_id():
    return "r_" + str(int(time.time())) + "_" + "".join(random.choices(string.ascii_lowercase+string.digits, k=4))

# ---------- DATABASE API (Google Sheets) ----------
def load_db():
    try:
        records = sheet.get_all_records()
        for x in records:
            x["portions"] = int(x.get("portions", 4) or 4)
            x["fav"] = str(x.get("fav", "")).lower() == "true"
        return records
    except Exception as e:
        st.error(f"Chyba při stahování dat: {e}")
        return []

def api_add(recipe):
    try:
        row = [
            recipe.get("id", ""),
            recipe.get("name", ""),
            recipe.get("type", ""),
            recipe.get("portions", ""),
            recipe.get("ingredients", ""),
            recipe.get("steps", ""),
            str(recipe.get("fav", False))
        ]
        sheet.append_row(row)
    except Exception as e: 
        st.error(f"Chyba při ukládání do tabulky: {e}")

def api_update(recipe_id, updated_data):
    try:
        cell = sheet.find(recipe_id, in_column=1)
        if cell:
            row_idx = cell.row
            row_data = [
                updated_data.get("id", recipe_id),
                updated_data.get("name", ""),
                updated_data.get("type", ""),
                updated_data.get("portions", ""),
                updated_data.get("ingredients", ""),
                updated_data.get("steps", ""),
                str(updated_data.get("fav", False))
            ]
            sheet.update(f"A{row_idx}:G{row_idx}", [row_data])
    except Exception as e:
        st.error(f"Chyba při úpravě receptu: {e}")

def api_delete(recipe_id):
    try:
        cell = sheet.find(recipe_id, in_column=1)
        if cell:
            sheet.delete_rows(cell.row)
    except Exception as e:
        st.error(f"Chyba při mazání receptu: {e}")

# ---------- INITIALIZATION ----------
if "recipes" not in st.session_state:
    st.session_state.recipes = load_db()

if "show_new" not in st.session_state: st.session_state.show_new = False
if "show_search" not in st.session_state: st.session_state.show_search = False

# ---------- STYLE ----------
st.markdown("""
<style>
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

# ---------- SEARCH & FILTER ----------
search = ""
filter_type = "Vše"

if st.session_state.show_search:
    search = st.text_input("Hledat recept podle názvu nebo ingredience:").lower()
    filter_type = st.radio("Zobrazit:", ["Vše", "Slané", "Sladké"], horizontal=True)
    st.divider()

# ---------- CONVERSION (Zobrazování & Přepočet porcí) ----------
unit_map = {"ml":1, "l":1000, "g":1, "kg":1000, "lžíce":15, "lžička":5, "hrnek":240, "cup":240}
density = {"voda":1, "mléko":1.03, "olej":0.92, "med":1.42}
ignore_units = ["ks", "kus", "vejce", "špetka", "trochu"]

def parse_qty(q):
    try: return float(sum(Fraction(x) for x in q.replace(",",".").split()))
    except Exception:
        try: return float(q)
        except Exception: return None

def convert_line(line, multiplier=1.0):
    line = line.strip()
    m = re.match(r"([\d\/\.,\s]+)\s*([^\d\s]+)?\s*(.*)", line)
    if not m: return line
    qty, unit, name = m.groups()
    val = parse_qty(qty)
    if val is None: return line
    
    # Aplikace přepočtu podle porcí
    val = val * multiplier
    
    # Pomocná funkce pro oříznutí desetinných míst, pokud je to celé číslo
    def fmt(v): return int(v) if v == int(v) else round(v, 1)

    if unit and unit.lower() in ignore_units: 
        return f"**{fmt(val)} {unit}** {name}"
        
    coef = unit_map.get((unit or "").lower(), 1)
    coef *= density.get(name.lower().strip(), 1)
    
    if coef == 1: 
        unit_str = f" {unit}" if unit else ""
        return f"**{fmt(val)}{unit_str}** {name}"
        
    return f"**{fmt(val*coef)} g** {name.strip()} *(původně: {line})*"

def convert_text(t, multiplier=1.0):
    return "\n".join(convert_line(l, multiplier) for l in t.splitlines() if l.strip())

# ---------- ACTION HANDLERS ----------
def toggle_fav(recipe):
    recipe["fav"] = not recipe.get("fav", False)
    api_update(recipe["id"], {"fav": recipe["fav"]})

def delete_recipe(recipe):
    st.session_state.recipes.remove(recipe)
    api_delete(recipe["id"])

# ---------- NEW RECIPE FORM (AI ENHANCED) ----------
if st.session_state.show_new:
    st.markdown("### 📝 Nový recept")
    
    ai_ready = "gemini_api_key" in st.secrets
    if ai_ready:
        genai.configure(api_key=st.secrets["gemini_api_key"])
        ai_model = genai.GenerativeModel('gemini-2.5-flash')
    
    system_prompt = """Jsi expert na extrakci receptů. Z poskytnutého textu nebo obrázku vytáhni recept.
    Vrať výsledek POUZE jako validní JSON formát s těmito přesnými klíči:
    "name" (text, název jídla),
    "type" (text, přesně buď "slané" nebo "sladké"),
    "portions" (číslo, odhadni porce, výchozí 4),
    "ingredients" (text, každá surovina na nový řádek),
    "steps" (text, očíslované kroky přípravy, každý na nový řádek)."""

    def process_ai_response(response_text):
        try:
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            if isinstance(data, list):
                if len(data) > 0: data = data[0]
                else: return None
            return data
        except Exception as e:
            st.error(f"Nepodařilo se zpracovat odpověď od AI. Detail: {e}")
            return None

    tab1, tab2, tab3 = st.tabs(["✍️ Ručně", "🔗 Z odkazu", "📸 Z fotky"])

    with tab1:
        with st.form("new_recipe_form_manual", clear_on_submit=True):
            n = st.text_input("Název")
            typ = st.radio("Typ", ["slané", "sladké"], horizontal=True)
            por = st.number_input("Porce", 1, 20, 4)
            ing = st.text_area("Ingredience (co řádek, to položka)")
            steps = st.text_area("Postup")
            
            if st.form_submit_button("✅ Uložit recept"):
                new_r = {
                    "id": new_id(), "name": n or "Bez názvu", "type": typ,
                    "portions": por, "ingredients": ing, "steps": steps, "fav": False
                }
                st.session_state.recipes.insert(0, new_r)
                api_add(new_r)
                st.session_state.show_new = False
                st.rerun()

    with tab2:
        if not ai_ready:
            st.warning("Nastav 'gemini_api_key' v Secrets.")
        else:
            url_input = st.text_input("Vlož URL adresu receptu:")
            if st.button("🪄 Vytěžit recept z webu"):
                if url_input:
                    with st.spinner("Pracuji na tom..."):
                        try:
                            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                            res = requests.get(url_input, headers=headers, timeout=10)
                            soup = BeautifulSoup(res.content, 'html.parser')
                            raw_text = soup.get_text(separator='\n', strip=True)
                            
                            response = ai_model.generate_content(
                                f"{system_prompt}\n\nZde je text z webu:\n{raw_text}",
                                generation_config={"response_mime_type": "application/json"}
                            )
                            parsed_data = process_ai_response(response.text)
                            
                            if parsed_data:
                                parsed_data["id"] = new_id()
                                parsed_data["fav"] = False
                                st.session_state.recipes.insert(0, parsed_data)
                                api_add(parsed_data)
                                st.session_state.show_new = False
                                st.rerun()
                        except Exception as e:
                            st.error(f"Chyba při stahování: {e}")

    with tab3:
        if not ai_ready:
            st.warning("Nastav 'gemini_api_key' v Secrets.")
        else:
            uploaded_file = st.file_uploader("Nahrát obrázek", type=["png", "jpg", "jpeg", "webp"])
            if uploaded_file and st.button("🪄 Přečíst z obrázku"):
                with st.spinner("AI studuje obrázek..."):
                    try:
                        img = Image.open(uploaded_file)
                        response = ai_model.generate_content(
                            [system_prompt, img],
                            generation_config={"response_mime_type": "application/json"}
                        )
                        parsed_data = process_ai_response(response.text)
                        
                        if parsed_data:
                            parsed_data["id"] = new_id()
                            parsed_data["fav"] = False
                            st.session_state.recipes.insert(0, parsed_data)
                            api_add(parsed_data)
                            st.session_state.show_new = False
                            st.rerun()
                    except Exception as e:
                        st.error(f"Chyba při čtení obrázku: {e}")

# ---------- SORT ----------
recipes_sorted = sorted(
    st.session_state.recipes,
    key=lambda x: (not x.get("fav", False), x.get("name", ""))
)

# ---------- DISPLAY ----------
for r in recipes_sorted:
    # Filtrování
    text = (r.get("name","") + r.get("ingredients","") + r.get("type","")).lower()
    if search and search not in text:
        continue
        
    if filter_type != "Vše":
        if r.get("type", "").lower() != filter_type.lower():
            continue

    title = ("⭐ " + r.get("name", "")) if r.get("fav") else r.get("name", "")

    with st.expander(title):
        edit_key = f"edit_{r['id']}"
        if edit_key not in st.session_state:
            st.session_state[edit_key] = False

        if st.session_state[edit_key]:
            with st.form(f"form_{r['id']}"):
                en = st.text_input("Název", r.get("name", ""))
                et = st.radio("Typ", ["sladké", "slané"], index=0 if r.get("type")=="sladké" else 1)
                ep = st.number_input("Porce", 1, 20, int(r.get("portions", 4)))
                ei = st.text_area("Ingredience", r.get("ingredients", ""))
                es = st.text_area("Postup", r.get("steps", ""))

                if st.form_submit_button("💾 Uložit"):
                    r.update({"name": en, "type": et, "portions": ep, "ingredients": ei, "steps": es})
                    api_update(r["id"], r)
                    st.session_state[edit_key] = False
                    st.rerun()
                    
            if st.button("❌ Zrušit", key=f"cancel_{r['id']}"):
                st.session_state[edit_key] = False
                st.rerun()

        else:
            # PŘEPOČET PORCÍ
            orig_portions = int(r.get("portions", 4))
            if orig_portions < 1: orig_portions = 1
            
            c_port, _ = st.columns([2, 3])
            with c_port:
                target_portions = st.number_input(
                    "👩‍🍳 Pro kolik lidí vaříš?", 
                    min_value=1, max_value=50, 
                    value=orig_portions, 
                    key=f"port_{r['id']}"
                )
            
            # Násobič pro suroviny
            multiplier = target_portions / orig_portions

            st.markdown("**Ingredience:**")
            html = "<div class='ingredients'>"
            for l in convert_text(r.get("ingredients", ""), multiplier).splitlines():
                html += f"<p>• {l}</p>"
            html += "</div><br>"
            st.markdown(html, unsafe_allow_html=True)

            st.markdown("**Postup:**")
            for l in r.get("steps", "").splitlines():
                if l.strip(): st.markdown(l)

            # --- EXPORT / SDÍLENÍ ---
            export_text = f"🍳 {r.get('name', '').upper()}\n"
            export_text += f"🥘 Porce: {target_portions}\n\n"
            export_text += "🛒 Ingredience:\n"
            for l in convert_text(r.get("ingredients", ""), multiplier).splitlines():
                # Očistíme od Markdown hvězdiček, aby to v textu vypadalo čistě
                clean_l = l.replace("**", "")
                export_text += f"• {clean_l}\n"
            export_text += "\n👨‍🍳 Postup:\n"
            for l in r.get("steps", "").splitlines():
                if l.strip(): export_text += f"{l}\n"

            with st.expander("📤 Sdílet / Kopírovat recept"):
                st.info("Kliknutím na ikonu v pravém horním rohu rámečku zkopíruješ text.")
                st.code(export_text, language="markdown")

            st.divider()
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
