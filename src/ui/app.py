import streamlit as st
import requests
import os
import json

# Configuration
API_URL = os.getenv("API_URL", "http://app:8000")
STREAM_ENDPOINT = f"{API_URL}/api/v1/query/stream"
HEALTH_ENDPOINT = f"{API_URL}/api/v1/health"

def distance_to_similarity(distance: float) -> float:
    """
    Convert ChromaDB Cosine distance to similarity score (0-1).
    For 'cosine' space, ChromaDB returns distance = 1 - cosine_similarity.
    similarity = 1 - distance.
    """
    if distance is None:
        return 0.0
    return max(0.0, 1.0 - distance)

st.set_page_config(
    page_title="RAG Lex - Polski System Prawny",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ RAG Lex - Inteligentny Asystent Prawny")
st.markdown("Zadaj pytanie dotyczące polskich ustaw z 2020 roku.")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
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
        health = requests.get(HEALTH_ENDPOINT, timeout=2)
        if health.status_code == 200:
            st.success("✅ Połączono z API")
        else:
            st.error("⚠️ API zwróciło błąd")
    except:
        st.error("❌ Brak połączenia z API")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        if msg.get("sources"):
            with st.expander("Zobacz źródła"):
                    for source in msg["sources"]:
                        score_val = source.get('score', 0)
                        similarity = distance_to_similarity(score_val)
                        
                        citation_text = source['citation']
                        if source.get('url'):
                            st.markdown(f"🔗 **[{citation_text}]({source['url']})** (Similarity: {similarity:.0%})")
                        else:
                            st.markdown(f"**{citation_text}** (Similarity: {similarity:.0%})")
                            
                        st.text(source['text'][:500] + "...")
                    st.divider()

# Chat input
if prompt := st.chat_input("O co chcesz zapytać?"):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt, "sources": None})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Stream AI response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        sources = []
        
        try:
            payload = {"query": prompt, "top_k": top_k}
            
            with requests.post(STREAM_ENDPOINT, json=payload, stream=True, timeout=300) as response:
                if response.status_code == 200:
                    for line in response.iter_lines(decode_unicode=True):
                        if line and line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])  # Remove "data: " prefix
                                
                                if data.get("error"):
                                    st.error(f"❌ {data['error']}")
                                    break
                                
                                if data.get("token"):
                                    full_response += data["token"]
                                    placeholder.markdown(full_response + "▌")
                                
                                if data.get("done"):
                                    sources = data.get("sources", [])
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                    
                    # Final display without cursor
                    placeholder.markdown(full_response)
                    
                    # Display sources
                    if sources:
                        with st.expander("Zobacz źródła"):
                            for source in sources:
                                score_val = source.get('score', 0)
                                similarity = distance_to_similarity(score_val)
                                
                                # Add clickable link if available
                                citation_text = source['citation']
                                if source.get('url'):
                                    st.markdown(f"🔗 **[{citation_text}]({source['url']})** (Similarity: {similarity:.0%})")
                                else:
                                    st.markdown(f"**{citation_text}** (Similarity: {similarity:.0%})")
                                    
                                st.text(source['text'][:500] + "...")
                                st.divider()
                    
                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "sources": sources
                    })
                else:
                    st.error(f"❌ Błąd API ({response.status_code})")
                    
        except Exception as e:
            st.error(f"❌ Błąd: {str(e)}")
