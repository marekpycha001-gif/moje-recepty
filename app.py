# ---------- IKONY NAHOŘE (malé čtverečky vedle sebe) ----------
st.markdown("""
<div style="display:flex; justify-content:flex-start; gap:4px; margin-bottom:10px;">
    <button style="width:35px; height:35px; font-size:20px; background:#0099ff; color:white; border:none; border-radius:8px; cursor:pointer;" onclick="document.querySelector('#btn_plus').click()">➕</button>
    <button style="width:35px; height:35px; font-size:20px; background:#0099ff; color:white; border:none; border-radius:8px; cursor:pointer;" onclick="document.querySelector('#btn_sync').click()">🔄</button>
    <button style="width:35px; height:35px; font-size:20px; background:#0099ff; color:white; border:none; border-radius:8px; cursor:pointer;" onclick="document.querySelector('#btn_search').click()">🔍</button>
    <button style="width:35px; height:35px; font-size:20px; background:#0099ff; color:white; border:none; border-radius:8px; cursor:pointer;" onclick="document.querySelector('#btn_api').click()">🔑</button>
</div>
""", unsafe_allow_html=True)

# skryté tlačítka pro Streamlit akce
st.button("", key="btn_plus", on_click=lambda: st.session_state.update({"show_new": not st.session_state.show_new}))
st.button("", key="btn_sync", on_click=lambda: save_db())
st.button("", key="btn_search", on_click=lambda: st.session_state.update({"show_search": not st.session_state.show_search}))
st.button("", key="btn_api", on_click=lambda: st.session_state.update({"show_api": not st.session_state.show_api}))
