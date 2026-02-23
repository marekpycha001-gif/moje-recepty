import streamlit as st
import json, os, re, requests

st.set_page_config(page_title="Moje recepty", layout="centered")

# ---------- STYLE ----------
st.markdown("""
<style>
.block-container {padding-top:1rem;padding-bottom:6rem;}
button[kind="primary"]{
    width:100%;border-radius:15px;height:3em;font-size:18px;
}
.bottom{
position:fixed;bottom:0;left:0;right:0;
background:#0e1117;padding:10px;z-index:999;
border-top:1px solid #333;
}
</style>
""",unsafe_allow_html=True)

FILE="recipes.json"

# ---------- LOAD ----------
if "recipes" not in st.session_state:
    if os.path.exists(FILE):
        st.session_state.recipes=json.load(open(FILE,"r",encoding="utf8"))
    else:
        st.session_state.recipes=[]

def save():
    json.dump(st.session_state.recipes,open(FILE,"w",encoding="utf8"),ensure_ascii=False,indent=2)

# ---------- CONVERT ----------
density={"olej":0.92,"mléko":1.03,"cukr":0.85,"mouka":0.53,"voda":1}
units={"lžíce":15,"lžička":5,"hrnek":240}

def convert(line):
    l=line.lower()

    m=re.search(r'(\d+)\s*ml\s*(\w+)',l)
    if m:
        g=int(int(m.group(1))*density.get(m.group(2),1))
        return f"{g} g {m.group(2)}"

    m=re.search(r'(\d+)\s*(lž[íi]ce|lž[íi]čka|hrnek)\s*(\w+)',l)
    if m:
        ml=units.get(m.group(2),0)*int(m.group(1))
        g=int(ml*density.get(m.group(3),1))
        return f"{g} g {m.group(3)}"

    return line

def convert_all(text):
    return "\n".join(convert(x) for x in text.splitlines())

# ---------- PAGE ----------
if "page" not in st.session_state:
    st.session_state.page="list"

# ---------- ADD ----------
if st.session_state.page=="add":
    st.title("Nový recept")

    name=st.text_input("Název")
    typ=st.radio("Typ",["sladké","slané"],horizontal=True)
    cat=st.text_input("Kategorie")
    portions=st.number_input("Porce",1,20,4)
    ing=st.text_area("Ingredience")
    steps=st.text_area("Postup")

    if st.button("Uložit",type="primary"):
        st.session_state.recipes.append({
            "name":name,
            "type":typ,
            "category":cat,
            "portions":portions,
            "ingredients":convert_all(ing),
            "steps":steps,
            "fav":False
        })
        save()
        st.session_state.page="list"
        st.rerun()

# ---------- LIST ----------
if st.session_state.page=="list":

    st.title("Moje recepty")

    q=st.text_input("Hledat")
    filt=st.radio("Filtr",["vše","sladké","slané","⭐ oblíbené"],horizontal=True)

    cats=sorted({r.get("category","") for r in st.session_state.recipes if r.get("category")})
    cat_filter=st.selectbox("Kategorie",["vše"]+cats)

    for i,r in enumerate(st.session_state.recipes):

        if q and q.lower() not in r["name"].lower(): continue
        if filt=="sladké" and r["type"]!="sladké": continue
        if filt=="slané" and r["type"]!="slané": continue
        if filt=="⭐ oblíbené" and not r.get("fav"): continue
        if cat_filter!="vše" and r.get("category")!=cat_filter: continue

        title=("⭐ " if r.get("fav") else "")+("🍰 " if r["type"]=="sladké" else "🥩 ")+r["name"]

        with st.expander(title):

            mult=st.slider("Porce",1,20,r["portions"],key=i)

            st.markdown("**Kategorie:** "+(r.get("category") or "—"))

            st.markdown("**Ingredience**")
            for line in r["ingredients"].splitlines():
                m=re.search(r'(\d+)',line)
                if m:
                    num=int(m.group(1))
                    new=int(num*mult/r["portions"])
                    line=line.replace(str(num),str(new),1)
                st.write("•",line)

            st.markdown("**Postup**")
            st.write(r["steps"])

            c1,c2,c3=st.columns(3)

            with c1:
                if st.button("⭐",key="fav"+str(i)):
                    r["fav"]=not r.get("fav",False)
                    save(); st.rerun()

            with c2:
                if st.button("🗑",key="del"+str(i)):
                    st.session_state.recipes.pop(i)
                    save(); st.rerun()

            with c3:
                if st.button("☁️",key="sync"+str(i)):
                    try:
                        requests.post("TVŮJ_SHEET_ENDPOINT",json=r)
                        st.success("Sync OK")
                    except:
                        st.error("Sheet nepřipojen")

# ---------- BOTTOM NAV ----------
st.markdown('<div class="bottom">',unsafe_allow_html=True)
c1,c2=st.columns(2)
with c1:
    if st.button("➕"):
        st.session_state.page="add"; st.rerun()
with c2:
    if st.button("📋"):
        st.session_state.page="list"; st.rerun()
st.markdown('</div>',unsafe_allow_html=True)
