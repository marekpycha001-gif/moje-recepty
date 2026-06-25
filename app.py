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
            
    is_vol = False
    unit_matched = ""
    coef = 1

    vol_units = {
        r"^(hrnku|hrnek|hrnky|hrnků|cup)\b": 240, r"^(lžička|lžičky|lžičku|lžiček|čl|č\.l\.)\b": 5,
        r"^(lžíce|lžíci|lžic|pl|p\.l\.|polévková lžíce|polévkové l
