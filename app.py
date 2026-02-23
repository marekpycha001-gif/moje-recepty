import streamlit as st
import json, os, re, requests

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

SDB_URL="https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE="recipes.json"

# ---------- SESSION ----------
defaults = {
    "recipes": [],
    "show_new": False,
    "show_search": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- STORAGE ----------
def load_local():
    if os.path.exists(LOCAL_FILE):
        return json.load(open(LOCAL_FILE, encoding="utf8"))
    return []

def save_local(d):
    with open(LOCAL_FILE, "w", encoding="utf8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def load_db():
    recipes = []
    try:
        r = requests.get(SDB_URL, timeout=3)
        if r.status_code == 200:
            for x in r.json():
                recipes.append({
                    "name": x.get("name","Bez názvu"),
                    "type": x.get("type","slané"),
                    "portions": x.get("portions",4),
                    "ingredients": x.get("ingredients",""),
                    "steps": x.get("steps",""),
                    "fav": x.get("fav", False)
                })
    except:
        pass
    if not recipes:
        recipes = load_local()
    for r in recipes:
        r.setdefault("name","Bez názvu")
        r.setdefault("type","slané")
        r.setdefault("portions",4)
        r.setdefault("ingredients","")
        r.setdefault("steps","")
        r.setdefault("fav", False)
    return recipes

def save_db():
    try:
        requests.delete(SDB_URL+"/all", timeout=3)
        requests.post(SDB_URL, json=st.session_state.recipes, timeout=3)
    except:
        st.warning("⚠️ Nepodařilo se připojit k Google Sheet.")
    save_local(st.session_state.recipes)

if not st.session_state.recipes:
    st.session_state.recipes = load_db()

# ---------- UNIT CONVERSIONS ----------
# hustota běžných surovin v g/ml
density = {
    "voda":1, "mléko":1.03, "olej":0.92, "máslo":0.91, "cukr":0.85, "cukr krupice":0.85,
    "mouka":0.55, "mouka hladká":0.55, "mouka hrubá":0.65, "kakao":0.55, "sůl":1.2, "škrob":0.6
}

volume_units = {
    "lžíce":15, "lžička":5, "čaj lžička":5, "ml":1, "cl":10, "dl":100, "hrnek":240
}

def convert_to_grams(line):
    """
    Rozpozná množství, jednotku a surovinu. Převádí na gramy podle hustoty.
    """
    m = re.match(r'([\d.,/]+)\s*(\w+)?\s*(.*)', line)
    if not m:
        return line
    qty, unit, rest = m.groups()
    try:
        if '/' in qty:
            num = float(sum([float(eval(fraction)) for fraction in qty.split()]))
        else:
            num = float(qty.replace(',','.'))
    except:
        return line
    # převod objemových jednotek na ml
    if unit in volume_units:
        ml = num * volume_units[unit]
        # zkus najít surovinu
        for key in density:
            if key in rest.lower():
                grams = ml * density[key]
                return f"{int(grams)} g {rest}"
        # pokud nenajde konkrétní surovinu, ml → g (voda)
        grams = ml
        return f"{int(grams)} g {rest}"
    return line

# ---------- DESIGN ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');
body,[data-testid="stAppViewContainer"]{background:radial-gradient(circle at bottom,#000428,#004e92); color:white;}
.topbar{display:flex; justify-content:center; gap:4px; margin-bottom:10px; flex-wrap:nowrap;}
.topbtn{background:#0099ff; color:white; border:none; padding:5px 10px; border-radius:8px; font-size:18px; cursor:pointer;}
.title{font-family:'Dancing Script',cursive; font-size:22px; text-align:center; color:#00ccff; margin-bottom:15px;}
.stExpanderHeader{background:#1E3A8A !important; color:white !important; border-radius:10px;}
.stExpanderContent{background:#cce0ff !important; color:black !important; border-radius:10px;}
.stTextInput>div>div>input, .stNumberInput>div>div>input, textarea{color:black;}
</style>
""",unsafe_allow_html=True)

# ---------- CALLBACKS ----------
def toggle_show_new(): st.session_state.show_new = not st.session_state.show_new
def toggle_show_search(): st.session_state.show_search = not st.session_state.show_search
def sync_all(): save_db(); st.success("Synchronizováno!")

# ---------- TOP ICON BAR ----------
col1, col2, col3 = st.columns([1,1,1])
with col1: st.button("➕", on_click=toggle_show_new)
with col2: st.button("🔍", on_click=toggle_show_search)
with col3: st.button("☁️ Sync", on_click=sync_all)

# ---------- TITLE ----------
st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search = st.text_input("Hledat recept podle názvu/ingrediencí")

# ---------- NEW RECIPE ----------
if st.session_state.show_new:
    st.markdown("### Přidat nový recept")
    name=st.text_input("Název")
    typ=st.radio("Typ",["sladké","slané"],horizontal=True)
    portions=st.number_input("Počet porcí",1,20,4)
    ingredients=st.text_area("Ingredience (každá na nový řádek)")
    steps=st.text_area("Postup")
    def save_new_recipe():
        st.session_state.recipes.insert(0,{
            "name": name or "Bez názvu",
            "type": typ,
            "portions": portions,
            "ingredients": ingredients,
            "steps": steps,
            "fav": False
        })
        save_db()
    st.button("Uložit recept", on_click=save_new_recipe)

# ---------- DISPLAY RECIPES ----------
for i,r in enumerate(st.session_state.recipes):
    r.setdefault("portions",4)
    r.setdefault("fav",False)
    title_prefix = "⭐ " if r.get("fav") else ""
    title = title_prefix + r["name"]

    if search and search.lower() not in (r["name"]+r["ingredients"]).lower():
        continue

    with st.expander(title):
        # --- EDIT ---
        edit_name = st.text_input("Název", r["name"], key=f"name{i}")
        edit_type = st.radio("Typ", ["sladké","slané"], index=0 if r["type"]=="sladké" else 1, key=f"type{i}")
        edit_portions = st.number_input("Počet porcí",1,20,r["portions"], key=f"portions{i}")
        edit_ingredients = st.text_area("Ingredience", r["ingredients"], key=f"ing{i}")
        edit_steps = st.text_area("Postup", r["steps"], key=f"steps{i}")

        def save_edit(i=i):
            r["name"] = edit_name
            r["type"] = edit_type
            r["portions"] = edit_portions
            r["ingredients"] = edit_ingredients
            r["steps"] = edit_steps
            save_db()
        st.button("💾 Uložit změny", key=f"save{i}", on_click=save_edit)

        # --- INGREDIENTS WITH CONVERSION ---
        st.markdown("### Ingredience podle porcí")
        for line in edit_ingredients.splitlines():
            # přepočet množství podle porcí
            m = re.search(r'(\d+)', line)
            display_line = line
            if m:
                num=int(m.group(1))
                new=int(num*edit_portions/r["portions"])
                display_line=line.replace(str(num),str(new),1)
            display_line = convert_to_grams(display_line)
            st.write("•", display_line)

        st.markdown("**Postup**")
        st.write(edit_steps)

        # --- ACTIONS ---
        c1,c2,c3 = st.columns([1,1,1])
        def toggle_fav(i=i):
            r["fav"] = not r.get("fav",False)
            save_db()
        c1.button("⭐", key=f"fav{i}", on_click=toggle_fav)

        def delete_recipe(i=i):
            st.session_state.recipes.pop(i)
            save_db()
        c2.button("🗑", key=f"del{i}", on_click=delete_recipe)

        def sync_recipe(i=i):
            try:
                requests.post(SDB_URL,json=r)
                st.success("Synchronizováno")
            except:
                st.warning("⚠️ Nepodařilo se připojit k Google Sheet")
        c3.button("☁️", key=f"sync{i}", on_click=sync_recipe)
