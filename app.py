import streamlit as st
import requests
import re

st.set_page_config(page_title="Recepty", layout="centered")

API_URL="https://sheetdb.io/api/v1/5ygnspqc90f9d"

# ---------- STYL ----------
st.markdown("""
<style>
.block-container{padding-top:1rem;padding-bottom:4rem;}
.ing{margin:0;line-height:1.2em;}
button{border-radius:12px!important;}
</style>
""",unsafe_allow_html=True)

# ---------- PŘEVODY ----------
densities={
 "olej":0.92,
 "mléko":1.03,
 "voda":1.0,
 "med":1.42
}

units={
 "lž":15,"lžíce":15,
 "lžič":5,"lžička":5,
 "hrnek":240,"hrnky":240
}

def density(name):
    name=name.lower()
    for k,v in densities.items():
        if k in name:
            return v
    return 1.0

def convert(line):
    if "|manual" in line:
        return line

    txt=line.strip().lower()

    # číslo + jednotka + surovina
    m=re.match(r"([\d\.,]+)\s*(ml|l|g|kg)\s+(.*)",txt)
    if m:
        val=float(m.group(1).replace(",","."))
        unit=m.group(2)
        name=m.group(3)

        if unit=="kg":
            val*=1000
        if unit=="l":
            val*=1000

        if unit in ["ml","l"]:
            val*=density(name)

        return f"{round(val)} g {name}"

    # lžíce hrnky
    m=re.match(r"([\d\.,]+)\s*(lž|lžíce|lžič|lžička|hrnek|hrnky)\s+(.*)",txt)
    if m:
        val=float(m.group(1).replace(",","."))
        unit=m.group(2)
        name=m.group(3)

        ml=val*units[unit]
        g=ml*density(name)

        return f"{round(g)} g {name}"

    return line

def convert_block(text):
    return "\n".join(convert(l) for l in text.splitlines() if l.strip())

# ---------- API ----------
def load():
    try:
        r=requests.get(API_URL)
        data=r.json()
        return [x for x in data if isinstance(x,dict) and x.get("name")]
    except:
        return []

def save(data):
    requests.post(API_URL,json=data)

def update(name,data):
    requests.patch(f"{API_URL}/name/{name}",json=data)

def delete(name):
    requests.delete(f"{API_URL}/name/{name}")

recipes=load()

# ---------- HEADER ----------
if "new" not in st.session_state:
    st.session_state.new=False

col1,col2=st.columns([1,7])
if col1.button("➕"):
    st.session_state.new=not st.session_state.new

st.title("📒 Recepty")

# ---------- NOVÝ ----------
if st.session_state.new:

    name=st.text_input("Název")
    portions=st.number_input("Porce",1,20,1)
    ing=st.text_area("Ingredience")
    steps=st.text_area("Postup")

    if st.button("Uložit"):
        if name:
            save({
                "name":name,
                "type":"",
                "portions":portions,
                "ingredients":convert_block(ing),
                "steps":steps,
                "fav":""
            })
            st.session_state.new=False
            st.rerun()

# ---------- SEZNAM ----------
for r in recipes:

    with st.expander(r["name"]):

        c1,c2=st.columns([8,1])

        edit=c2.button("✏️",key="e"+r["name"])
        delete_btn=c2.button("🗑️",key="d"+r["name"])

        if delete_btn:
            delete(r["name"])
            st.rerun()

        portions=int(r.get("portions",1))
        st.slider("Porce",1,20,portions,key="p"+r["name"])

        st.markdown("**Ingredience**")
        for l in r.get("ingredients","").splitlines():
            st.markdown(f"<div class='ing'>{l}</div>",unsafe_allow_html=True)

        st.markdown("**Postup**")
        st.write(r.get("steps",""))

        # ---------- EDIT ----------
        if edit:

            new_ing=st.text_area("Ingredience",
                                 r.get("ingredients",""),
                                 key="i"+r["name"])

            new_steps=st.text_area("Postup",
                                   r.get("steps",""),
                                   key="s"+r["name"])

            if st.button("Uložit změny",key="u"+r["name"]):

                update(r["name"],{
                    "ingredients":convert_block(new_ing),
                    "steps":new_steps
                })

                st.rerun()
