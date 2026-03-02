import streamlit as st
import requests
from datetime import datetime

API_BASE = "http://127.0.0.1:8000"   #Base url

st.set_page_config(page_title="AI-Native Compliance Demo", layout="wide")

st.title("🧠 AI-Native Compliance Case Engine")

account_id = st.text_input("Enter Account ID", value="ACC123")

# Keep the latest case response across reruns
if "case_data" not in st.session_state:
    st.session_state.case_data = None
    
if st.button("Generate Case"):
    with st.spinner("Generating case..."):
        try:
            res = requests.get(f"{API_BASE}/ai_decision/{account_id}")

            # If the API fails, show the exact error message
            if res.status_code != 200:
                st.error(f"API Error ({res.status_code})")
                st.code(res.text)
                st.stop()

            data = res.json()

        except Exception as e:
            st.error("Request failed")
            st.code(str(e))
            st.stop()

    st.success("Case Generated")


    # -----------------------------
    # AI Decision Section
    # -----------------------------
    decision = data["ai_decision"]
    sla = data["sla"]
    case_id = data["case_id"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("AI Decision")
        st.markdown(f"**Workflow Path:** `{decision['routed_path']}`")
        st.markdown(f"**Confidence:** {decision['confidence']}")
        st.markdown("### Narrative")
        st.write(decision["narrative_summary"])

    with col2:
        st.subheader("SLA")
        st.write(f"Status: **{sla['sla_status']}**")
        if sla["sla_due_at"]:
            st.write(f"Due At: {sla['sla_due_at']}")

    st.divider()


    # -----------------------------
    # Signals
    # -----------------------------
    st.subheader("Fired Signals")
    for s in decision.get("why_this_path", []):
        st.write(f"- {s}")

    st.divider()


    # -----------------------------
    # Policy Grounding
    # -----------------------------
    st.subheader("Policy Snippets (RAG)")
    for snippet in data["policy_snippets"]:
        st.markdown(f"**{snippet['source']}#chunk_{snippet['chunk_id']}**")
        st.write(snippet["snippet"])
        st.write("---")

    st.divider()


    # -----------------------------
    # For the Analyst
    # -----------------------------
    st.subheader("Human Action")

    action = st.selectbox(
        "Select Action",
        ["APPROVE", "OVERRIDE", "REQUEST_INFO", "ESCALATE"]
    )

    reason = ""
    if st.button("Submit Action"):

    # Guardrail: OVERRIDE must have a reason
        if action == "OVERRIDE" and not reason.strip():
            st.error("OVERRIDE requires a reason.")
            st.stop()

        payload = {
        "case_id": case_id,
        "account_id": data["account_id"],
        "action": action,
        "reason": reason,
        "extra_data": {"override_to_path": "REVIEW"} if action == "OVERRIDE" else {},
        }

        r = requests.post(f"{API_BASE}/cases/actions", json=payload)

        if r.status_code != 200:
            st.error(f"API Error ({r.status_code})")
            st.code(r.text)
            st.stop()

        st.success("Action Logged")
        st.json(r.json())