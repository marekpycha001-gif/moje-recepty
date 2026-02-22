import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests, json, os

# Pokus importovat BeautifulSoup
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# Pokus importovat pytesseract
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"

# ---------- SESSION ----------
defaults = {"api": "", "recipes": [], "show_new": False, "show_search": False, "show_api": False}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

# ---------- AI ----------
def ai_generate(txt):
    """
    Generuje text pomocí Google Generative AI.
    - Dynamicky vybírá dostupný model pro generate_content
    - Překládá do češtiny a lehce upravuje recept
    """
    if not st.session_state.api:
        return "⚠️ Zadej API klíč"
    
    genai.configure(api_key=st.session_state.api)
    
    try:
        # Načti seznam dostupných modelů
        models = genai.list_models()
        
        # Hledáme model, který podporuje generate_content
        available_models = [
            m["name"] for m in models 
            if "generateContent" in m.get("supported_methods", [])
        ]
        
        if not available_models:
            return "⚠️ Žádný dostupný model nepodporuje generate_content"
        
        # Použij první dostupný model
        model_name = available_models[0]
        model = genai.GenerativeModel(model_name)
        
        # Prompt pro AI: recept do češtiny, lehce upravený
        prompt = f"Jsi expert na vaření. Přelož vše do češtiny a uprav recept tak, aby byl originální a zachoval hlavní kroky. {txt}"
        
        return model.generate_content([prompt]).text
    
    except Exception as e:
        return f"AI chyba: {e}"

# ---------- STORAGE ----------
def load_local():
    if os.path.exists(LOCAL_FILE):
        return json.load(open(LOCAL_FILE, encoding="utf8"))
    return []

def save_local():
    with open(LOCAL_FILE,"w",encoding="utf8") as f:
        json.dump(st.session_state.recipes,f,ensure_ascii=False,indent=2)

def load_db():
    recipes=[]
    try:
        r=requests.get(SDB_URL,timeout=3)
        if r.status_code==200:
            for x in r.json():
                recipes.append({
                    "id": x.get("id",""),
                    "title": x.get("nazev","Bez názvu"),
                    "text": x.get("text",""),
                    "fav": str(x.get("fav","False")).lower()=="true",
                    "img": x.get("img",""),
                    "time": x.get("time",""),
                    "calories": x.get("calories","")
                })
    except:
        pass
    if not recipes:
        recipes=load_local()
    return recipes

def save_db():
    save_local()
    try:
        data_to_send = [{
            "id": r.get("id",""),
            "nazev": r["title"],
            "text": r["text"],
            "fav": "true" if r.get("fav", False) else "false",
            "img": r.get("img",""),
            "time": r.get("time",""),
            "calories": r.get("calories","")
        } for r in st.session_state.recipes]
        requests.post(SDB_URL,json=data_to_send,timeout=3)
    except:
        pass

if not st.session_state.recipes:
    st.session_state.recipes=load_db()

# ---------- DESIGN ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');
body,[data-testid="stAppViewContainer"]{background:radial-gradient(circle at bottom,#000428,#004e92); color:white;}
.title{font-family:'Dancing Script',cursive; font-size:20px; text-align:center; color:#00ccff; margin-bottom:10px;}
.stExpanderHeader{background:#1E3A8A !important; color:white !important; border-radius:10px;}
.stExpanderContent{background:#cce0ff !important; color:black !important; border-radius:10px;}
.stTextInput>div>div>input, .stNumberInput>div>div>input, textarea{color:black;}
</style>
""",unsafe_allow_html=True)

# ---------- TOP BAR ----------
col1,col2,col3,col4 = st.columns(4)
with col1:
    if st.button("➕"): st.session_state.show_new = not st.session_state.show_new
with col2:
    if st.button("🔄"): save_db(); st.success("Uloženo!")
with col3:
    if st.button("🔍"): st.session_state.show_search = not st.session_state.show_search
with col4:
    if st.button("🔑"): st.session_state.show_api = not st.session_state.show_api

st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- API ----------
if st.session_state.show_api:
    st.session_state.api = st.text_input("API klíč (jednou na spuštění)", type="password")

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search=st.text_input("Hledat recept podle názvu/ingrediencí")

# ---------- NEW RECIPE ----------
if st.session_state.show_new:
    t1,t2,t3=st.tabs(["Text","Web","Foto"])
    
    with t1:
        with st.form("form_text"):
            txt=st.text_area("Text receptu")
            title=st.text_input("Název receptu")
            time=st.text_input("Doba přípravy (min)")
            cal=st.text_input("Kalorie")
            if st.form_submit_button("Uložit text"):
                if txt:
                    st.session_state.recipes.insert(0,{"id":"","title":title or "Bez názvu","text":txt,"fav":False,"img":"","time":time,"calories":cal})
                    save_db(); st.success("Recept uložen!")
                    
    with t2:
        with st.form("form_web"):
            url=st.text_input("URL receptu")
            title2=st.text_input("Název receptu")
            if st.form_submit_button("Vygenerovat z webu"):
                if url:
                    if BS4_AVAILABLE:
                        try:
                            page=requests.get(url,timeout=5).text
                            soup=BeautifulSoup(page,"html.parser")
                            text_content=" ".join([p.get_text() for p in soup.find_all("p")])
                            gen_txt=ai_generate(text_content)
                        except:
                            gen_txt="Nepodařilo se načíst stránku"
                    else:
                        gen_txt=st.text_area("Zadej text receptu ručně (BeautifulSoup není nainstalován)")
                    st.session_state.recipes.insert(0,{"id":"","title":title2 or "Bez názvu","text":gen_txt,"fav":False,"img":"","time":"","calories":""})
                    save_db(); st.success("Recept vygenerován!")
                    
    with t3:
        img=st.file_uploader("Foto", type=["jpg","png"])
        title3=st.text_input("Název receptu (foto)")
        if img:
            if OCR_AVAILABLE:
                if st.button("Vygenerovat z obrázku"):
                    try:
                        img_txt=pytesseract.image_to_string(Image.open(img),lang="ces")
                        gen_txt=ai_generate(img_txt)
                        st.session_state.recipes.insert(0,{"id":"","title":title3 or "Bez názvu","text":gen_txt,"fav":False,"img":"","time":"","calories":""})
                        save_db(); st.success("Recept z obrázku vygenerován!")
                    except Exception as e:
                        st.warning(f"Chyba: {e}")
            else:
                st.text("OCR není dostupné. Zadej text ručně.")

# ---------- DISPLAY RECIPES ----------
for i,r in enumerate(st.session_state.recipes):
    title=r.get("title","Bez názvu")
    text=r.get("text","")
    fulltext=(title+" "+text).lower()
    if search and search.lower() not in fulltext: continue
    with st.expander("⭐ "+title if r.get("fav",False) else title):
        nt=st.text_input("Název", title,key=f"t{i}")
        tx=st.text_area("Text", text,key=f"x{i}",height=250)
        t_col,c_col,d_col,fav_col=st.columns([1,1,1,1])
        with t_col:
            if st.button("💾", key=f"s{i}"):
                st.session_state.recipes[i]["title"]=nt
                st.session_state.recipes[i]["text"]=tx
                save_db(); st.success("Uloženo!")
        with fav_col:
            if st.button("⭐", key=f"f{i}"):
                st.session_state.recipes[i]["fav"]=not r.get("fav",False)
                save_db()
        with d_col:
            if st.button("🗑", key=f"d{i}"):
                st.session_state.recipes=[rec for idx,rec in enumerate(st.session_state.recipes) if idx!=i]
                save_db(); st.experimental_rerun()
