# CodePath Academy

CodePath Academy is a W3Schools-inspired programming learning website built with Python and Streamlit. It uses its own original layout and lesson wording; it does not copy W3Schools' source code or lesson text.

## Project goal

Help beginners learn programming step by step through structured courses, clear concept explanations, syntax, examples, code explanations and outputs. The website also includes an AI programming tutor for programming questions and code explanations.

## Courses

- Python
- Java
- C
- C++
- HTML
- CSS
- JavaScript

The curriculum contains 292 chapter entries organised into sections. Lesson pages are structured around a definition, why the concept is used, how it works, syntax, an example, explanation and output.

**Content quality note:** Some advanced chapters are introductory scaffolds and should be reviewed and expanded before being treated as a complete reference. The project does not claim to reproduce the full depth of W3Schools.

## Technology stack

| Area | Technology |
|---|---|
| Programming language | Python |
| Web application | Streamlit |
| Live AI tutor | Google Gemini API using the `google-genai` SDK |
| LLM experimentation | TinyLlama 1.1B Chat |
| Fine-tuning approach | LoRA / 4-bit quantized fine-tuning experiment |
| Training dataset | Code Alpaca 20K (Hugging Face) |
| Training environment | Google Colab |
| Training GPU | NVIDIA Tesla T4 |
| Version control | Git and GitHub |
| Deployment | Streamlit Community Cloud |

## LLM fine-tuning experiment (Google Colab)

A separate model-training experiment was carried out in Google Colab:

1. Started with the pretrained `TinyLlama/TinyLlama-1.1B-Chat-v1.0` model.
2. Loaded programming instruction data from the Code Alpaca 20K dataset on Hugging Face.
3. Prepared and formatted the instruction/response examples for supervised fine-tuning.
4. Used 4-bit quantization to reduce GPU memory usage.
5. Applied LoRA (Low-Rank Adaptation) so that only a small adapter parameter set was trained instead of updating the full base model.
6. Ran the training configuration for 100 training steps (approximately 0.2 epoch in the recorded run).
7. Saved the trained LoRA adapter and tokenizer.

This was a fine-tuning experiment, not training a language model from scratch.

### Important: which model powers the deployed chatbot?

The TinyLlama fine-tuning experiment and the deployed chatbot are separate parts of the project.

- **TinyLlama + LoRA:** trained as an LLM fine-tuning experiment in Google Colab; the adapter was saved.
- **Gemini:** currently powers the live website's AI Programming Tutor through the Gemini API.

The saved TinyLlama adapter is not currently loaded by the deployed Streamlit chatbot. Do not describe the live chatbot as TinyLlama-powered unless the adapter is integrated into the application in a future update.

## Run locally (macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Configure the Gemini AI tutor

1. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/api-keys).
2. Create `.streamlit/secrets.toml` in the project folder.
3. Add your key:

```toml
GEMINI_API_KEY = "paste-your-valid-api-key-here"
```

4. Restart Streamlit.

The application uses the `google-genai` Python SDK and defaults to `gemini-3.5-flash-lite`. You can override the model by setting the `GEMINI_MODEL` environment variable or Streamlit secret.

The key is read from Streamlit secrets or the `GEMINI_API_KEY` environment variable. It is not displayed in the website. The `.gitignore` excludes the local secrets file.

**Security:** Never commit your real API key, paste it into source code, or share it publicly.

## Deploy to Streamlit Community Cloud

1. Push the project to GitHub.
2. Create an app in [Streamlit Community Cloud](https://share.streamlit.io/).
3. Select this repository, the `main` branch and `app.py` as the main file.
4. In the app's **Settings → Secrets**, add:

```toml
GEMINI_API_KEY = "your-valid-gemini-api-key"
```

5. Deploy or reboot the app.

Never upload `.streamlit/secrets.toml` to GitHub.

## Project structure

```text
CodePath-Academy/
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
