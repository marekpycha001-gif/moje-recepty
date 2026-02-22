import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests, json, os

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳")

SDB_URL="https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE="recipes.json"

# ---------------- SESSION ----------------
defaults={"api":"","recipes":[],"show_new":False,"show_search":False,"show_api":False}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

# ---------------- AI ----------------
def ai_generate(content):
    try:
        genai.configure(api_key=st.session_state.api)

        model_name=None
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                model_name=m.name
                if "flash" in m.name.lower():
                    break

        model=genai.GenerativeModel(model_name)

        prompt="""
Jsi český kuchař.
Vytvoř recept ČESKY.

Formát:
NAZEV:
INGREDIENCE:
POSTUP:
"""
        r=model.generate_content([prompt,content])
        return r.text

    except Exception as e:
        return f"AI chyba: {e}"

# ---------------- STORAGE ----------------
def load_local():
    if os.path.exists(LOCAL_FILE):
        return json.load(open(LOCAL_FILE,encoding="utf8"))
    return []

def save_local(data):
    with open(LOCAL_FILE,"w",encoding="utf8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

def normalize(rec):
    # opraví staré i nové názvy
    if "nazev" not in rec:
        rec["nazev"]=rec.get("title","Bez názvu")
    return rec

def load_db():
    try:
        r=requests.get(SDB_URL,timeout=5)
        if r.status_code==200:
            return [normalize(x) for x in r.json()]
    except:
        pass
    return load_local()

def save_db():
    try:
        requests.delete(SDB_URL+"/all",timeout=5)
        requests.post(SDB_URL,json=st.session_state.recipes,timeout=5)
    except:
        pass
    save_local(st.session_state.recipes)

if not st.session_state.recipes:
    st.session_state.recipes=load_db()

# ---------------- DESIGN ----------------
st.markdown("""
<style>
body,[data-testid="stAppViewContainer"]{
 background:radial-gradient(circle at bottom,#000428,#004e92);
 color:white;
}

.title{
 text-align:center;
 font-size:24px;
 font-weight:bold;
 margin-bottom:10px;
 color:#00ccff;
}

.topbar{
 display:flex;
 justify-content:center;
 gap:6px;
 margin-bottom:10px;
}

.stButton button{
 height:42px;
 width:42px;
 border-radius:10px;
 font-size:20px;
 background:#0099ff;
 color:white;
}

.stExpanderHeader{
 background:#1E3A8A !important;
 color:white !important;
 border-radius:10px;
}

.stExpanderContent{
 background:#cce0ff !important;
 color:black;
 border-radius:10px;
}
</style>
""",unsafe_allow_html=True)

# ---------------- TOP BAR ----------------
c1,c2,c3,c4=st.columns(4)
with c1:
    if st.button("➕"):
        st.session_state.show_new=not st.session_state.show_new
with c2:
    if st.button("🔄"):
        save_db()
with c3:
    if st.button("🔍"):
        st.session_state.show_search=not st.session_state.show_search
with c4:
    if st.button("🔑"):
        st.session_state.show_api=not st.session_state.show_api

st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------------- API ----------------
if st.session_state.show_api:
    st.session_state.api=st.text_input("API klíč",type="password")

# ---------------- SEARCH ----------------
search=""
if st.session_state.show_search:
    search=st.text_input("Hledat")

# ---------------- ADD ----------------
if st.session_state.show_new:

    tab1,tab2,tab3=st.tabs(["Ručně","URL","Obrázek"])

    # ručně
    with tab1:
        with st.form("manual"):
            t=st.text_input("Název")
            txt=st.text_area("Text")
            if st.form_submit_button("Uložit"):
                st.session_state.recipes.insert(0,{
                    "nazev":t or "Bez názvu",
                    "text":txt,
                    "fav":False
                })
                save_db()
                st.rerun()

    # URL
    with tab2:
        url=st.text_input("URL receptu")
        title_web=st.text_input("Název receptu (volitelné)")
        if st.button("Načíst z webu"):
            if url:

                if not url.startswith("http"):
                    url="https://"+url

                try:
                    headers={"User-Agent":"Mozilla/5.0"}
                    page=requests.get(url,headers=headers,timeout=15).text
                    text=ai_generate(page)

                    st.session_state.recipes.insert(0,{
                        "nazev":title_web or "Recept z webu",
                        "text":text,
                        "fav":False
                    })
                    save_db()
                    st.rerun()

                except Exception as e:
                    st.error(f"Načtení selhalo: {e}")

    # obrázek
    with tab3:
        img=st.file_uploader("Nahraj obrázek",type=["png","jpg","jpeg"])
        title_img=st.text_input("Název receptu z obrázku")

        if img and st.button("Načíst z obrázku"):
            text=ai_generate(Image.open(img))

            st.session_state.recipes.insert(0,{
                "nazev":title_img or "Recept z obrázku",
                "text":text,
                "fav":False
            })
            save_db()
            st.rerun()

# ---------------- LIST ----------------
for i,r in enumerate(st.session_state.recipes):

    title=r.get("nazev","Bez názvu")

    if search and search.lower() not in title.lower() and search.lower() not in r.get("text","").lower():
        continue

    with st.expander(("⭐ " if r.get("fav") else "")+title):

        nt=st.text_input("Název",title,key=f"t{i}")
        tx=st.text_area("Text",r.get("text",""),height=200,key=f"x{i}")

        c1,c2,c3=st.columns(3)

        with c1:
            if st.button("💾",key=f"s{i}"):
                r["nazev"]=nt
                r["text"]=tx
                save_db()
                st.rerun()

        with c2:
            if st.button("⭐",key=f"f{i}"):
                r["fav"]=not r.get("fav",False)
                save_db()
                st.rerun()

        with c3:
            if st.button("🗑",key=f"d{i}"):
                st.session_state.recipes.pop(i)
                save_db()
                st.rerun()
