import streamlit as st
import requests
import os
import json
import uuid
import datetime
import re
from dotenv import load_dotenv

load_dotenv()

CHAT_HISTORY_FILE = 'chat_history.json'
API_URL = 'https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/PartnerTrainingSandbox/jovanche_AgentDriver_Triggered_NEW'
BEARER_TOKEN = 'disabled' #'4muMThpvh2NQoJ0XTNcvyxAOn2GElcsx'

GENERATE_CHAT_TITLE_API = 'https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/PartnerTrainingSandbox/jovanche_GenerateTitle_Triggered'
GENERATE_CHAT_TITLE_API_BEARER_TOKEN = 'P7Tw6mHdZmDVP9JK8IxoPqwJ7duVgXYF'

def parse_email_template_ordered(response: str):
    """
    Parses the response and returns a list of segments preserving the order.
    Each segment is a dict with a "type" key:
      - type "text": a plain text segment
      - type "email_template": a segment representing the email template block.
    
    If no email template is found, a single text segment is returned.
    """
    pattern = r'<EMAIL_TEMPLATE>(.*?)</EMAIL_TEMPLATE>'
    match = re.search(pattern, response, re.DOTALL)
    
    if not match:
        return [{"type": "text", "content": response.strip()}]
    
    segments = []
    text_before = response[:match.start()].strip()
    if text_before:
        segments.append({"type": "text", "content": text_before})
    
    template_content = match.group(1)
    subject_match = re.search(r'<SUBJECT>(.*?)</SUBJECT>', template_content, re.DOTALL)
    recipient_match = re.search(r'<RECIPIENT>(.*?)</RECIPIENT>', template_content, re.DOTALL)
    body_match = re.search(r'<BODY>(.*?)</BODY>', template_content, re.DOTALL)
    if subject_match and recipient_match and body_match:
        email_template = {
            "subject": subject_match.group(1).strip(),
            "recipient": recipient_match.group(1).strip(),
            "body": body_match.group(1).strip()
        }
        segments.append({"type": "email_template", "template": email_template})
    else:
        segments.append({"type": "text", "content": match.group(0).strip()})
    
    text_after = response[match.end():].strip()
    if text_after:
        segments.append({"type": "text", "content": text_after})
    
    return segments

def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, 'r') as file:
            sessions = json.load(file)
            for session in sessions:
                session.setdefault("session_id", str(uuid.uuid4()))
                session.setdefault("messages", [])
                session.setdefault("created_at", datetime.datetime.now().isoformat())
                session.setdefault("status", "complete")
                session.setdefault("title", "")
            return sorted(sessions, key=lambda x: x["created_at"], reverse=True)
    return []

def save_chat_history(sessions):
    with open(CHAT_HISTORY_FILE, 'w') as file:
        json.dump(sessions, file)

st.set_page_config(page_title="Neura - JIRA Vulnerability AI Agent", layout="wide", page_icon=":material/neurology:")
#st.title(":material/neurology: Neura - JIRA Vulnerability AI Agent")
st.title(":material/neurology: Neura - JIRA Vulnerability AI Agent (Disabled)")

# Initialize state
if "sessions" not in st.session_state:
    st.session_state.sessions = load_chat_history()
    st.session_state.current_session_id = None
    if st.session_state.sessions:
        st.session_state.current_session_id = st.session_state.sessions[0]["session_id"]

# Check processing status (if any session is processing)
is_processing = any(session.get("status") == "processing" for session in st.session_state.sessions)

# ------------------ Sidebar ------------------
with st.sidebar:
    st.logo('Logocombo_SnapLogic_RGB.png', size="large")

    # Button to start a new chat
    if st.button("New chat", disabled=is_processing, icon=":material/chat_add_on:"):
        new_id = str(uuid.uuid4())
        new_session = {
            "session_id": new_id,
            "messages": [],
            "created_at": datetime.datetime.now().isoformat(),
            "status": "complete",  # New chat starts complete (no prompt yet)
            "title": ""
        }
        st.session_state.sessions.insert(0, new_session)
        st.session_state.current_session_id = new_id
        save_chat_history(st.session_state.sessions)
        st.rerun()

    st.header("Chat history")
    st.write("---")

    if st.session_state.sessions:
        st.subheader("Your chats")
        # Iterate through recent chats (limit to 20)
        for index, session in enumerate(st.session_state.sessions[:20]):
            session_id = session["session_id"]
            is_current = session_id == st.session_state.current_session_id

            col1, col2 = st.columns([4, 1])
            with col1:
                btn_type = "primary" if is_current else "secondary"
                # Use the stored title if available, otherwise default to "New chat"
                label = session.get("title") or "New chat"
                if st.button(
                    label,
                    key=f"chat_{session_id}",
                    type=btn_type,
                    help="Switch to this chat",
                    use_container_width=True,
                    disabled=is_processing
                ):
                    st.session_state.current_session_id = session_id
                    st.rerun()

            with col2:
                if st.button(
                    "",
                    key=f"delete_{session_id}",
                    type="secondary",
                    disabled=is_processing,
                    icon=":material/delete:"
                ):
                    del st.session_state.sessions[index]
                    if session_id == st.session_state.current_session_id:
                        st.session_state.current_session_id = (
                            st.session_state.sessions[0]["session_id"]
                            if st.session_state.sessions else None
                        )
                    save_chat_history(st.session_state.sessions)
                    st.rerun()
    else:
        st.caption("No chats yet...")

# ------------------ Main Chat Display ------------------
current_session = next(
    (s for s in st.session_state.sessions 
     if s["session_id"] == st.session_state.current_session_id),
    None
)

if current_session:
    # Find the index of the last assistant message.
    last_assistant_idx = None
    for i, msg in enumerate(reversed(current_session["messages"])):
        if msg["role"] == "assistant":
            last_assistant_idx = len(current_session["messages"]) - 1 - i
            break

    # Display messages.
    for i, message in enumerate(current_session["messages"]):
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                if "segments" not in message and "<EMAIL_TEMPLATE>" in message["content"]:
                    segments = parse_email_template_ordered(message["content"])
                else:
                    segments = message.get("segments", [{"type": "text", "content": message["content"]}])
                
                for j, segment in enumerate(segments):
                    if segment["type"] == "text":
                        st.markdown(segment["content"])
                    elif segment["type"] == "email_template":
                        is_last_assistant = (i == last_assistant_idx)
                        edit_disabled = not is_last_assistant
                        with st.expander("Email Template", icon=":material/email:"):
                            edited_subject = st.text_input(
                                "Subject", 
                                value=segment["template"]["subject"],
                                disabled=edit_disabled,
                                key=f"subject_{current_session['session_id']}_{i}_{j}"
                            )
                            edited_recipient = st.text_input(
                                "Recipient", 
                                value=segment["template"]["recipient"],
                                disabled=edit_disabled,
                                key=f"recipient_{current_session['session_id']}_{i}_{j}"
                            )
                            edited_body = st.text_area(
                                "Body", 
                                value=segment["template"]["body"],
                                height=300,
                                disabled=edit_disabled,
                                key=f"body_{current_session['session_id']}_{i}_{j}"
                            )
                            
                            if is_last_assistant:
                                col1, col2 = st.columns(2)
                                if col1.button(":heavy_check_mark: Approve & Send", key=f"approve_{current_session['session_id']}_{i}_{j}", use_container_width=True):
                                    approved_email = {
                                        "subject": edited_subject,
                                        "recipient": edited_recipient,
                                        "body": edited_body,
                                    }
                                    approved_email_text = (
                                        "I approve the email to be sent.\n\n"
                                        f"Subject: {approved_email['subject']}\n"
                                        f"Recipient: {approved_email['recipient']}\n"
                                        f"Body:\n{approved_email['body']}"
                                    )
                                    current_session["messages"].append({
                                        "role": "user", 
                                        "content": approved_email_text,
                                        "approved_email": approved_email
                                    })
                                    current_session["status"] = "processing"
                                    save_chat_history(st.session_state.sessions)
                                    st.rerun()
                                if col2.button(":lock: Security Check", key=f"security_{current_session['session_id']}_{i}_{j}", use_container_width=True):
                                    current_session["messages"].append({
                                        "role": "user",
                                        "content": "Check if there is any security-sensitive information on the email."
                                    })
                                    current_session["status"] = "processing"
                                    save_chat_history(st.session_state.sessions)
                                    st.rerun()
            elif message["role"] == "user":
                if "approved_email" in message:
                    st.markdown(message["content"])
                    with st.expander("Approved email", icon=":material/forward_to_inbox:"):
                        approved_email = message["approved_email"]
                        st.text_input(
                            "Subject", 
                            value=approved_email["subject"],
                            disabled=True,
                            key=f"subject_{current_session['session_id']}_{i}"
                        )
                        st.text_input(
                            "Recipient", 
                            value=approved_email["recipient"],
                            disabled=True,
                            key=f"recipient_{current_session['session_id']}_{i+1}"
                        )
                        st.text_area(
                            "Body", 
                            value=approved_email["body"],
                            height=300,
                            disabled=True,
                            key=f"body_{current_session['session_id']}_{i+1}"
                        )
                else:
                    st.markdown(message["content"])
    
    # ----- Editable Last User Prompt on Historical Conversations -----
    # Look for the last user message (ignoring approved emails) that is followed by an assistant message.
    last_user_idx = None
    for idx in range(len(current_session["messages"]) - 2, -1, -1):
        msg = current_session["messages"][idx]
        if msg["role"] == "user":
            # Ensure there is at least one assistant response after this message.
            if any(m["role"] == "assistant" for m in current_session["messages"][idx+1:]):
                last_user_idx = idx
                break
    if last_user_idx is not None and not is_processing:
        with st.expander("Edit your last prompt", expanded=False, icon=":material/edit:"):
            edited_prompt = st.text_area("", value=current_session["messages"][last_user_idx]["content"], key=f"edit_last_prompt_{current_session['session_id']}", disabled=is_processing)
            # A send icon button (using an emoji) to update the prompt.
            if st.button("Resend", disabled=is_processing, key=f"update_prompt_{current_session['session_id']}", icon=":material/send:"):
                # Remove all messages after the last user prompt (i.e. remove the assistant response(s))
                current_session["messages"] = current_session["messages"][:last_user_idx+1]
                # Update the user prompt.
                current_session["messages"][last_user_idx]["content"] = edited_prompt
                # Set status to processing so that a new assistant response is generated.
                current_session["status"] = "processing"
                save_chat_history(st.session_state.sessions)
                st.rerun()
    
    # If the last message is from the user and status is processing, show a "Thinking..." indicator.
    if current_session["messages"] and current_session["messages"][-1]["role"] == "user" and current_session.get("status") == "processing":
        with st.chat_message("assistant"):
            st.status("Thinking...", state="running")

# ------------------ Chat Input ------------------
prompt = st.chat_input(
    "Type to start new chat..." if not current_session else "Ask anything",
    disabled=is_processing
)

if prompt and len(prompt) > 0 and not is_processing:
    if not current_session:
        new_id = str(uuid.uuid4())
        current_session = {
            "session_id": new_id,
            "messages": [],
            "created_at": datetime.datetime.now().isoformat(),
            "status": "complete",
            "title": ""
        }
        st.session_state.sessions.insert(0, current_session)
        st.session_state.current_session_id = new_id
    
    st.chat_message("user").markdown(prompt)
    current_session["messages"].append({"role": "user", "content": prompt})
    current_session["status"] = "processing"
    save_chat_history(st.session_state.sessions)
    st.rerun()

# ------------------ API Processing ------------------
# ------------------ API Processing ------------------

if st.session_state.sessions:
    for session in st.session_state.sessions:
        if session["status"] == "processing":
            # --- First, if no title is set, generate a title using the first user prompt ---
            if not session.get("title"):
                first_user_prompt = next((m["content"] for m in session["messages"] if m["role"] == "user"), "")
                if first_user_prompt:
                    data_title = [{"prompt": first_user_prompt}]
                    headers_title = {'Authorization': f'Bearer {GENERATE_CHAT_TITLE_API_BEARER_TOKEN}'}
                    try:
                        response_title = requests.post(
                            url=GENERATE_CHAT_TITLE_API,
                            json=data_title,
                            headers=headers_title,
                            timeout=180,
                            verify=False
                        )
                        response_title.raise_for_status()
                        result_title = response_title.json()
                        generated_title = result_title.get('response', "New chat")
                    except Exception as e:
                        generated_title = "New chat"
                        st.error(f"Error generating chat title: {e}")
                    session["title"] = f"{'New chat' if generated_title == 'New chat' else generated_title[:15] + '...'}"
                    save_chat_history(st.session_state.sessions)
                    # Do not call st.rerun() here.
            
            # --- Now call the conversation API ---
            try:
                messages_data = [
                    {"sl_role": msg["role"], "content": msg["content"]} 
                    for msg in session["messages"]
                ]
                prompt_text = next((m["content"] for m in reversed(session["messages"]) if m["role"] == "user"), "")
                data = [{
                    "session_id": session["session_id"],
                    "prompt": prompt_text,
                    "messages": messages_data
                }]

                headers = {'Authorization': f'Bearer {BEARER_TOKEN}'}
                response = requests.post(
                    url=API_URL,
                    json=data,
                    headers=headers,
                    timeout=1000,
                    verify=False
                )
                response.raise_for_status()
                result = response.json()
                api_response = result.get('response', "Error: Unexpected response format")
                
                segments = parse_email_template_ordered(api_response)
                assistant_message = {
                    "role": "assistant", 
                    "content": api_response,
                    "segments": segments
                }
                
                session["messages"].append(assistant_message)
                session["status"] = "complete"
                save_chat_history(st.session_state.sessions)
                st.rerun()
                break
            except Exception as e:
                session["messages"].append({
                    "role": "assistant", 
                    "content": f"Error: {str(e)}"
                })
                session["status"] = "error"
                save_chat_history(st.session_state.sessions)
                st.rerun()
