import streamlit as st
import requests
import re

st.set_page_config(page_title="Recepty", layout="centered")

API_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"

# ---------- STYLY ----------
st.markdown("""
<style>
.block-container {padding-top:1.5rem;padding-bottom:4rem;}
textarea,input{font-size:16px !important;}
.ing{line-height:1.15em;margin:0;padding:0;}
button[kind="secondary"]{border-radius:12px;}
</style>
""", unsafe_allow_html=True)

# ---------- PŘEVODY ----------
densities = {
    "olej":0.92,
    "mléko":1.03,
    "voda":1.0,
    "med":1.42
}

spoon = {
    "lž":15,
    "lžíce":15,
    "lžič":5,
    "lžička":5,
    "hrnek":240,
    "hrnky":240
}

def normalize(txt):
    return txt.lower().strip()

def detect_density(name):
    name = normalize(name)
    for k,v in densities.items():
        if k in name:
            return v
    return 1.0

def convert_line(line):
    if "|c" in line:
        return line.replace("|c","")

    l=line.lower().strip()

    m = re.match(r"([\d\.,]+)\s*(ml|l|g|kg)\s+(.*)", l)
    if m:
        val=float(m.group(1).replace(",",".")) 
        unit=m.group(2)
        name=m.group(3)

        if unit=="kg": val*=1000
        if unit=="l": val*=1000

        if unit in ["ml","l"]:
            val*=detect_density(name)

        grams=round(val)
        return f"{grams} g {name}|c"

    m = re.match(r"([\d\.,]+)\s*(lž|lžíce|lžič|lžička|hrnek|hrnky)\s+(.*)", l)
    if m:
        val=float(m.group(1).replace(",",".")) 
        unit=m.group(2)
        name=m.group(3)

        ml = val*spoon[unit]
        grams = round(ml*detect_density(name))
        return f"{grams} g {name}|c"

    return line

def convert_block(text):
    lines=text.splitlines()
    return "\n".join(convert_line(x) for x in lines if x.strip())

# ---------- API ----------
def load_recipes():
    try:
        r=requests.get(API_URL).json()
        return r
    except:
        return []

def save_recipe(data):
    requests.post(API_URL,json=data)

def update_recipe(name,data):
    requests.patch(f"{API_URL}/name/{name}",json=data)

def delete_recipe(name):
    requests.delete(f"{API_URL}/name/{name}")

recipes = load_recipes()

# ---------- NOVÝ ----------
if "show_new" not in st.session_state:
    st.session_state.show_new=False

col1,col2=st.columns([1,8])
if col1.button("➕"):
    st.session_state.show_new=not st.session_state.show_new

st.title("📒 Recepty")

if st.session_state.show_new:
    with st.container():
        name=st.text_input("Název")
        portions=st.number_input("Porce",1,20,1)
        ing=st.text_area("Ingredience (řádek = položka)")
        steps=st.text_area("Postup")

        if st.button("Uložit"):
            if name:
                data={
                    "name":name,
                    "type":"",
                    "portions":portions,
                    "ingredients":convert_block(ing),
                    "steps":steps,
                    "fav":""
                }
                save_recipe(data)
                st.session_state.show_new=False
                st.rerun()

# ---------- LIST ----------
for r in recipes:
    with st.expander(r["name"]):

        colA,colB=st.columns([8,1])
        edit=colB.button("✏️",key="e"+r["name"])
        delete=colB.button("🗑️",key="d"+r["name"])

        if delete:
            delete_recipe(r["name"])
            st.rerun()

        mult = st.slider("Porce",1,20,int(r["portions"]),key=r["name"])

        st.markdown("**Ingredience**")
        for line in r["ingredients"].splitlines():
            st.markdown(f"<div class='ing'>{line.replace('|c','')}</div>",unsafe_allow_html=True)

        st.markdown("**Postup**")
        st.write(r["steps"])

        if edit:
            new_ing=st.text_area("Upravit ingredience",r["ingredients"].replace("|c",""),key="i"+r["name"])
            new_steps=st.text_area("Upravit postup",r["steps"],key="s"+r["name"])

            if st.button("Uložit změny",key="u"+r["name"]):
                data={
                    "ingredients":convert_block(new_ing),
                    "steps":new_steps
                }
                update_recipe(r["name"],data)
                st.rerun()
