"""Gemini-backed LangChain agent setup."""

import os

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from banking_agent.tools import BankingState, build_tools


SYSTEM_PROMPT = """You are Nivara Bank's customer support assistant in a synthetic demo.
The authenticated demo customer is CUST-1001. You may use this identity for
account lookup unless the customer gives another ID. Do not claim that demo
data is real or that you accessed a live banking system.

For a loan request, use the EMI calculator and eligibility tool with the
customer's stated values. The configured annual rate is 12% unless the customer
specifies another rate. Retrieve account details when requested. Ask for any
missing value required by a tool; never invent customer financial information.
Only prepare an application when the eligibility tool says eligible. The
submission tool cannot submit until the Streamlit interface records explicit
customer confirmation. If it returns awaiting_confirmation, say the application
is prepared but not submitted. Never describe an application as submitted unless
the tool returns status submitted. Finish with a concise summary of EMI,
eligibility, account lookup, and application status when those are relevant."""


def build_agent(state: BankingState):
    """Create a single tool-calling agent bound to the current session."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add your Gemini API key to the local .env file."
        )

    model = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        google_api_key=api_key,
        temperature=0,
    )
    return create_agent(
        model=model,
        tools=build_tools(state),
        system_prompt=SYSTEM_PROMPT,
    )