import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, timedelta

# ======================
# KONFIG
# ======================
DATA_FILE = "recepty.json"
SYNC_FILE = "last_sync.txt"

st.set_page_config(page_title="Moje recepty", layout="centered")

# ======================
# GOOGLE SHEETS NASTAVENÍ
# ======================
def connect_gsheet():
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        sheet = client.open(st.secrets["gsheet_name"]).sheet1
        return sheet
    except:
        return None


# ======================
# ULOŽENÍ / NAČTENÍ
# ======================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ======================
# SYNCHRONIZACE
# ======================
def sync_to_gsheet(data):
    sheet = connect_gsheet()
    if sheet is None:
        st.warning("⚠️ Nepodařilo se připojit k Google Sheet.")
        return

    sheet.clear()
    sheet.append_row(["Název","Typ","Ingredience","Postup"])

    for r in data:
        sheet.append_row([
            r["name"],
            r["type"],
            r["ingredients"],
            r["steps"]
        ])

    with open(SYNC_FILE,"w") as f:
        f.write(datetime.now().isoformat())

    st.success("✔ Synchronizováno s Google Sheet")


def auto_sync(data):
    if not os.path.exists(SYNC_FILE):
        return sync_to_gsheet(data)

    last = datetime.fromisoformat(open(SYNC_FILE).read())
    if datetime.now() - last > timedelta(days=7):
        sync_to_gsheet(data)


# ======================
# PŘEVODY JEDNOTEK
# ======================
densities = {
    "olej":0.92,
    "mléko":1.03,
    "voda":1.0
}

spoon_weights = {
    "cukr":12,
    "mouka":10,
    "olej":13,
    "med":21
}

def convert_units(text):
    words = text.lower().split()
    out = []

    for i,w in enumerate(words):
        if w == "ml" and i>0:
            try:
                val=float(words[i-1])
                for k,d in densities.items():
                    if k in text:
                        out.append(f"{val*d:.1f} g")
                        break
            except: pass

        if w.startswith("lžíce"):
            for k,v in spoon_weights.items():
                if k in text:
                    out.append(f"{v} g {k}")

    if out:
        return text + "\n\n➡ Přepočet:\n" + "\n".join(out)
    return text


# ======================
# DATA
# ======================
if "recipes" not in st.session_state:
    st.session_state.recipes = load_data()

auto_sync(st.session_state.recipes)


# ======================
# HEADER
# ======================
c1,c2,c3 = st.columns([1,1,6])

with c1:
    if st.button("➕"):
        st.session_state.add=True

with c2:
    if st.button("🔄"):
        sync_to_gsheet(st.session_state.recipes)

search = c3.text_input("🔍 Hledat recept")


# ======================
# PŘIDÁNÍ RECEPTU
# ======================
if st.session_state.get("add"):

    st.subheader("Nový recept")

    name = st.text_input("Název")
    typ = st.radio("Typ",["sladké","slané"])
    ing = st.text_area("Ingredience")
    steps = st.text_area("Postup")

    if st.button("Uložit"):
        st.session_state.recipes.append({
            "name":name,
            "type":typ,
            "ingredients":convert_units(ing),
            "steps":steps
        })
        save_data(st.session_state.recipes)
        st.session_state.add=False
        st.rerun()


# ======================
# FILTRY
# ======================
f1,f2 = st.columns(2)
show_sweet = f1.toggle("🍰 sladké",True)
show_salty = f2.toggle("🥩 slané",True)


# ======================
# VÝPIS
# ======================
for i,r in enumerate(st.session_state.recipes):

    if search and search.lower() not in r["name"].lower():
        continue

    if r["type"]=="sladké" and not show_sweet:
        continue
    if r["type"]=="slané" and not show_salty:
        continue

    with st.expander(("🍰 " if r["type"]=="sladké" else "🥩 ") + r["name"]):

        st.markdown("**Ingredience**")
        st.write(r["ingredients"])

        st.markdown("**Postup**")
        st.write(r["steps"])

        c1,c2 = st.columns(2)

        if c1.button("✏️ Upravit",key=f"edit{i}"):
            st.session_state.edit=i
            st.rerun()

        if c2.button("🗑 Smazat",key=f"del{i}"):
            st.session_state.recipes.pop(i)
            save_data(st.session_state.recipes)
            st.rerun()


# ======================
# EDITACE
# ======================
if "edit" in st.session_state:
    i = st.session_state.edit
    r = st.session_state.recipes[i]

    st.subheader("Upravit recept")

    name = st.text_input("Název",r["name"])
    typ = st.radio("Typ",["sladké","slané"],index=0 if r["type"]=="sladké" else 1)
    ing = st.text_area("Ingredience",r["ingredients"])
    steps = st.text_area("Postup",r["steps"])

    if st.button("Uložit změny"):
        st.session_state.recipes[i]={
            "name":name,
            "type":typ,
            "ingredients":convert_units(ing),
            "steps":steps
        }
        save_data(st.session_state.recipes)
        del st.session_state.edit
        st.rerun()
