import streamlit as st
import requests, json, os

st.set_page_config("Moje recepty", layout="centered")

API_URL="https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL="recepty.json"

# ================= DESIGN =================
st.markdown("""
<style>
.block-container{
padding-top:4rem;
padding-bottom:2rem;
max-width:700px;
}

/* background */
[data-testid="stAppViewContainer"]{
background: radial-gradient(circle at top,#0f2027,#203a43,#2c5364);
color:white;
}

/* header buttons */
.topbar button{
height:48px;
font-size:20px;
border-radius:14px;
background:#00b4ff;
color:white;
border:none;
}

/* cards */
.card{
background:white;
color:black;
padding:18px;
border-radius:18px;
box-shadow:0 6px 18px rgba(0,0,0,0.2);
margin-bottom:18px;
}

.title{
font-size:22px;
font-weight:700;
margin-bottom:10px;
}

/* inputs */
input,textarea{
color:black !important;
}
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
            return r.json()
    except:
        pass
    return load_local()

def save_online(data):
    try:
        requests.delete(API_URL+"/all")
        requests.post(API_URL,json=data)
        st.toast("☁ Uloženo do cloudu")
    except:
        st.toast("⚠ Cloud nedostupný — uloženo lokálně")
    save_local(data)

# ================= STATE =================
if "recipes" not in st.session_state:
    st.session_state.recipes=load_online()

# ================= HEADER =================
st.markdown("<h2 style='text-align:center'>📖 Moje recepty</h2>",unsafe_allow_html=True)

c1,c2,c3=st.columns([1,1,3],gap="small")

with c1:
    if st.button("➕",use_container_width=True):
        st.session_state.add=True

with c2:
    if st.button("☁",use_container_width=True):
        save_online(st.session_state.recipes)

search=c3.text_input("🔎 hledat")

# ================= ADD =================
if st.session_state.get("add"):

    st.markdown("### Nový recept")

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

    name=r.get("name","Bez názvu")
    typ=r.get("type","slané")
    ing=r.get("ingredients","")
    steps=r.get("steps","")

    if search and search.lower() not in name.lower():
        continue
    if typ=="sladké" and not show_sweet:
        continue
    if typ=="slané" and not show_salty:
        continue

    st.markdown(f"""
    <div class="card">
    <div class="title">{'🍰' if typ=="sladké" else '🥩'} {name}</div>
    <b>Ingredience:</b><br>{ing.replace(chr(10),"<br>")}<br><br>
    <b>Postup:</b><br>{steps.replace(chr(10),"<br>")}
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

    st.markdown("### Upravit recept")

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
