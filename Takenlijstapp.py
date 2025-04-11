import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime

st.set_page_config(page_title="Dagelijkse To-Do", page_icon="📝")

# Setup Google Sheets toegang
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_sheets"], scope)
client = gspread.authorize(credentials)
sheet = client.open_by_url(st.secrets["google_sheets"]["sheet_url"]).sheet1

def safe_rerun():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()
# Helpers
def get_today():
    return date.today().isoformat()

def fetch_tasks():
    records = sheet.get_all_records()
    return [r for r in records if r["Verwijderd"] == "FALSE" and r["Datum"] == get_today()]

def update_task_cell(task_id, col_name, value):
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):  # row 1 is headers
        if str(row["ID"]) == str(task_id):
            col_index = sheet.row_values(1).index(col_name) + 1
            sheet.update_cell(i, col_index, value)
            sheet.update_cell(i, sheet.row_values(1).index("Laatst Gewijzigd") + 1, datetime.now().isoformat())
            break

def soft_delete(task_id):
    update_task_cell(task_id, "Verwijderd", "TRUE")

# UI
st.title("📝 Dagelijkse To-Do Lijst")
st.markdown(f"📅 **{get_today()}**")

with st.form("add_form"):
    title = st.text_input("Titel")
    link = st.text_input("Link (optioneel)")
    if st.form_submit_button("➕ Taak toevoegen") and title:
        records = sheet.get_all_records()
        new_id = max([r["ID"] for r in records], default=0) + 1
        sheet.append_row([new_id, title, link, "FALSE", get_today(), datetime.now().isoformat(), "FALSE"])
        st.success("Taak toegevoegd!")
        safe_rerun()

# Toon taken
tasks = fetch_tasks()
if not tasks:
    st.info("Je hebt nog geen taken voor vandaag.")
else:
    for task in tasks:
        cols = st.columns([0.06, 0.65, 0.15, 0.14])
        task_id = task["ID"]
        is_done = task["Voltooid"] == "TRUE"

        with cols[0]:
            checked = st.checkbox("Voltooid", value=is_done, key=f"check_{task_id}", label_visibility="collapsed")
            if checked != is_done:
                update_task_cell(task_id, "Voltooid", "TRUE" if checked else "FALSE")

        with cols[1]:
            if task["Link"]:
                st.markdown(f"[{task['Titel']}]({task['Link']})", unsafe_allow_html=True)
            else:
                st.markdown(f"**{task['Titel']}**")

        with cols[2]:
            if cols[2].button("🗑️", key=f"delete_{task_id}"):
                soft_delete(task_id)
                safe_rerun()

        with cols[3]:
            st.caption(f"Gewijzigd: {task['Laatst Gewijzigd'].split('T')[0]}")

st.markdown("---")
st.caption("🛠️ Takenlijst werkt via Google Sheets + Streamlit")
