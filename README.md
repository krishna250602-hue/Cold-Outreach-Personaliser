# Cold Outreach Personaliser

> “Paste a profile, get an email that does not sound AI-generated.”

Cold Outreach Personaliser is a production-quality, beginner-friendly AI-powered web application built using Python, Streamlit, Groq API, and python-dotenv. It generates highly personalized, natural-sounding cold outreach emails and follow-ups based on prospect profiles, while strictly avoiding typical AI-generated clichés and excessive flattery.

---

## Features

- **Single Prospect Personalisation**: Quick generation of natural opening lines, custom bodies, and contextual follow-ups by pasting a single profile.
- **Batch CSV Generation**: Upload a CSV of prospects, automatically compile custom profiles if individual fields (like company, role, website) are provided, process sequentially, and add new outreach columns.
- **Customisable Tone**: Choose from `Professional`, `Friendly`, `Casual`, `Confident`, `Concise`, or `Consultative`.
- **Targeted Outreach Goals**: Align the generated email with specific objectives like `Book a meeting`, `Introduce a product`, `Offer a service`, `Start a conversation`, `Partnership`, or `Networking`.
- **Optional Sender Details**: Expandable field to inject your specific product, role, and website dynamically—without making the AI hallucinate if left empty.
- **Copy-Ready Output**: Unified text-area containing subject line, email body, and follow-up separator for easy copying.
- **Robust Parsing & Fallbacks**: Smart parser dynamically processes model output, gracefully handles irregularities, and provides realistic fallbacks.
- **Error Resilient Batching**: Row-level try-catch block prevents one API error from interrupting your entire file export.

---

## Installation

Follow these steps to set up the application on your local machine:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd cold-outreach-personaliser
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment:**
   - **Windows:**
     ```bash
     .venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```

4. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Environment Setup

1. Create a `.env` file in the root of the project directory (based on `.env.example`):
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=llama-3.3-70b-versatile
   ```
   
   *Note: Never commit your `.env` file containing actual keys to public version control.*

---

## Running the Application

To run the Streamlit interface, execute:

```bash
streamlit run app.py
```

The application will automatically launch and open in your default web browser (typically at `http://localhost:8501`).
