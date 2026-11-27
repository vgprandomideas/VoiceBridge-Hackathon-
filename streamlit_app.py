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

st.markdown("""<style>
.stButton button {min-height: 3rem; font-size: 1.05rem; border-radius: 12px;}
.stTextArea textarea {font-size: 1.1rem;}
.block-container {max-width: 760px; padding-top: 2rem;}
</style>""",unsafe_allow_html=True)
st.title("VoiceBridge")
st.caption("A simple way to ask for help and stay connected.")
if "access" not in st.session_state:
    st.session_state.access=""
with db() as con:
    staff=con.execute("SELECT id,name FROM groups WHERE token=?",(st.session_state.access,)).fetchone()
    resident=con.execute("SELECT id,gid,name FROM residents WHERE token=?",(st.session_state.access,)).fetchone()
if not staff and not resident:
    st.subheader("How can we help you?")
    role=st.radio("Choose your role",["I need assistance","I'm a caregiver"],horizontal=False)
    if role=="I'm a caregiver":
        st.write("Create a group for the people you care for, or reconnect to an existing group.")
        with st.form("create"):
            name=st.text_input("Name of your care group",placeholder="Example: Home care")
            if st.form_submit_button("Create a care group",type="primary",use_container_width=True):
                if name.strip():
                    gid,key=token(),token()
                    with db() as con:
                        con.execute("INSERT INTO groups VALUES (?,?,?)",(gid,name.strip()[:80],key))
                    st.session_state.access=key
                    st.rerun()
                else:
                    st.warning("Please enter a group name.")
    else:
        st.write("Ask your caregiver for your private code. Enter it below to start talking.")
    with st.form("connect"):
        access=st.text_input("Your private code",type="password")
        if st.form_submit_button("Connect",use_container_width=True):
            with db() as con:
                table="groups" if role=="I'm a caregiver" else "residents"
                valid=con.execute("SELECT id FROM "+table+" WHERE token=?",(access.strip(),)).fetchone()
            if valid:
                st.session_state.access=access.strip()
                st.rerun()
            else:
                st.error("Code not recognized. Check it with your caregiver.")
    st.caption("For demonstration only. Not an emergency service.")
    st.stop()
if st.button("Disconnect"):
    st.session_state.access=""
    st.rerun()
if staff:
    gid,name=staff
    st.header("Your care group: "+name)
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
    selected=st.selectbox("Who would you like to talk to?",people,format_func=lambda x:x[1])
    rid,_,key=selected
    with st.expander("Private resident invitation code"):
        st.code(key)
    sender="Caregiver"
else:
    rid,gid,name=resident
    st.header("Hello, "+name)
    st.write("Send a message to your caregiver below.")
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
st.subheader("What would you like to say?")
draft_key="draft_"+rid
if st.session_state.pop("clear_draft_"+rid,False):
    st.session_state[draft_key]=""
phrases=["I need water","I need food","Please help me","I feel unwell","I need the toilet","Thank you"] if resident else ["I am coming","How can I help?","Please wait","I understand"]
for i,phrase in enumerate(phrases):
    if i%2==0:
        cols=st.columns(2)
    if cols[i%2].button(phrase,use_container_width=True):
        st.session_state[draft_key]=phrase
body=st.text_area("Write your message or dictate using Wispr Flow.",key=draft_key,max_chars=700)
if st.button("Send message",type="primary",use_container_width=True) and body.strip():
    with db() as con:
        con.execute("INSERT INTO messages (rid,sender,body) VALUES (?,?,?)",(rid,sender,body.strip()))
    st.session_state["clear_draft_"+rid]=True
    st.rerun()
st.caption("Browser speech playback depends on device support. Translation and automatic transcription are not included in this Streamlit edition. Local SQLite data may be lost on cloud restarts.")
