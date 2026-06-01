from setuptools import setup, find_packages

setup(
    name="digital-twin-tesla",
    version="1.0.0",
    description="Digital Twin of Nikola Tesla  --  AIMS DTU Summer Project 2026",
    author="AIMS DTU",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "google-generativeai",
        "langchain",
        "langchain-google-genai",
        "langchain-community",
        "langchain-chroma",
        "sentence-transformers",
        "chromadb",
        "streamlit",
        "plotly",
        "python-dotenv",
        "requests",
        "beautifulsoup4",
        "pypdf",
        "lxml",
        "gTTS",
        "SpeechRecognition",
    ],
)
