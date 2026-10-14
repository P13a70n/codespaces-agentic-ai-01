"""Streamlit chat interface for the synthetic Nivara banking demo."""

import json
import os

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

from banking_agent.agent import build_agent
from banking_agent.tools import BankingState, build_tools


load_dotenv()

st.set_page_config(
    page_title="Nivara Banking Support",
    page_icon="N",
    layout="centered",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap');
    :root {
        --ink: #18231e;
        --muted: #637168;
        --paper: #f5f6f0;
        --green: #174b3a;
        --lime: #d9ef8b;
        --coral: #e8795f;
    }
    .stApp { background: var(--paper); color: var(--ink); }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 880px; padding-top: 2.2rem; }
    h1, h2, h3 { font-family: 'Newsreader', Georgia, serif !important; color: var(--ink); }
    p, label, div, button, input { font-family: 'DM Sans', sans-serif; }
    .eyebrow { color: var(--green); font-size: .74rem; font-weight: 700; letter-spacing: .12em; }
    .app-title { font-family: 'Newsreader', Georgia, serif; font-size: 2.55rem; line-height: 1.08; margin: .4rem 0 .5rem; }
    .app-subtitle { color: var(--muted); margin-bottom: 1.5rem; }
    .demo-note { background: #e9eee3; border-left: 3px solid var(--coral); padding: .7rem .9rem; border-radius: 3px; color: #435148; font-size: .88rem; }
    [data-testid="stChatMessage"] { border: 1px solid #e0e4dc; border-radius: 8px; background: rgba(255,255,255,.72); }
    [data-testid="stChatInput"] { border-color: #bbc8bd; }
    .stButton > button[kind="primary"] { background: var(--green); border-color: var(--green); }
    .stButton > button { border-radius: 5px; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "banking_state" not in st.session_state:
    st.session_state.banking_state = BankingState()
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

banking_state: BankingState = st.session_state.banking_state

st.markdown('<div class="eyebrow">NIVARA BANK · CUSTOMER DESK</div>', unsafe_allow_html=True)
st.markdown('<div class="app-title">How can we help?</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">A secure-feeling demo for everyday banking requests.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="demo-note">Demo environment · Signed in as CUST-1001 · All account data is synthetic</div>',
    unsafe_allow_html=True,
)

for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

pending = banking_state.pending_application
if pending:
    application = pending["application"]
    eligibility = pending["eligibility"]
    with st.container(border=True):
        st.subheader("Review loan application")
        st.write(
            f"₹{application['principal']:,.0f} for {application['tenure_months']} months · "
            f"EMI ₹{application['monthly_emi']:,.2f} · "
            f"{application['annual_interest_rate']:g}% annual interest"
        )
        st.caption(
            f"Eligible · total EMI is {eligibility['emi_to_income_ratio']:.1%} of monthly salary. "
            "Nothing has been submitted yet."
        )
        confirm_col, cancel_col = st.columns([1, 1])
        with confirm_col:
            confirmed = st.button(
                "Confirm & submit",
                type="primary",
                key=f"confirm-{pending['application_id']}",
                use_container_width=True,
            )
        with cancel_col:
            cancelled = st.button(
                "Cancel",
                key=f"cancel-{pending['application_id']}",
                use_container_width=True,
            )

    if confirmed:
        banking_state.confirmed_application_id = pending["application_id"]
        submission_tool = next(
            tool for tool in build_tools(banking_state)
            if tool.name == "submit_loan_application"
        )
        result = json.loads(
            submission_tool.invoke(
                {
                    **application,
                    "application_id": pending["application_id"],
                }
            )
        )
        if result["status"] == "submitted":
            st.session_state.chat_messages.append(
                {
                    "role": "assistant",
                    "content": (
                        f"**Application submitted:** {result['application_id']}\n\n"
                        f"**Monthly EMI:** ₹{application['monthly_emi']:,.2f} at "
                        f"{application['annual_interest_rate']:g}% annual interest\n\n"
                        f"**Eligibility:** Eligible; total EMIs are "
                        f"{eligibility['emi_to_income_ratio']:.1%} of monthly salary.\n\n"
                        "Your account details above are synthetic demo data."
                    ),
                }
            )
        else:
            st.error("The application could not be submitted. Please try again.")
        st.rerun()

    if cancelled:
        banking_state.pending_application = None
        banking_state.confirmed_application_id = None
        st.session_state.chat_messages.append(
            {"role": "assistant", "content": "The pending loan application was cancelled."}
        )
        st.rerun()

if not os.getenv("GEMINI_API_KEY", "").strip():
    st.info("Add GEMINI_API_KEY to your local .env file to start a conversation.")

if prompt := st.chat_input("Ask about a loan or your account"):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    try:
        agent = build_agent(banking_state)
        history = [
            HumanMessage(content=message["content"])
            if message["role"] == "user"
            else AIMessage(content=message["content"])
            for message in st.session_state.chat_messages
        ]
        result = agent.invoke({"messages": history})
        response = result["messages"][-1].content
        if not isinstance(response, str):
            response = "\n".join(
                block.get("text", str(block)) if isinstance(block, dict) else str(block)
                for block in response
            )
    except Exception as error:
        response = f"I couldn't complete that request: {error}"

    st.session_state.chat_messages.append({"role": "assistant", "content": response})
    st.rerun()