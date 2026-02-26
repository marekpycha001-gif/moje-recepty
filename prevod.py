import json

# Načte tvůj stažený klíč od Googlu
with open("credentials.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Vypíše to do konzole v dokonalém TOML formátu pro Streamlit
print("[gcp_service_account]")
for key, value in data.items():
    # Zabezpečí, že se text nerozpadne na více řádků
    val_str = str(value).replace('\n', '\\n')
    print(f'{key} = "{val_str}"')
