import streamlit as st
import json, os, re, time, random, string
import requests
from fractions import Fraction
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from bs4 import BeautifulSoup
from PIL import Image

# Načtení vlastní ikony
try:
    ikona_aplikace = Image.open("ikona.png")
    st.set_page_config(page_title="Márova kuchařka", page_icon=ikona_aplikace, layout="centered")
except:
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
    
    expected_headers = ["id", "name", "type", "portions", "ingredients", "steps", "fav", "calories", "protein", "carbs", "fat"]
    
    current_headers = sheet.row_values(1)
    if not current_headers:
        sheet.append_row(expected_headers)
    elif len(current_headers) < len(expected_headers):
        try:
            sheet.update("A1:K1", [expected_headers])
        except Exception as e:
            sheet.update(range_name="A1:K1", values=[expected_headers])
        
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
            x["calories"] = int(x.get("calories", 0) or 0)
            x["protein"] = int(x.get("protein", 0) or 0)
            x["carbs"] = int(x.get("carbs", 0) or 0)
            x["fat"] = int(x.get("fat", 0) or 0)
        return records
    except Exception as e:
        st.error(f"Chyba při stahování dat: {e}")
        return []

def api_add(recipe):
    try:
        row = [
            recipe.get("id", ""), recipe.get("name", ""), recipe.get("type", ""),
            recipe.get("portions", ""), recipe.get("ingredients", ""), recipe.get("steps", ""),
            str(recipe.get("fav", False)), recipe.get("calories", 0),
            recipe.get("protein", 0), recipe.get("carbs", 0), recipe.get("fat", 0)
        ]
        sheet.append_row(row)
    except Exception as e: 
        st.error(f"Chyba při ukládání: {e}")

def api_update(recipe_id, updated_data):
    try:
        cell = sheet.find(recipe_id, in_column=1)
        if cell:
            row_idx = cell.row
            row_data = [
                updated_data.get("id", recipe_id), updated_data.get("name", ""),
                updated_data.get("type", ""), updated_data.get("portions", ""),
                updated_data.get("ingredients", ""), updated_data.get("steps", ""),
                str(updated_data.get("fav", False)), updated_data.get("calories", 0),
                updated_data.get("protein", 0), updated_data.get("carbs", 0), updated_data.get("fat", 0)
            ]
            try: sheet.update(f"A{row_idx}:K{row_idx}", [row_data])
            except: sheet.update(range_name=f"A{row_idx}:K{row_idx}", values=[row_data])
    except Exception as e:
        st.error(f"Chyba při úpravě receptu: {e}")

def api_delete(recipe_id):
    try:
        cell = sheet.find(recipe_id, in_column=1)
        if cell: sheet.delete_rows(cell.row)
    except Exception as e:
        st.error(f"Chyba při mazání receptu: {e}")

# ---------- POMOCNÁ FUNKCE PRO DOPLNĚNÍ MAKER ----------
def get_macros_only(ingredients, portions, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""Odhadni nutriční hodnoty na 1 porci. Recept je celkem pro {portions} porcí.
        Vrať POUZE validní JSON formát (klíče anglicky, hodnoty celá čísla):
        {{"calories": 0, "protein": 0, "carbs": 0, "fat": 0}}
        Ingredience:
        {ingredients}"""
        res = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        text = res.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        st.error(f"Nepodařilo se spočítat makra: {e}")
        return None

# ---------- INITIALIZATION ----------
if "recipes" not in st.session_state: st.session_state.recipes = load_db()
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
    font-size: 28px; text-align: center; color: #00ccff; margin-bottom: 20px; font-weight: 700;
}
.topbar { display: flex; justify-content: flex-start; gap: 10px; margin-bottom: 15px; }
button { border-radius: 10px !important; transition: .15s; }
button:hover {transform: scale(1.05)}
.ingredients p { margin: 0; line-height: 1.2; font-size: 15px; }
.macros {
    background: rgba(0, 204, 255, 0.1); padding: 10px; border-radius: 8px;
    margin-bottom: 15px; font-size: 14px; border: 1px solid rgba(0, 204, 255, 0.3);
}
.calc-btn { margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# ---------- TOP UI ----------
st.markdown('<div class="topbar">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns([1, 1, 1, 3])
with c1:
    if st.button("➕ Nový"): st.session_state.show_new = not st.session_state.show_new
with c2:
    if st.button("🔍 Hledat"): st.session_state.show_search = not st.session_state.show_search
with c3:
    if st.button("🔄 Obnovit"): 
        st.session_state.recipes = load_db()
        st.rerun()
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
def parse_qty(q):
    try: return float(sum(Fraction(x) for x in q.replace(",",".").split()))
    except Exception:
        try: return float(q)
        except Exception: return None

def convert_line(line, multiplier=1.0):
    line = line.strip()
    m = re.match(r"^([\d\/\.,\s]+)\s*(.*)", line)
    if not m: return line
    qty_str, rest = m.groups()
    val = parse_qty(qty_str)
    if val is None: return line
    val = val * multiplier
    def fmt(v): return int(v) if v == int(v) else round(v, 1)

    rest_lower = rest.lower()
    ignore_patterns = ["ks", "kus", "kusů", "kusy", "vejce", "špetka", "špetku", "špetky", "trochu", "balení", "bal", "plechovka", "plechovky"]
    for ig in ignore_patterns:
        if rest_lower.startswith(ig): return f"{fmt(val)} {ig} {rest[len(ig):].strip()}"
            
    coef = 1; is_vol = False; unit_matched = ""
    vol_units = {
        r"^(hrnku|hrnek|hrnky|hrnků|cup)\b": 240, r"^(lžička|lžičky|lžičku|lžiček|čl|č\.l\.)\b": 5,
        r"^(lžíce|lžíci|lžic|pl|p\.l\.|polévková lžíce|polévkové lžíce)\b": 15,
        r"^(kg|kilo|kila|kilogram|kilogramů)\b": 1000, r"^(l|litr|litru|litrů|litry)\b": 1000,
        r"^(dkg|deka)\b": 10, r"^(g|gram|gramů|gramy|ml|mililitr|mililitrů)\b": 1
    }
    
    for pat, mult in vol_units.items():
        match = re.search(pat, rest_lower)
        if match:
            unit_matched = match.group(0); coef = mult
            if mult in [5, 15, 240]: is_vol = True
            break
            
    if not unit_matched: return f"{fmt(val)} {rest}"
    name = rest[len(unit_matched):].strip()
    name_lower = name.lower()
    
    if coef == 1 and not is_vol: return f"{fmt(val)} {unit_matched} {name}"
        
    dens = 1.0
    if is_vol:
        if "mouk" in name_lower: dens = 0.55
        elif "cukr" in name_lower: dens = 0.85
        elif "olej" in name_lower: dens = 0.92
        elif "másl" in name_lower or "masl" in name_lower: dens = 0.95
        elif "med" in name_lower: dens = 1.42
        elif "kakao" in name_lower or "kakaa" in name_lower: dens = 0.4
        elif "mlék" in name_lower or "mlek" in name_lower: dens = 1.03
        elif "vloč" in name_lower: dens = 0.4
        elif "rýž" in name_lower or "ryz" in name_lower: dens = 0.85

    final_val = val * coef * dens
    out_unit = "ml" if any(x in name_lower for x in ["vod", "mlék", "mlek", "olej", "smetan", "rum", "vín", "šťáv"]) else "g"

    return f"{fmt(final_val)} {out_unit} {name} (původně: {line})"

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
    
    system_prompt = """Jsi expert na extrakci receptů a výživu. Z textu/obrázku vytáhni recept.
    Vrať POUZE validní JSON formát s klíči: "name", "type" ("slané"/"sladké"), "portions" (výchozí 4),
    "ingredients" (text, řádky), "steps" (text, řádky), "calories" (celé číslo na 1 porci),
    "protein" (celé číslo, 1 porce), "carbs" (celé číslo, 1 porce), "fat" (celé číslo, 1 porce)."""

    def process_ai_response(response_text):
        try:
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            if isinstance(data, list):
                if len(data) > 0: data = data[0]
                else: return None
            return data
        except Exception as e:
            st.error(f"Nepodařilo se zpracovat odpověď od AI: {e}")
            return None

    tab1, tab2, tab3 = st.tabs(["✍️ Ručně", "🔗 Z odkazu", "📸 Z fotky"])

    with tab1:
        with st.form("new_recipe_form_manual", clear_on_submit=True):
            n = st.text_input("Název")
            typ = st.radio("Typ", ["slané", "sladké"], horizontal=True)
            por = st.number_input("Porce", 1, 20, 4)
            st.markdown("**Nutriční hodnoty na 1 porci:**")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            cal_in = m_col1.number_input("Kcal", 0, 5000, 0)
            pro_in = m_col2.number_input("Bílkoviny", 0, 500, 0)
            car_in = m_col3.number_input("Sacharidy", 0, 500, 0)
            fat_in = m_col4.number_input("Tuky", 0, 500, 0)
            ing = st.text_area("Ingredience (co řádek, to položka)")
            steps = st.text_area("Postup")
            
            if st.form_submit_button("✅ Uložit recept"):
                new_r = {
                    "id": new_id(), "name": n or "Bez názvu", "type": typ,
                    "portions": por, "ingredients": ing, "steps": steps, "fav": False,
                    "calories": cal_in, "protein": pro_in, "carbs": car_in, "fat": fat_in
                }
                st.session_state.recipes.insert(0, new_r)
                api_add(new_r)
                st.session_state.show_new = False
                st.rerun()

    with tab2:
        if not ai_ready: st.warning("Nastav 'gemini_api_key' v Secrets.")
        else:
            url_input = st.text_input("Vlož URL adresu receptu:")
            if st.button("🪄 Vytěžit recept z webu"):
                if url_input:
                    with st.spinner("Pracuji na tom (počítám i kalorie)..."):
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
                        except Exception as e: st.error(f"Chyba při stahování: {e}")

    with tab3:
        if not ai_ready: st.warning("Nastav 'gemini_api_key' v Secrets.")
        else:
            uploaded_file = st.file_uploader("Nahrát obrázek", type=["png", "jpg", "jpeg", "webp"])
            if uploaded_file and st.button("🪄 Přečíst z obrázku"):
                with st.spinner("AI studuje obrázek a odhaduje makra..."):
                    try:
                        img = Image.open(uploaded_file)
                        img.thumbnail((1500, 1500)) 
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
                    except Exception as e: st.error(f"Chyba při čtení obrázku: {e}")

# ---------- SORT ----------
recipes_sorted = sorted(st.session_state.recipes, key=lambda x: (not x.get("fav", False), x.get("name", "")))

# ---------- DISPLAY ----------
for r in recipes_sorted:
    text = (r.get("name","") + r.get("ingredients","") + r.get("type","")).lower()
    if search and search not in text: continue
    if filter_type != "Vše":
        if r.get("type", "").lower() != filter_type.lower(): continue

    title = ("⭐ " + r.get("name", "")) if r.get("fav") else r.get("name", "")

    with st.expander(title):
        edit_key = f"edit_{r['id']}"
        if edit_key not in st.session_state: st.session_state[edit_key] = False

        if st.session_state[edit_key]:
            
            # --- TLAČÍTKO PRO DOPOČÍTÁNÍ MAKER PŘES AI ---
            if "gemini_api_key" in st.secrets:
                if st.button("🪄 Spočítat makra pomocí AI", key=f"ai_mac_{r['id']}"):
                    with st.spinner("AI studuje ingredience..."):
                        macs = get_macros_only(r.get("ingredients", ""), r.get("portions", 4), st.secrets["gemini_api_key"])
                        if macs:
                            st.session_state[f"cal_{r['id']}"] = macs.get("calories", 0)
                            st.session_state[f"pro_{r['id']}"] = macs.get("protein", 0)
                            st.session_state[f"car_{r['id']}"] = macs.get("carbs", 0)
                            st.session_state[f"fat_{r['id']}"] = macs.get("fat", 0)
                            st.rerun()

            with st.form(f"form_{r['id']}"):
                en = st.text_input("Název", r.get("name", ""))
                et = st.radio("Typ", ["sladké", "slané"], index=0 if r.get("type")=="sladké" else 1)
                ep = st.number_input("Porce", 1, 20, int(r.get("portions", 4)))
                
                st.markdown("**Nutriční hodnoty (na 1 porci):**")
                
                # Zjištění, zda už máme spočítáno z AI nebo bereme stará data z databáze
                def_cal = st.session_state.get(f"cal_{r['id']}", int(r.get("calories", 0)))
                def_pro = st.session_state.get(f"pro_{r['id']}", int(r.get("protein", 0)))
                def_car = st.session_state.get(f"car_{r['id']}", int(r.get("carbs", 0)))
                def_fat = st.session_state.get(f"fat_{r['id']}", int(r.get("fat", 0)))

                ec1, ec2, ec3, ec4 = st.columns(4)
                ecal = ec1.number_input("Kcal", 0, 5000, def_cal)
                epro = ec2.number_input("Bílkoviny", 0, 500, def_pro)
                ecar = ec3.number_input("Sacharidy", 0, 500, def_car)
                efat = ec4.number_input("Tuky", 0, 500, def_fat)
                
                ei = st.text_area("Ingredience", r.get("ingredients", ""))
                es = st.text_area("Postup", r.get("steps", ""))

                if st.form_submit_button("💾 Uložit"):
                    r.update({"name": en, "type": et, "portions": ep, "ingredients": ei, "steps": es,
                              "calories": ecal, "protein": epro, "carbs": ecar, "fat": efat})
                    api_update(r["id"], r)
                    st.session_state[edit_key] = False
                    st.rerun()
                    
            if st.button("❌ Zrušit", key=f"cancel_{r['id']}"):
                st.session_state[edit_key] = False
                st.rerun()

        else:
            orig_portions = int(r.get("portions", 4))
            if orig_portions < 1: orig_portions = 1
            
            kcal = int(r.get("calories", 0))
            pro = int(r.get("protein", 0))
            car = int(r.get("carbs", 0))
            fat = int(r.get("fat", 0))
            
            if kcal > 0 or pro > 0 or car > 0 or fat > 0:
                st.markdown(f"<div class='macros'><b>📊 Hodnoty na 1 porci:</b> 🔥 {kcal} kcal | 🥩 Bílkoviny: {pro} g | 🍞 Sacharidy: {car} g | 🧈 Tuky: {fat} g</div>", unsafe_allow_html=True)

            c_port, _ = st.columns([2, 3])
            with c_port:
                target_portions = st.number_input("👩‍🍳 Pro kolik lidí vaříš?", min_value=1, max_value=50, value=orig_portions, key=f"port_{r['id']}")
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

            export_text = f"🍳 {r.get('name', '').upper()}\n"
            if kcal > 0: export_text += f"📊 1 porce: {kcal} kcal | {pro}g B | {car}g S | {fat}g T\n"
            export_text += f"🥘 Porce: {target_portions}\n\n🛒 Ingredience:\n"
            for l in convert_text(r.get("ingredients", ""), multiplier).splitlines():
                export_text += f"• {l}\n"
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
