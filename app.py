import streamlit as st
import fitz  # PyMuPDF
from docx import Document
from transformers import pipeline
import pyttsx3
import os

# AI Summarizer
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Extract Text from PDF
def extract_text_from_pdf(file_path):
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    return text

# Extract Text from DOCX
def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return '\n'.join([p.text for p in doc.paragraphs])

# Summarize with chunking and error handling
def summarize(text):
    max_chunk = 1000  # max tokens per chunk (adjust if needed)
    text_chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
    summaries = []
    for chunk in text_chunks:
        try:
            summary = summarizer(chunk, max_length=150, min_length=40, do_sample=False)
            if summary and 'summary_text' in summary[0]:
                summaries.append(summary[0]['summary_text'])
            else:
                summaries.append("Summary could not be generated for this chunk.")
        except Exception as e:
            summaries.append(f"Error during summarization: {e}")
    full_summary = ' '.join(summaries).strip()
    if not full_summary:
        full_summary = "Summary not available."
    return full_summary

# Estimate Study Time
def estimate_time(text):
    words = len(text.split())
    return round(words / 200)  # 200 words per minute

# Generate Voice Notes
def generate_voice(text):
    engine = pyttsx3.init()
    filename = "voice_note.mp3"
    engine.save_to_file(text, filename)
    engine.runAndWait()
    return filename

# Generate Flashcards
def generate_flashcards(text):
    cards = []
    for line in text.split('.'):
        if ' is ' in line:
            q, a = line.split(' is ', 1)
            cards.append((f"What is {q.strip()}?", a.strip()))
    return cards

# Streamlit UI
st.title("📚 AI-Powered Study Assistant")

uploaded = st.file_uploader("Upload your study file (PDF or DOCX)", type=["pdf", "docx"])

if uploaded:
    file_path = f"uploaded_file.{uploaded.name.split('.')[-1]}"
    with open(file_path, "wb") as f:
        f.write(uploaded.read())

    if uploaded.name.endswith(".pdf"):
        raw_text = extract_text_from_pdf(file_path)
    else:
        raw_text = extract_text_from_docx(file_path)

    st.subheader("📃 Extracted Text")
    st.write(raw_text[:500] + "...")

    st.subheader("🧠 Summary")
    summary = summarize(raw_text)
    if summary and summary != "Summary not available.":
        st.success(summary)
    else:
        st.warning("Summary could not be generated. Please try a shorter document or check your internet connection.")

    st.subheader("⏱️ Estimated Study Time")
    time_needed = estimate_time(summary)
    st.info(f"About {time_needed} minute(s) to study")

    st.subheader("🔊 Voice Note")
    voice_file = generate_voice(summary)
    st.audio(voice_file)

    st.subheader("🧠 Smart Flashcards")
    flashcards = generate_flashcards(summary)
    if flashcards:
        for q, a in flashcards[:5]:
            st.markdown(f"**Q:** {q}")
            st.markdown(f"**A:** {a}")
    else:
        st.info("No flashcards could be generated from the summary.")
