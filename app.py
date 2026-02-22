import streamlit as st
import requests, json, os

st.set_page_config("Moje recepty", layout="centered")

API_URL="https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL="recepty.json"

# ================= STYLE =================
st.markdown("""
<style>
.block-container{padding-top:1rem}
.card{
background:white;
padding:15px;
border-radius:18px;
box-shadow:0 3px 12px rgba(0,0,0,0.1);
margin-bottom:15px;
}
.title{font-size:22px;font-weight:700}
</style>
""",unsafe_allow_html=True)

# ================= DATA =================
def load_local():
    if os.path.exists(LOCAL):
        return json.load(open(LOCAL,"r",encoding="utf8"))
    return []

def save_local(data):
    json.dump(data,open(LOCAL,"w",encoding="utf8"),ensure_ascii=False,indent=2)

def load_online():
    try:
        r=requests.get(API_URL,timeout=5)
        if r.status_code==200:
            data=[]
            for x in r.json():
                data.append({
                    "name":x.get("name",""),
                    "type":x.get("type","slané"),
                    "ingredients":x.get("ingredients",""),
                    "steps":x.get("steps","")
                })
            return data
    except:
        pass
    return load_local()

def save_online(data):
    try:
        requests.delete(API_URL+"/all")
        requests.post(API_URL,json=data)
    except:
        pass
    save_local(data)

# ================= STATE =================
if "recipes" not in st.session_state:
    st.session_state.recipes=load_online()

# ================= HEADER =================
c1,c2,c3=st.columns([1,1,4])

with c1:
    if st.button("➕",use_container_width=True):
        st.session_state.add=True

with c2:
    if st.button("🔄",use_container_width=True):
        save_online(st.session_state.recipes)

search=c3.text_input("🔎 hledat")

# ================= ADD =================
if st.session_state.get("add"):

    st.subheader("Nový recept")

    name=st.text_input("Název")
    typ=st.radio("Typ",["sladké","slané"],horizontal=True)
    ing=st.text_area("Ingredience")
    steps=st.text_area("Postup")

    if st.button("Uložit",use_container_width=True):
        st.session_state.recipes.insert(0,{
            "name":name,
            "type":typ,
            "ingredients":ing,
            "steps":steps
        })
        save_online(st.session_state.recipes)
        st.session_state.add=False
        st.rerun()

# ================= FILTER =================
f1,f2=st.columns(2)
show_sweet=f1.toggle("🍰 sladké",True)
show_salty=f2.toggle("🥩 slané",True)

# ================= LIST =================
for i,r in enumerate(st.session_state.recipes):

    if search and search.lower() not in r["name"].lower():
        continue
    if r["type"]=="sladké" and not show_sweet:
        continue
    if r["type"]=="slané" and not show_salty:
        continue

    st.markdown(f"""
    <div class="card">
    <div class="title">{'🍰' if r["type"]=="sladké" else '🥩'} {r["name"]}</div>
    <b>Ingredience:</b><br>{r["ingredients"].replace(chr(10),"<br>")}<br><br>
    <b>Postup:</b><br>{r["steps"].replace(chr(10),"<br>")}
    </div>
    """,unsafe_allow_html=True)

    b1,b2=st.columns(2)

    if b1.button("✏ Upravit",key="e"+str(i),use_container_width=True):
        st.session_state.edit=i
        st.rerun()

    if b2.button("🗑 Smazat",key="d"+str(i),use_container_width=True):
        st.session_state.recipes.pop(i)
        save_online(st.session_state.recipes)
        st.rerun()

# ================= EDIT =================
if "edit" in st.session_state:

    i=st.session_state.edit
    r=st.session_state.recipes[i]

    st.subheader("Upravit recept")

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
        save_online(st.session_state.recipes)
        del st.session_state.edit
        st.rerun()
