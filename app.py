import streamlit as st
import json, os
from datetime import datetime, timedelta

st.set_page_config("Moje recepty", layout="centered")

DATA_FILE="recepty.json"
SYNC_FILE="sync.txt"

# ================= UI STYLE =================
st.markdown("""
<style>
.block-container{padding-top:1rem}
.card{
    background:#ffffff;
    padding:15px;
    border-radius:18px;
    box-shadow:0 3px 12px rgba(0,0,0,0.08);
    margin-bottom:15px;
}
.title{
    font-size:22px;
    font-weight:700;
}
.ing{color:#444;font-size:15px}
.step{color:#222;font-size:15px}
.topbtn button{
    width:100%;
    border-radius:12px;
    height:45px;
    font-size:18px;
}
</style>
""",unsafe_allow_html=True)

# ================= DATA =================
def load():
    if os.path.exists(DATA_FILE):
        return json.load(open(DATA_FILE,"r",encoding="utf8"))
    return []

def save(data):
    json.dump(data,open(DATA_FILE,"w",encoding="utf8"),ensure_ascii=False,indent=2)

if "recipes" not in st.session_state:
    st.session_state.recipes=load()

# ================= GOOGLE SHEET =================
def connect_sheet():
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        creds=Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        return gspread.authorize(creds).open(st.secrets["gsheet_name"]).sheet1
    except:
        return None

def sync():
    sheet=connect_sheet()
    if not sheet:
        st.warning("⚠️ Google Sheet nepřipojen")
        return

    sheet.clear()
    sheet.append_row(["Název","Typ","Ingredience","Postup"])

    for r in st.session_state.recipes:
        sheet.append_row([r["name"],r["type"],r["ingredients"],r["steps"]])

    open(SYNC_FILE,"w").write(datetime.now().isoformat())
    st.success("✔ Synchronizováno")

def autosync():
    if not os.path.exists(SYNC_FILE):
        return
    last=datetime.fromisoformat(open(SYNC_FILE).read())
    if datetime.now()-last>timedelta(days=7):
        sync()

autosync()

# ================= HEADER =================
c1,c2,c3=st.columns([1,1,5])

with c1:
    if st.button("➕",use_container_width=True):
        st.session_state.add=True

with c2:
    if st.button("☁",use_container_width=True):
        sync()

search=c3.text_input("🔎 Hledat recept")

# ================= ADD =================
if st.session_state.get("add"):

    st.markdown("## Nový recept")

    name=st.text_input("Název")
    typ=st.radio("Typ",["sladké","slané"],horizontal=True)
    ing=st.text_area("Ingredience")
    steps=st.text_area("Postup")

    if st.button("Uložit",use_container_width=True):
        st.session_state.recipes.append({
            "name":name,
            "type":typ,
            "ingredients":ing,
            "steps":steps
        })
        save(st.session_state.recipes)
        st.session_state.add=False
        st.rerun()

# ================= FILTER =================
f1,f2=st.columns(2)
sweet=f1.toggle("🍰 sladké",True)
salty=f2.toggle("🥩 slané",True)

# ================= LIST =================
for i,r in enumerate(st.session_state.recipes):

    if search and search.lower() not in r["name"].lower():
        continue
    if r["type"]=="sladké" and not sweet:
        continue
    if r["type"]=="slané" and not salty:
        continue

    st.markdown(f"""
    <div class="card">
        <div class="title">{'🍰' if r["type"]=="sladké" else '🥩'} {r["name"]}</div>
        <div class="ing"><b>Ingredience:</b><br>{r["ingredients"].replace(chr(10),"<br>")}</div>
        <div class="step"><b>Postup:</b><br>{r["steps"].replace(chr(10),"<br>")}</div>
    </div>
    """,unsafe_allow_html=True)

    b1,b2=st.columns(2)

    if b1.button("✏ Upravit",key="e"+str(i),use_container_width=True):
        st.session_state.edit=i
        st.rerun()

    if b2.button("🗑 Smazat",key="d"+str(i),use_container_width=True):
        st.session_state.recipes.pop(i)
        save(st.session_state.recipes)
        st.rerun()

# ================= EDIT =================
if "edit" in st.session_state:

    i=st.session_state.edit
    r=st.session_state.recipes[i]

    st.markdown("## Upravit recept")

    name=st.text_input("Název",r["name"])
    typ=st.radio("Typ",["sladké","slané"],index=0 if r["type"]=="sladké" else 1,horizontal=True)
    ing=st.text_area("Ingredience",r["ingredients"])
    steps=st.text_area("Postup",r["steps"])

    if st.button("Uložit změny",use_container_width=True):
        st.session_state.recipes[i]={
            "name":name,
            "type":typ,
            "ingredients":ing,
            "steps":steps
        }
        save(st.session_state.recipes)
        del st.session_state.edit
        st.rerun()
