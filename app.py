import streamlit as st
from PIL import Image
import requests, json, os, re

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"

# ---------- SESSION ----------
defaults = {
    "api": "",
    "recipes": [],
    "show_new": False,
    "show_search": False,
    "show_api": False
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- AI ----------
def ai_generate(txt):
    if not st.session_state.api:
        return "⚠️ Zadej API klíč"

    try:
        url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=" + st.session_state.api
        
        payload = {
            "contents": [{
                "parts":[{"text": f"Jsi expert na vaření. Přelož do češtiny a přepracuj recept tak, aby byl originální a zachoval hlavní kroky:\n{txt[:15000]}"}]
            }]
        }

        headers = {"Content-Type": "application/json"}
        r = requests.post(url, headers=headers, json=payload, timeout=60)

        if r.status_code != 200:
            return f"AI chyba HTTP {r.status_code}: {r.text}"

        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"AI chyba: {e}"

# ---------- STORAGE ----------
def load_local():
    if os.path.exists(LOCAL_FILE):
        return json.load(open(LOCAL_FILE, encoding="utf8"))
    return []

def save_local():
    with open(LOCAL_FILE, "w", encoding="utf8") as f:
        json.dump(st.session_state.recipes, f, ensure_ascii=False, indent=2)

def load_db():
    try:
        r = requests.get(SDB_URL, timeout=5)
        if r.status_code == 200:
            return [{
                "id": x.get("id",""),
                "title": x.get("nazev","Bez názvu"),
                "text": x.get("text",""),
                "fav": str(x.get("fav","False")).lower()=="true",
                "img": x.get("img",""),
                "time": x.get("time",""),
                "calories": x.get("calories","")
            } for x in r.json()]
    except:
        pass
    return load_local()

def save_db():
    save_local()
    try:
        data = [{
            "id": r.get("id",""),
            "nazev": r["title"],
            "text": r["text"],
            "fav": "true" if r.get("fav",False) else "false",
            "img": r.get("img",""),
            "time": r.get("time",""),
            "calories": r.get("calories","")
        } for r in st.session_state.recipes]
        requests.post(SDB_URL, json=data, timeout=5)
    except:
        pass

if not st.session_state.recipes:
    st.session_state.recipes = load_db()

# ---------- DESIGN ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');
body,[data-testid="stAppViewContainer"]{background:radial-gradient(circle at bottom,#000428,#004e92); color:white;}
.title{font-family:'Dancing Script',cursive; font-size:22px; text-align:center; color:#00ccff; margin-bottom:10px;}
.stExpanderHeader{background:#1E3A8A !important; color:white !important; border-radius:10px;}
.stExpanderContent{background:#cce0ff !important; color:black !important; border-radius:10px;}
.stTextInput input, textarea{color:black !important;}
</style>
""", unsafe_allow_html=True)

# ---------- TOP BAR ----------
c1,c2,c3,c4 = st.columns(4)
with c1:
    if st.button("➕"): st.session_state.show_new = not st.session_state.show_new
with c2:
    if st.button("🔄"): save_db(); st.success("Uloženo")
with c3:
    if st.button("🔍"): st.session_state.show_search = not st.session_state.show_search
with c4:
    if st.button("🔑"): st.session_state.show_api = not st.session_state.show_api

st.markdown('<div class="title">Márova kuchařka</div>', unsafe_allow_html=True)

# ---------- API ----------
if st.session_state.show_api:
    st.session_state.api = st.text_input("API klíč", type="password")

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search = st.text_input("Hledat")

# ---------- ADD RECIPE ----------
if st.session_state.show_new:
    t1,t2,t3 = st.tabs(["Text","Web","Foto"])

    # TEXT
    with t1:
        with st.form("textform"):
            txt = st.text_area("Text receptu")
            title = st.text_input("Název")
            time = st.text_input("Čas")
            cal = st.text_input("Kalorie")
            if st.form_submit_button("Uložit") and txt:
                st.session_state.recipes.insert(0,{
                    "id":"",
                    "title":title or "Bez názvu",
                    "text":txt,
                    "fav":False,
                    "img":"",
                    "time":time,
                    "calories":cal
                })
                save_db()
                st.success("Uloženo")

    # WEB
    with t2:
        with st.form("webform"):
            url = st.text_input("URL receptu")
            title2 = st.text_input("Název")
            if st.form_submit_button("Načíst z webu") and url:
                try:
                    page = requests.get(url,timeout=10).text
                    paragraphs = re.findall(r'<p.*?>(.*?)</p>', page, flags=re.S)
                    text_content = " ".join([re.sub(r'<.*?>','',p) for p in paragraphs])
                    gen = ai_generate(text_content)
                except:
                    gen = "Nepodařilo se načíst stránku"
                st.session_state.recipes.insert(0,{
                    "id":"",
                    "title":title2 or "Bez názvu",
                    "text":gen,
                    "fav":False,
                    "img":"",
                    "time":"",
                    "calories":""
                })
                save_db()
                st.success("Hotovo")

    # IMAGE
    with t3:
        img = st.file_uploader("Foto receptu", type=["jpg","png"])
        title3 = st.text_input("Název")
        if img and st.button("Vytáhnout text"):
            try:
                import pytesseract
                text = pytesseract.image_to_string(Image.open(img), lang="ces")
                gen = ai_generate(text)
            except:
                gen = "Nepodařilo se přečíst obrázek"
            st.session_state.recipes.insert(0,{
                "id":"",
                "title":title3 or "Bez názvu",
                "text":gen,
                "fav":False,
                "img":"",
                "time":"",
                "calories":""
            })
            save_db()
            st.success("Hotovo")

# ---------- DISPLAY ----------
for i,r in enumerate(st.session_state.recipes):
    title = r.get("title","Bez názvu")
    text = r.get("text","")
    if search and search.lower() not in (title+" "+text).lower():
        continue

    with st.expander(("⭐ " if r.get("fav") else "") + title):
        nt = st.text_input("Název", title, key=f"t{i}")
        tx = st.text_area("Text", text, height=250, key=f"x{i}")

        c1,c2,c3 = st.columns(3)

        with c1:
            if st.button("💾", key=f"s{i}"):
                st.session_state.recipes[i]["title"]=nt
                st.session_state.recipes[i]["text"]=tx
                save_db()
                st.success("Uloženo")

        with c2:
            if st.button("⭐", key=f"f{i}"):
                st.session_state.recipes[i]["fav"]=not r.get("fav",False)
                save_db()
                st.experimental_rerun()

        with c3:
            if st.button("🗑", key=f"d{i}"):
                st.session_state.recipes.pop(i)
                save_db()
                st.experimental_rerun()
