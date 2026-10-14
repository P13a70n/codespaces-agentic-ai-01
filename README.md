# Nivara Banking Support Agent

A Streamlit demo of a single LangChain agent coordinating four banking tools:
EMI calculation, loan eligibility, synthetic account lookup, and gated loan
application submission. The demo uses Gemini and never connects to a real bank.

## Run locally

1. Create and activate a virtual environment:

	```bash
	python -m venv .venv
	source .venv/bin/activate
	```

2. Install dependencies and configure the model:

	```bash
	pip install -r requirements.txt
	```

	Add your Gemini API key to `.env` as `GEMINI_API_KEY=...`. The key is read
	locally and `.env` is ignored by Git. Never commit or share the key.

3. Start the app:

	```bash
	streamlit run app.py
	```

The demo uses a 12% annual reducing-balance interest rate and considers a loan
eligible when total monthly EMIs are no more than 40% of monthly salary. A
loan application is staged first; it is submitted only after the customer
presses **Confirm & submit**. Account and application data are synthetic and
exist only for the current app session.

Run the unit tests with `pytest`.