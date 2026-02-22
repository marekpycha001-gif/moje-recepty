import streamlit as st
import json, os, re, requests

st.set_page_config(page_title="Márova kuchařka PRO", page_icon="🍳", layout="centered")

FILE="recipes.json"

# ---------- SESSION ----------
defaults={
    "recipes":[],
    "show_add":False,
    "show_search":False,
    "api":"",
    "filter":"all"
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

# ---------- LOAD / SAVE ----------
def load():
    if os.path.exists(FILE):
        data=json.load(open(FILE,encoding="utf8"))
        # oprava starých receptů bez typu
        for r in data:
            if "type" not in r:
                r["type"]="slané"
        return data
    return []

def save():
    with open(FILE,"w",encoding="utf8") as f:
        json.dump(st.session_state.recipes,f,ensure_ascii=False,indent=2)

if not st.session_state.recipes:
    st.session_state.recipes=load()

# ---------- CONVERTER ----------
density={
    "olej":0.92,
    "mléko":1.03,
    "voda":1,
    "cukr":0.85,
    "mouka":0.53,
    "med":1.42,
    "máslo":0.96
}

units={
    "ml":1,
    "l":1000,
    "lžíce":15,
    "lžička":5,
    "cup":240,
    "hrnek":240
}

def convert_line(line):
    text=line.lower()
    m=re.search(r"(\d+\.?\d*)\s*(ml|l|lžíce|lžička|cup|hrnek)",text)
    if not m:
        return line

    val=float(m.group(1))
    unit=m.group(2)
    ml=val*units.get(unit,1)

    for name,d in density.items():
        if name in text:
            g=round(ml*d)
            return f"{line} → {g} g"

    return f"{line} → {round(ml)} g (odhad)"

# ---------- AI optional ----------
def ai_convert(text):
    if not st.session_state.api:
        return None
    try:
        url="https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key="+st.session_state.api
        payload={"contents":[{"parts":[{"text":f"Převeď ingredience do gramů a přelož do češtiny:\n{text}"}]}]}
        r=requests.post(url,json=payload,timeout=30)
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return None

# ---------- STYLE ----------
st.markdown("""
<style>
body,[data-testid="stAppViewContainer"]{
background:linear-gradient(180deg,#000428,#004e92);
color:white}
.title{
font-size:26px;
text-align:center;
color:#00ccff;
margin-bottom:12px}
.stExpanderHeader{
background:#1E3A8A!important;
color:white!important;
border-radius:12px}
.stExpanderContent{
background:#e6f0ff!important;
color:black!important;
border-radius:12px}
button{
border-radius:12px!important}
</style>
""",unsafe_allow_html=True)

# ---------- TOP BAR ----------
c1,c2,c3=st.columns(3)

with c1:
    if st.button("➕ Přidat"):
        st.session_state.show_add=not st.session_state.show_add

with c2:
    if st.button("🔑 AI"):
        st.session_state.api=st.text_input("API klíč",type="password")

with c3:
    if st.button("🔍 Hledat"):
        st.session_state.show_search=not st.session_state.show_search

st.markdown('<div class="title">Márova kuchařka PRO</div>',unsafe_allow_html=True)

# ---------- FILTER ----------
f1,f2,f3=st.columns(3)

with f1:
    if st.button("🍰 Sladké",use_container_width=True):
        st.session_state.filter="sladké"

with f2:
    if st.button("🥩 Slané",use_container_width=True):
        st.session_state.filter="slané"

with f3:
    if st.button("📖 Vše",use_container_width=True):
        st.session_state.filter="all"

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search=st.text_input("Vyhledat recept")

# ---------- ADD ----------
if st.session_state.show_add:
    with st.form("add"):
        name=st.text_input("Název receptu")
        ing=st.text_area("Ingredience (řádek = položka)")
        steps=st.text_area("Postup")
        typ=st.selectbox("Kategorie",["sladké","slané"])

        if st.form_submit_button("Uložit recept"):
            st.session_state.recipes.insert(0,{
                "name":name or "Bez názvu",
                "ing":ing,
                "steps":steps,
                "type":typ
            })
            save()
            st.success("Recept uložen")

# ---------- DISPLAY ----------
for i,r in enumerate(st.session_state.recipes):

    typ=r.get("type","slané")
    name=r.get("name","Bez názvu")
    ing=r.get("ing","")
    steps=r.get("steps","")

    if st.session_state.filter!="all" and typ!=st.session_state.filter:
        continue

    if search and search.lower() not in (name+ing+steps).lower():
        continue

    icon="🍰" if typ=="sladké" else "🥩"

    with st.expander(f"{icon} {name}"):

        n=st.text_input("Název",name,key=f"n{i}")
        ing2=st.text_area("Ingredience",ing,key=f"i{i}")
        steps2=st.text_area("Postup",steps,key=f"s{i}")

        if st.button("⚖ Převést jednotky",key=f"c{i}"):
            lines=[convert_line(x) for x in ing2.splitlines()]
            ai=ai_convert(ing2)
            st.text_area("Výsledek",ai if ai else "\n".join(lines))

        b1,b2=st.columns(2)

        with b1:
            if st.button("💾 Uložit",key=f"save{i}"):
                st.session_state.recipes[i]["name"]=n
                st.session_state.recipes[i]["ing"]=ing2
                st.session_state.recipes[i]["steps"]=steps2
                save()
                st.success("Uloženo")

        with b2:
            if st.button("🗑 Smazat",key=f"del{i}"):
                st.session_state.recipes.pop(i)
                save()
                st.experimental_rerun()
