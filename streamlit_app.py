import streamlit as st
import sqlite3, secrets, os
from contextlib import contextmanager
import streamlit.components.v1 as components
import json

st.set_page_config(page_title="VoiceBridge", page_icon="🎙️", layout="centered")
@contextmanager
def db():
    con=sqlite3.connect(os.environ.get("VOICEBRIDGE_DB","voicebridge.sqlite"),timeout=15)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS groups (id TEXT PRIMARY KEY, name TEXT, token TEXT UNIQUE)")
        con.execute("CREATE TABLE IF NOT EXISTS residents (id TEXT PRIMARY KEY, gid TEXT, name TEXT, token TEXT UNIQUE)")
        con.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, rid TEXT, sender TEXT, body TEXT, status TEXT DEFAULT 'New')")
        yield con
        con.commit()
    finally:
        con.close()

def token():
    return secrets.token_urlsafe(32)

def speak(body):
    safe=json.dumps(body).replace("<","\\u003c")
    components.html('<button onclick="play()">Listen to message</button><script>function play(){if(window.speechSynthesis){speechSynthesis.cancel();speechSynthesis.speak(new SpeechSynthesisUtterance('+safe+'));}}</script>',height=45)

st.title("VoiceBridge")
st.caption("Communication without barriers")
st.info("Prototype only. Not for emergencies or clinical decisions. Use demonstration data.")
if "access" not in st.session_state:
    st.session_state.access=st.query_params.get("access","")
with st.sidebar:
    st.header("Connect")
    access=st.text_input("Private access code",type="password")
    if st.button("Connect"):
        st.session_state.access=access.strip()
        st.rerun()
    if st.button("Disconnect"):
        st.session_state.access=""
        st.query_params.clear()
        st.rerun()
with db() as con:
    staff=con.execute("SELECT id,name FROM groups WHERE token=?",(st.session_state.access,)).fetchone()
    resident=con.execute("SELECT id,gid,name FROM residents WHERE token=?",(st.session_state.access,)).fetchone()
if not staff and not resident:
    st.subheader("Create a Care Group")
    with st.form("create"):
        name=st.text_input("Group name")
        if st.form_submit_button("Create group") and name.strip():
            gid,key=token(),token()
            with db() as con:
                con.execute("INSERT INTO groups VALUES (?,?,?)",(gid,name.strip()[:80],key))
            st.session_state.access=key
            st.rerun()
    st.write("Residents can connect using their private access code. Wispr Flow users can dictate directly into editable text fields.")
    st.stop()
if staff:
    gid,name=staff
    st.header(name)
    with st.expander("Caregiver access code"):
        st.code(st.session_state.access)
    with st.form("add"):
        name=st.text_input("Resident name")
        if st.form_submit_button("Add resident") and name.strip():
            with db() as con:
                con.execute("INSERT INTO residents VALUES (?,?,?,?)",(token(),gid,name.strip()[:80],token()))
    with db() as con:
        people=con.execute("SELECT id,name,token FROM residents WHERE gid=?",(gid,)).fetchall()
    if not people:
        st.info("Add a resident to start communicating.")
        st.stop()
    selected=st.selectbox("Resident",people,format_func=lambda x:x[1])
    rid,_,key=selected
    with st.expander("Private resident invitation code"):
        st.code(key)
    sender="Caregiver"
else:
    rid,gid,name=resident
    st.header("Hello, "+name)
    sender="Resident"

@st.fragment(run_every=3)
def conversation():
    with db() as con:
        rows=con.execute("SELECT id,sender,body,status FROM messages WHERE rid=? ORDER BY id DESC LIMIT 50",(rid,)).fetchall()
    for mid,who,body,status in reversed(rows):
        with st.chat_message("user" if who==sender else "assistant"):
            st.text(who+" · "+status)
            st.write(body)
            speak(body)
            if staff and who=="Resident" and status=="New":
                if st.button("Acknowledge",key="ack"+str(mid)):
                    with db() as con:
                        con.execute("UPDATE messages SET status='Acknowledged' WHERE id=? AND rid=?",(mid,rid))
                    st.rerun(scope="fragment")
conversation()
st.subheader("Compose a message")
draft_key="draft_"+rid
for col,phrase in zip(st.columns(3),["I need water","Please help me","Thank you"]):
    if col.button(phrase):
        st.session_state[draft_key]=phrase
body=st.text_area("Type or dictate with Wispr Flow. Review before sending.",key=draft_key,max_chars=700)
if st.button("Send message",type="primary") and body.strip():
    with db() as con:
        con.execute("INSERT INTO messages (rid,sender,body) VALUES (?,?,?)",(rid,sender,body.strip()))
    st.rerun()
st.caption("Browser speech playback depends on device support. Translation and automatic transcription are not included in this Streamlit edition. Local SQLite data may be lost on cloud restarts.")
