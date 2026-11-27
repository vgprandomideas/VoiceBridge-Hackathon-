import streamlit as st
import sqlite3, secrets, os
from contextlib import contextmanager
import streamlit.components.v1 as components
import json
from urllib.parse import urlencode
import re
import time
import requests

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
        con.execute("CREATE TABLE IF NOT EXISTS reverse_invites (code TEXT PRIMARY KEY, gid TEXT, expires INTEGER)")
        if "audio" not in [r[1] for r in con.execute("PRAGMA table_info(messages)")]:
            con.execute("ALTER TABLE messages ADD COLUMN audio BLOB")
        con.execute("CREATE TABLE IF NOT EXISTS translations (mid INTEGER, lang TEXT, body TEXT, PRIMARY KEY(mid,lang))")
        yield con
        con.commit()
    finally:
        con.close()

def token():
    return secrets.token_urlsafe(32)

def invite_code(con):
    while True:
        code="".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(10))
        if not con.execute("SELECT 1 FROM residents WHERE token=? UNION SELECT 1 FROM reverse_invites WHERE code=?",(code,code)).fetchone():
            return code

def share_invite(code, role):
    base=os.environ.get("VOICEBRIDGE_PUBLIC_URL","https://voicebridgesolutions.streamlit.app/")
    link=base.rstrip("/")+"/?"+urlencode({"join":code,"role":role})
    message="Join me on VoiceBridge. Connection code: "+code+" (valid for 3 minutes). Open: "+link
    st.link_button("Share via WhatsApp","https://wa.me/?"+urlencode({"text":message}),use_container_width=True)
    st.code(link,language=None)

LANGUAGES={"English":"en","Tamil — தமிழ்":"ta","Hindi — हिन्दी":"hi","Telugu — తెలుగు":"te","Malayalam — മലയാളം":"ml","Kannada — ಕನ್ನಡ":"kn","Bengali — বাংলা":"bn","Marathi — मराठी":"mr","Gujarati — ગુજરાતી":"gu","Punjabi — ਪੰਜਾਬੀ":"pa","Odia — ଓଡ଼ିଆ":"or","Urdu — اردو":"ur","Assamese — অসমীয়া":"as"}

def translate_message(mid, body, target):
    with db() as con:
        row=con.execute("SELECT body FROM translations WHERE mid=? AND lang=?",(mid,target)).fetchone()
    if row:
        return row[0]
    try:
        response=requests.get("https://translate.googleapis.com/translate_a/single",params={"client":"gtx","sl":"auto","tl":target,"dt":"t","q":body},timeout=4)
        response.raise_for_status()
        translated="".join(part[0] or "" for part in response.json()[0])
        if not translated:
            return None
        with db() as con:
            con.execute("INSERT OR REPLACE INTO translations VALUES (?,?,?)",(mid,target,translated))
        return translated
    except Exception:
        return None

def speak(body, lang="en"):
    safe=json.dumps(body).replace("<","\\u003c")
    components.html('<button onclick="play()">Listen to message</button><script>function play(){if(window.speechSynthesis){speechSynthesis.cancel();let u=new SpeechSynthesisUtterance('+safe+');u.lang='+json.dumps(lang+"-IN")+';speechSynthesis.speak(u);}}</script>',height=45)

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
    join_role=st.query_params.get("role","receiver")
    st.query_params.clear()
    with db() as con:
        if join_role=="giver":
            match=con.execute("SELECT groups.token FROM reverse_invites JOIN groups ON groups.id=reverse_invites.gid WHERE code=? AND expires>?",(st.session_state.access,int(time.time()))).fetchone()
            st.session_state.access=match[0] if match else ""
        elif not con.execute("SELECT 1 FROM residents WHERE token=? AND expires>?",(st.session_state.access,int(time.time()))).fetchone():
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
        st.write("Create a code and share it with the person you want to help.")
        if st.button("Create connection code",type="primary",use_container_width=True):
            gid,key=token(),token()
            with db() as con:
                con.execute("INSERT INTO groups VALUES (?,?,?)",(gid,"Quick connection",key))
                con.execute("INSERT INTO residents (id,gid,name,token,expires) VALUES (?,?,?,?,?)",(token(),gid,"Assistance receiver",invite_code(con),int(time.time())+180))
            st.session_state.access=key
            st.rerun()
        st.caption("For multiple people, create a care group below.")
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
        st.write("Create a code to share with your helper, or enter a code they sent.")
        if st.button("Create connection code",type="primary",use_container_width=True):
            gid,staffkey,rid,reskey=token(),token(),token(),token()
            with db() as con:
                con.execute("INSERT INTO groups VALUES (?,?,?)",(gid,"Quick connection",staffkey))
                con.execute("INSERT INTO residents (id,gid,name,token,expires) VALUES (?,?,?,?,?)",(rid,gid,"Assistance receiver",reskey,0))
                code=invite_code(con)
                con.execute("INSERT INTO reverse_invites VALUES (?,?,?)",(code,gid,int(time.time())+180))
            st.session_state.access=reskey
            st.rerun()
    with st.form("connect"):
        access=st.text_input("Enter your connection code",placeholder="Paste the code here")
        if st.form_submit_button("Connect",use_container_width=True):
            with db() as con:
                table="groups" if role=="I'm a caregiver" else "residents"
                candidate=access.strip()
                if table=="residents":
                    candidate=re.sub(r"[\s-]","",candidate).upper() if len(re.sub(r"[\s-]","",candidate))==10 else candidate
                valid=con.execute("SELECT id FROM residents WHERE token=? AND expires>?",(candidate,int(time.time()))).fetchone() if table=="residents" else con.execute("SELECT id FROM groups WHERE token=?",(candidate,)).fetchone()
            if not valid and table=="groups":
                with db() as con:
                    match=con.execute("SELECT groups.token FROM reverse_invites JOIN groups ON groups.id=reverse_invites.gid WHERE code=? AND expires>?",(re.sub(r"[\s-]","",candidate).upper(),int(time.time()))).fetchone()
                if match:
                    candidate=match[0]
                    valid=True
            if valid:
                st.session_state.access=candidate
                st.rerun()
            else:
                st.error("Code not recognized. Check it with your caregiver.")
    st.caption("Connect from Android, iPhone, Windows or Mac using a modern browser. Microphone permission is needed for recording. No VoiceBridge installation required.")
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
    with st.expander("Your connection code — share with receiver",expanded=True):
        if st.button("Renew connection code (3 minutes)",use_container_width=True):
            with db() as con:
                con.execute("UPDATE residents SET expires=? WHERE id=? AND gid=?",(int(time.time())+180,rid,gid))
            st.rerun()
        st.write("Invitation expires 3 minutes after generation. Existing conversations remain active.")
        if expires<=time.time():
            st.warning("Invitation expired. Generate a fresh invitation above.")
        else:
            st.caption("Invitation valid until "+time.strftime("%H:%M:%S UTC",time.gmtime(expires)))
        base=os.environ.get("VOICEBRIDGE_PUBLIC_URL","https://voicebridgesolutions.streamlit.app/")
        if expires>time.time():
            share_invite(key,"receiver")
        st.caption("Or enter this code on the assistance screen:")
        st.code(key,language=None)
        st.caption("Anyone with this invitation can access this conversation. Share privately.")
    sender="Caregiver"
else:
    rid,gid,name=resident
    st.header("Hello, "+name)
    st.write("Send a message to your caregiver below.")
    sender="Resident"
    with db() as con:
        invitation=con.execute("SELECT code,expires FROM reverse_invites WHERE gid=? ORDER BY expires DESC LIMIT 1",(gid,)).fetchone()
    if invitation:
        with st.expander("Your connection code — share with caregiver",expanded=True):
            if invitation[1]>time.time():
                st.code(invitation[0],language=None)
                share_invite(invitation[0],"giver")
                st.caption("Valid until "+time.strftime("%H:%M:%S UTC",time.gmtime(invitation[1])))
            else:
                st.warning("Connection code expired.")
            if st.button("Create fresh connection code",use_container_width=True):
                with db() as con:
                    con.execute("DELETE FROM reverse_invites WHERE gid=?",(gid,))
                    con.execute("INSERT INTO reverse_invites VALUES (?,?,?)",(invite_code(con),gid,int(time.time())+180))
                st.rerun()

preferred=st.selectbox("Read and listen in your preferred language",list(LANGUAGES),key="preferred_language")
target=LANGUAGES[preferred]
allow_translation=st.checkbox("Translate incoming messages automatically (sends text to external translation service)",value=True)
st.caption("Demo data only. Translation can be inaccurate; confirm important requests.")

@st.fragment(run_every=0.5)
def inbox_status():
    with db() as con:
        latest=con.execute("SELECT COALESCE(MAX(id),0) FROM messages WHERE rid=?",(rid,)).fetchone()[0]
    if latest>st.session_state.get("seen_"+rid,0):
        st.info("New message available — tap Refresh conversation below.")
    else:
        st.caption("Listening for new messages…")

def conversation():
    with db() as con:
        rows=con.execute("SELECT id,sender,body,status,audio FROM messages WHERE rid=? ORDER BY id DESC LIMIT 50",(rid,)).fetchall()
    st.session_state["seen_"+rid]=max([r[0] for r in rows],default=0)
    for mid,who,body,status,audio in reversed(rows):
        with st.chat_message("user" if who==sender else "assistant"):
            st.text(who+" · "+status)
            if body:
                st.text(body)
                if who!=sender and allow_translation:
                    attempt="translated_"+str(mid)+"_"+target
                    if attempt not in st.session_state:
                        st.session_state[attempt]=translate_message(mid,body,target)
                    translated=st.session_state[attempt]
                    if translated:
                        st.caption("Translation · "+preferred)
                        st.text(translated)
                        speak(translated,target)
                    else:
                        st.caption("Translation unavailable. Original text shown.")
                        if st.button("Retry translation",key="retry_"+str(mid)):
                            st.session_state.pop(attempt,None)
                            st.rerun()
                else:
                    speak(body,target)
            if audio:
                st.audio(audio,format="audio/wav")
            if staff and who=="Resident" and status=="New":
                if st.button("Acknowledge",key="ack"+str(mid)):
                    with db() as con:
                        con.execute("UPDATE messages SET status='Acknowledged' WHERE id=? AND rid=?",(mid,rid))
                    st.rerun()
st.subheader("What would you like to say?")
st.markdown("**Choose your communication method**")
method=st.radio("Input method",["Type a message","Dictate with Wispr Flow","Record original voice"],horizontal=False,key="input_method")
if method=="Dictate with Wispr Flow":
    st.link_button("Open Wispr Flow","https://wisprflow.ai/",use_container_width=True)
    st.caption("Tap the message field below, then activate Flow using your device controls.")
    with st.expander("Connect Wispr Flow on your device",expanded=True):
        st.markdown("**Android:** Tap the message field, then the Flow Bubble. **iPhone:** Switch to the Flow keyboard and tap its microphone. **Windows:** Hold Ctrl + Win. **Mac:** Hold Fn (or your configured shortcut). Finish dictating and review the inserted text.")
        st.link_button("Setup and troubleshooting","https://docs.wisprflow.ai/articles/6409258247-starting-your-first-dictation")
st.write("Tap the message box, activate Wispr Flow on your device and speak at your own pace. Review your words before sending.")
with st.expander("How to use Wispr Flow"):
    st.write("1. Install and enable Wispr Flow on a supported device.\n\n2. Select the message box below.\n\n3. Activate Flow using your configured shortcut or supported keyboard.\n\n4. Finish dictating, review the text and tap Send message.")
    st.link_button("Get Wispr Flow","https://wisprflow.ai/")
    st.caption("VoiceBridge receives text through device-level dictation. No direct Wispr API connection is used. If Flow is unavailable, type or select a quick phrase.")
draft_key="draft_"+rid
if st.session_state.pop("clear_draft_"+rid,False):
    st.session_state[draft_key]=""
phrases=["I need water","I need food","Please help me","I feel unwell","I need the toilet","Thank you"] if resident else ["I am coming","How can I help?","Please wait","I understand"]
for i,phrase in enumerate(phrases):
    if i%2==0:
        cols=st.columns(2)
    if cols[i%2].button(phrase,use_container_width=True):
        st.session_state[draft_key]=phrase
body=st.text_area("Message — type or dictate with Wispr Flow",key=draft_key,max_chars=700)
recording=st.audio_input("Record your original voice",key="record_"+rid+"_"+str(st.session_state.get("record_version_"+rid,0)))
if recording:
    st.caption("Review your recording before sending. You can add text using Wispr Flow.")
if recording and not body.strip():
    st.info("For translation, add a transcript using Wispr Flow or type the message. You can also send original audio alone.")
if st.button("Send message",type="primary",use_container_width=True) and (body.strip() or recording):
    audio=recording.getvalue() if recording else None
    if audio and len(audio)>8*1024*1024:
        st.error("Recording too large. Please record a shorter message.")
        st.stop()
    with db() as con:
        con.execute("INSERT INTO messages (rid,sender,body,audio) VALUES (?,?,?,?)",(rid,sender,body.strip(),audio))
    st.session_state["record_version_"+rid]=st.session_state.get("record_version_"+rid,0)+1
    st.session_state["clear_draft_"+rid]=True
    st.rerun()
inbox_status()
st.button("Refresh conversation",use_container_width=True)
conversation()
st.caption("Original voice recordings are shared within this private conversation. Use demonstration data only.")
st.caption("Browser speech playback depends on device support. Automatic text translation uses an external experimental service. Audio-only messages require a Wispr transcript for translation. Local SQLite data may be lost on cloud restarts.")
