import streamlit as st
import json
import os

FILE="recipes.json"

# ---------- LOAD ----------
def load():
    if os.path.exists(FILE):
        with open(FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    return []

def save(data):
    with open(FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

recipes=load()

# ---------- SESSION ----------
if "edit" not in st.session_state:
    st.session_state.edit=None
if "search" not in st.session_state:
    st.session_state.search=""

# ---------- STYLE ----------
st.markdown("""
<style>
.block-container{padding-top:1rem;}
.ing div{margin-bottom:2px!important;line-height:1.1!important;}
button[kind="secondary"]{padding:2px 10px!important;font-size:12px!important;}
</style>
""",unsafe_allow_html=True)

# ---------- HEADER ----------
c1,c2=st.columns([1,1])

with c1:
    if st.button("➕",use_container_width=True):
        st.session_state.edit={"name":"","ingredients":"","type":"","labels":[]}

with c2:
    st.session_state.search=st.text_input("🔎",value=st.session_state.search,label_visibility="collapsed")

# ---------- FILTER ----------
search=st.session_state.search.lower()

filtered=[]
for r in recipes:
    text=(r.get("name","")+r.get("ingredients","")+r.get("type","")).lower()
    if search in text:
        filtered.append(r)

# ---------- EDIT FORM ----------
if st.session_state.edit is not None:
    r=st.session_state.edit

    st.subheader("Recept")

    r["name"]=st.text_input("Název",r["name"])
    r["type"]=st.text_input("Typ",r["type"])
    r["ingredients"]=st.text_area("Ingredience",r["ingredients"],height=120)

    c1,c2=st.columns(2)

    with c1:
        if st.button("💾 Uložit",use_container_width=True):

            if r not in recipes:
                recipes.insert(0,r)

            save(recipes)
            st.session_state.edit=None
            st.rerun()

    with c2:
        if st.button("❌ Zavřít",use_container_width=True):
            st.session_state.edit=None
            st.rerun()

    st.stop()

# ---------- LIST ----------
for r in filtered:

    box=st.container(border=True)

    with box:
        st.subheader(r["name"])

        st.caption(r["type"])

        ing=r["ingredients"].splitlines()

        with st.container():
            st.markdown('<div class="ing">',unsafe_allow_html=True)
            for i in ing:
                st.markdown(f"<div>• {i}</div>",unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)

        b1,b2=st.columns(2)

        with b1:
            if st.button("Upravit",key="e"+r["name"],use_container_width=True):
                st.session_state.edit=r
                st.rerun()

        with b2:
            if st.button("Smazat",key="d"+r["name"],use_container_width=True):
                recipes.remove(r)
                save(recipes)
                st.rerun()
