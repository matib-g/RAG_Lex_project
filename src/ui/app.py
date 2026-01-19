import streamlit as st
import requests
import os
import json

# Configuration
API_URL = os.getenv("API_URL", "http://app:8000")
API_ENDPOINT = f"{API_URL}/api/v1/query"

st.set_page_config(
    page_title="RAG Lex - Polski System Prawny",
    page_icon="⚖️",
    layout="wide"
)

# Custom CSS for better aesthetics
st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    .source-box {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .citation {
        font-weight: bold;
        color: #007bff;
        font-size: 0.9em;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚖️ RAG Lex - Inteligentny Asystent Prawny")
st.markdown("Zadaj pytanie dotyczące polskich ustaw z 2020 roku.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for information and settings
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Seal_of_the_Senate_of_Poland.svg/1200px-Seal_of_the_Senate_of_Poland.svg.png", width=100)
    st.header("Informacje")
    st.info("""
        System wykorzystuje technikę RAG (Retrieval-Augmented Generation), 
        aby odpowiadać na pytania w oparciu o bazę aktów prawnych Sejmu.
    """)
    
    st.divider()
    st.subheader("Ustawienia")
    top_k = st.slider("Liczba dokumentów źródłowych (top_k)", 1, 10, 5)
    
    if st.button("Wyczyść historię czatu"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    # Health check
    try:
        health = requests.get(f"{API_URL}/api/v1/health", timeout=2)
        if health.status_code == 200:
            st.success("✅ Połączono z API")
        else:
            st.error("⚠️ API zwróciło błąd")
    except:
        st.error("❌ Brak połączenia z API")

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("Zobacz źródła"):
                for source in message["sources"]:
                    st.markdown(f"""
                        <div class="source-box">
                            <div class="citation">{source['citation']} (Prawdopodobieństwo: {1 - source['score']:.2f})</div>
                            <div style="font-size: 0.85em; margin-top: 5px;">{source['text'][:500]}...</div>
                        </div>
                    """, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("O co chcesz zapytać?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call API for RAG response
    with st.chat_message("assistant"):
        with st.spinner("Przeszukuję bazę aktów prawnych i generuję odpowiedź..."):
            try:
                payload = {
                    "query": prompt,
                    "top_k": top_k
                }
                import time
                start_time = time.time()
                response = requests.post(API_ENDPOINT, json=payload, timeout=300)
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                    
                    if not answer:
                        st.warning("Model nie wygenerował żadnej treści. Możliwy problem z promptem lub modelem.")
                    else:
                        print(f"DEBUG: Received answer from API. Length: {len(answer)}")
                        st.success(f"Odpowiedź wygenerowana w {duration:.1f} sekund.")
                        st.markdown(f"### Odpowiedź:\n{answer}")
                        # Optional: st.write(answer) to bypass markdown parsing if it's the issue

                    
                    if sources:
                        with st.expander("Zobacz źródła"):
                            for source in sources:
                                score_val = source.get('score')
                                prob = (1 - score_val) if score_val is not None else 0.0
                                st.markdown(f"""
                                    <div class="source-box">
                                        <div class="citation">{source['citation']} (Prawdopodobieństwo: {prob:.2f})</div>
                                        <div style="font-size: 0.85em; margin-top: 5px;">{source['text'][:500]}...</div>
                                    </div>
                                """, unsafe_allow_html=True)
                    
                    # Store in history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer if answer else "Błąd: Brak odpowiedzi z modelu.",
                        "sources": sources
                    })
                    
                    # Force rerun to show message in history
                    st.rerun()
                else:
                    st.error(f"Błąd API ({response.status_code}): {response.text}")
            except Exception as e:
                st.error(f"Wystąpił błąd podczas komunikacji z API: {e}")


