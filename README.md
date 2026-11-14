# CodePath Academy

A W3Schools-inspired programming tutorial application built with Streamlit. It uses an original layout and original lesson wording; it does not copy W3Schools' source code or lesson text.

## Included courses
- Python
- Java
- C
- C++
- HTML
- CSS
- JavaScript

The curriculum has 292 chapter entries organised into sections. Each chapter page is structured with a definition, why the concept is used, how it works, syntax, example, explanation and output.

**Content quality note:** Some advanced chapters are introductory scaffolds and should be reviewed and expanded before being treated as a complete reference. The core introductory lessons have more detailed, topic-specific examples. This project does not claim to reproduce the full depth of W3Schools.

## Run locally (macOS)
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Configure Gemini AI Tutor
1. Open Google AI Studio and create a Gemini API key: https://aistudio.google.com/api-keys
2. Create a file named `.streamlit/secrets.toml` in the project folder.
3. Add:
```toml
GEMINI_API_KEY = "paste-your-valid-api-key-here"
```
4. Restart Streamlit.

The app uses the `google-genai` Python SDK and defaults to `gemini-3.8-flash`. To override the model, set the `GEMINI_MODEL` environment variable.

The key is loaded from Streamlit secrets or the `GEMINI_API_KEY` environment variable. It is never displayed in the website. The `.gitignore` excludes the local secrets file.

### If the chatbot reports 401 UNAUTHENTICATED
This is an invalid or unsupported API key, not a lesson-page problem. Create a new Gemini API key in Google AI Studio, ensure you copied the complete API key (not an OAuth access token), replace the secret, and restart the app. Never share the key or commit it to GitHub.

## Deploy to Streamlit Community Cloud
1. Push this folder to a GitHub repository.
2. Create a Streamlit Community Cloud app and select `app.py`.
3. In the app's Secrets settings, add:
```toml
GEMINI_API_KEY = "your-valid-key"
```
4. Deploy or reboot the app.

Never upload `.streamlit/secrets.toml` to GitHub.

## Project structure
```text
CodePath-Academy-Clean/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
└── data/
    ├── courses/curriculum.json
    ├── lessons/lessons.json
    └── roadmaps/
```
