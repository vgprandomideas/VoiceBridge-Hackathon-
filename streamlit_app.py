import streamlit as st
import sqlite3, secrets, os
from contextlib import contextmanager
import streamlit.components.v1 as components
import json
from urllib.parse import urlencode
import re
import time

st.set_page_config(page_title="VoiceBridge", page_icon="🎙️", layout="centered")
@contextmanager
def db():
    con=sqlite3.connect(os.environ.get("VOICEBRIDGE_DB","voicebridge.sqlite"),timeout=15)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS groups (id TEXT PRIMARY KEY, name TEXT, token TEXT UNIQUE)")
        con.execute("CREATE TABLE IF NOT EXISTS residents (id TEXT PRIMARY KEY, gid TEXT, name TEXT, token TEXT UNIQUE)")
        con.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, rid TEXT, sender TEXT, body TEXT, status TEXT DEFAULT 'New')")
        if "expires" not in [r[1] for r in con.execute("PRAGMA table_info(residents)")]:
            con.execute("ALTER TABLE residents ADD COLUMN expires INTEGER NOT NULL DEFAULT 0")
        yield con
        con.commit()
    finally:
        con.close()

def token():
    return secrets.token_urlsafe(32)

def invite_code(con):
    while True:
        code="".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(10))
        if not con.execute("SELECT 1 FROM residents WHERE token=?",(code,)).fetchone():
            return code

def speak(body):
    safe=json.dumps(body).replace("<","\\u003c")
    components.html('<button onclick="play()">Listen to message</button><script>function play(){if(window.speechSynthesis){speechSynthesis.cancel();speechSynthesis.speak(new SpeechSynthesisUtterance('+safe+'));}}</script>',height=45)

st.markdown("""<style>
.stApp {background: radial-gradient(ellipse at 90% 0%, #dcefeb 0%, transparent 45%), linear-gradient(145deg,#f7fafc,#edf3f8); color:#142d40;}
[data-testid="stHeader"] {background:transparent;}
.block-container {max-width:760px;padding:2.5rem 1.4rem 3rem;}
.stButton button, .stFormSubmitButton button {min-height:3.2rem;font-size:1.05rem;border-radius:12px;font-weight:600;}
.stTextArea textarea {font-size:1.1rem;}
[data-testid="stForm"], [data-testid="stChatMessage"] {background:#ffffff;border:1px solid #d7e3e9;border-radius:16px;padding:1rem;}
h1,h2,h3,p,label {color:#142d40;}
.vb-brand {background:linear-gradient(120deg,#102c43,#126c70);border-radius:20px;padding:28px;color:white;margin-bottom:24px;box-shadow:0 10px 30px #163c5020;}
.vb-brand h1 {color:white;margin:0;font-size:2.2rem;}
.vb-brand p {color:#e0f4f1;margin:8px 0 0;}
</style>""",unsafe_allow_html=True)
st.markdown('<div class="vb-brand"><h1>VoiceBridge</h1><p>A simple way to ask for help and stay connected.</p></div>',unsafe_allow_html=True)
if "access" not in st.session_state:
    st.session_state.access=st.query_params.get("join","").strip()
    st.query_params.clear()
    with db() as con:
        if not con.execute("SELECT 1 FROM residents WHERE token=? AND expires>?",(st.session_state.access,int(time.time()))).fetchone():
            st.session_state.access=""
with db() as con:
    staff=con.execute("SELECT id,name FROM groups WHERE token=?",(st.session_state.access,)).fetchone()
    resident=con.execute("SELECT id,gid,name FROM residents WHERE token=?",(st.session_state.access,)).fetchone()
if not staff and not resident:
    if st.session_state.access:
        st.warning("This invitation is no longer available. Ask your caregiver for a new one.")
        st.session_state.access=""
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
        access=st.text_input("Enter your connection code",placeholder="Paste the code here")
        if st.form_submit_button("Connect",use_container_width=True):
            with db() as con:
                table="groups" if role=="I'm a caregiver" else "residents"
                candidate=access.strip()
                if table=="residents":
                    candidate=re.sub(r"[\\s-]","",candidate).upper() if len(re.sub(r"[\\s-]","",candidate))==10 else candidate
                valid=con.execute("SELECT id FROM residents WHERE token=? AND expires>?",(candidate,int(time.time()))).fetchone() if table=="residents" else con.execute("SELECT id FROM groups WHERE token=?",(candidate,)).fetchone()
            if valid:
                st.session_state.access=candidate
                st.rerun()
            else:
                st.error("Code not recognized. Check it with your caregiver.")
    st.caption("For demonstration only. Not an emergency service.")
    st.stop()
if st.button("Disconnect"):
    st.session_state.access=""
    st.query_params.clear()
    st.rerun()
if staff:
    gid,name=staff
    st.header("People you help")
    st.caption(name)
    with st.expander("Caregiver access code"):
        st.code(st.session_state.access)
    with st.form("add"):
        name=st.text_input("Name of the person you help")
        if st.form_submit_button("Add person",use_container_width=True) and name.strip():
            with db() as con:
                con.execute("INSERT INTO residents (id,gid,name,token,expires) VALUES (?,?,?,?,?)",(token(),gid,name.strip()[:80],invite_code(con),int(time.time())+180))
    with db() as con:
        people=con.execute("SELECT id,name,token,expires FROM residents WHERE gid=?",(gid,)).fetchall()
    if not people:
        st.info("Enter a name above and tap Add person to create their invitation.")
        st.stop()
    selected=st.selectbox("Who would you like to talk to?",people,format_func=lambda x:x[1])
    rid,_,key,expires=selected
    with st.expander("Invite this person",expanded=True):
        if st.button("Generate fresh 3-minute invitation",use_container_width=True):
            with db() as con:
                con.execute("UPDATE residents SET expires=? WHERE id=? AND gid=?",(int(time.time())+180,rid,gid))
            st.rerun()
        st.write("Invitation expires 3 minutes after generation. Existing conversations remain active.")
        if expires<=time.time():
            st.warning("Invitation expired. Generate a fresh invitation above.")
        else:
            st.caption("Invitation valid until "+time.strftime("%H:%M:%S UTC",time.gmtime(expires)))
        base=os.environ.get("VOICEBRIDGE_PUBLIC_URL","https://voicebridgesolutions.streamlit.app/")
        st.code(base.rstrip("/")+"/?"+urlencode({"join":key}),language=None)
        st.caption("Or enter this code on the assistance screen:")
        st.code(key,language=None)
        st.caption("Anyone with this invitation can access this conversation. Share privately.")
    sender="Caregiver"
else:
    rid,gid,name=resident
    st.header("Hello, "+name)
    st.write("Send a message to your caregiver below.")
    sender="Resident"

@st.fragment(run_every=0.5)
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
conversation()
st.caption("Browser speech playback depends on device support. Translation and automatic transcription are not included in this Streamlit edition. Local SQLite data may be lost on cloud restarts.")
