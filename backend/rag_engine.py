import os
import re
import google.generativeai as genai
import PIL.Image # Assurez-vous d'avoir installé 'Pillow'
from typing import List
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    print("Successfully imported ChatGoogleGenerativeAI")
except ImportError as e:
    print(f"ImportError for langchain_google_genai: {e}")
    ChatGoogleGenerativeAI = None

# Initialize global variables for RAG components
vectorstore = None
retriever = None
chain = None
llm = None

# Read secrets from environment instead of hardcoding them in source.
HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN", "").strip()
if HF_TOKEN:
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = HF_TOKEN

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

class SimpleTextSplitter:
    """
    A simple text splitter to avoid importing langchain_text_splitters
    which triggers a Spacy/Pydantic error on Python 3.14.
    Improved to respect Markdown sections (---).
    """
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, documents: List[Document]) -> List[Document]:
        splits = []
        for doc in documents:
            text = doc.page_content
            # Robust splitting by Markdown separator "---" using regex
            sections = re.split(r'\n-{3,}\n', text)
            
            # Fallback for simple "---" if regex fails
            if len(sections) < 2:
                 sections = text.split("---")

            for section in sections:
                section = section.strip()
                # Skip empty sections or very short ones
                if len(section) < 50: 
                    continue
                splits.append(Document(page_content=section, metadata=doc.metadata))
        return splits

class HuggingFaceConversationalWrapper(HuggingFaceEndpoint):
    """
    Wrapper to use 'conversational' models (chat-based) like text-generation models.
    Simply passes the prompt directly.
    """
    def invoke(self, input: str, config=None, **kwargs):
        return super().invoke(input, config=config, **kwargs)


def _is_cnie_renewal_question(question: str) -> bool:
    q = question.lower()
    renewal_words = ["renouvel", "expire", "expir", "تجديد", "سالات"]
    card_words = ["carte", "cin", "cnie", "la carte", "لاكارط", "البطاقة"]
    return any(w in q for w in renewal_words) and any(w in q for w in card_words)


def analyze_document_with_ai(image_file, user_context=""):
    """
    Analyse un document administratif via Gemini Vision.
    """
    # 1. Configurer la clé API pour la vision
    api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    
    # 2. Ouvrir l'image envoyée par l'utilisateur
    img = PIL.Image.open(image_file)
    
    # 3. DÉFINIR LE MODÈLE (C'est la ligne qui vous manquait !)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 4. Prompt d'analyse court (meme concept: 4 points FR + darija)
    prompt = f"""
    Tu es expert de l'administration marocaine. Analyse ce document.

    Contexte utilisateur: {user_context}

    Regles strictes:
    - Pas d'introduction, pas de conclusion.
    - Donne uniquement 4 points: Statut, Manque, Risque, A faire.
    - Chaque point en francais: 1 phrase courte (max 18 mots).
    - Juste en dessous, meme idee en darija: 1 phrase courte (max 18 mots).
    - Si aucun manque: "Rien". Si aucun risque: "Aucun".
    - Reponse totale <= 10 lignes.

    Format exact:
    1. Statut: ...
       الحالة: ...
    2. Manque: ...
       النواقص: ...
    3. Risque: ...
       الخطر: ...
    4. A faire: ...
       شنو خاص يدير: ...
    """
    
    # 5. Générer la réponse en analysant l'image et le texte
    response = model.generate_content([prompt, img])
    
    return response.text


def _is_mostly_french(text: str) -> bool:
    latin_chars = len(re.findall(r"[a-zA-Z]", text))
    arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
    return latin_chars > arabic_chars

def _french_cnie_answer() -> str:
    return (
        "Pour renouveler votre Carte Nationale (CNIE), voici les étapes :\n\n"
        "1) Documents nécessaires :\n"
        "- L'ancienne carte\n"
        "- 2 nouvelles photos d'identité\n"
        "- Le formulaire rempli (imprimé)\n"
        "- Certificat de résidence si vous avez changé d'adresse\n\n"
        "2) Déposez le dossier au commissariat ou au centre d'enregistrement le plus proche.\n"
        "3) Suivez votre demande jusqu'à ce que la nouvelle carte soit prête."
    )

def _darija_cnie_answer() -> str:
    return (
        "بالنسبة لتجديد لاكارط ناسيونال (CNIE)، هادي هي الخطوات:\n\n"
        "1) وجد الوراق:\n"
        "- لاكارط القديمة\n"
        "- جوج تصاور جداد ديال لاكارط\n"
        "- الاستمارة معمرة\n"
        "- شهادة السكنى إلا بدلتي العنوان\n\n"
        "2) دّي الملف للمقاطعة ولا الكوميسارية التابعة لبلاصتك.\n"
        "3) تبع الطلب ديالك حتى تخرج لاكارط الجديدة.\n\n"
        "إلى بغيتي، نقدر نعطيك لائحة الوراق بصيغة مختصرة باش تمشي واجد."
    )


def _fallback_answer(question: str) -> str:
    if _is_cnie_renewal_question(question):
        if _is_mostly_french(question):
            return _french_cnie_answer()
        return _darija_cnie_answer()

    # Fallback to Smart Search (Retrieval only) when LLM fails
    if retriever is not None:
        try:
             # Search for documents using the retriever
             # Keep top 2 documents max for fallback to avoid noise
             if hasattr(retriever, "vectorstore"):
                 docs = retriever.vectorstore.similarity_search(question, k=2)
             elif hasattr(retriever, "invoke"):
                 # if not vectorstore found (rare), rely on invoke but slice it
                 docs = retriever.invoke(question)[:2]
             else:
                 docs = retriever.get_relevant_documents(question)[:2]
                 
             if docs:
                 combined_text = "\n---\n".join([doc.page_content for doc in docs])
                 
                 if _is_mostly_french(question):
                     return (
                         "Désolé, je rencontre un problème technique avec l'IA. "
                         "Cependant, voici les informations trouvées dans les documents :\n\n"
                         + combined_text[:1500] 
                         + ("..." if len(combined_text) > 1500 else "")
                     )
                 
                 return (
                     "سمح ليا، كاين مشكل فالاتصال مع الذكاء الاصطناعي (Service Unavailable). "
                     "ولكن ها هي المعلومات اللي لقيت فالوثائق:\n\n" 
                     + combined_text[:1500] 
                     + ("..." if len(combined_text) > 1500 else "")
                 )
        except Exception as e:
             print(f"Fallback retrieval failed: {e}")

    if _is_mostly_french(question):
        return (
            "Désolé, une erreur technique est survenue lors de la génération de la réponse. "
            "Veuillez reformuler votre question brièvement, et je vous répondrai par écrit."
        )

    return (
        "سمح ليا، وقع مشكل تقني فالتوليد ديال الجواب. "
        "عاود كتب السؤال بطريقة قصيرة، وغادي نجاوبك بالدارجة وبالخطوات."
    )

def initialize_rag_system(files: List[str]):
    """
    Initializes the RAG system by loading documents, creating embeddings,
    and setting up the retrieval chain with a cloud LLM.
    """
    global vectorstore, retriever, chain, llm
    
    all_documents = []
    
    # Load all markdown files
    for file_path in files:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            all_documents.append(Document(page_content=text, metadata={"source": file_path}))
        else:
            print(f"Warning: File not found: {file_path}")

    if not all_documents:
        # Create a dummy document if no files are found to prevent crash during testing
        print("Warning: No documents found. Using dummy data for initialization.")
        all_documents.append(Document(page_content="Khadamat AI est un assistant administratif.", metadata={"source": "dummy"}))

    # Split documents into chunks
    text_splitter = SimpleTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(all_documents)

    # Create embeddings and vector store
    print("Loading local embeddings (multilingual)... This might take a moment.")
    try:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        vectorstore = FAISS.from_documents(splits, embeddings)
        # Increased k to 5 to better catch relevant documents, but we will filter later for retrieval
        # For retrieval, we want more candidates, but for fallback display we want fewer.
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    except Exception as e:
        print(f"Failed to init vectorstore: {e}")
        retriever = None

    # Initialize LLM
    # Try Google Gemini if API Key is available
    if ChatGoogleGenerativeAI and os.environ.get("GOOGLE_API_KEY"):
         print(f"Initializing Google Gemini (Key starts with {os.environ.get('GOOGLE_API_KEY')[:5]})...")
         # Updated candidates list based on 2026 available models
         gemini_candidates = [
             "gemini-2.5-flash", 
             "gemini-2.0-flash", 
             "gemini-2.0-flash-lite", 
             "gemini-flash-latest", 
             "gemini-pro-latest"
         ]
         
         for model_name in gemini_candidates:
             try:
                 print(f"Attempting to use model: {model_name}")
                 llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.3, max_retries=2)
                 # Test invocation to ensure it works
                 llm.invoke("Hi") 
                 print(f"Gemini {model_name} initialized and tested successfully.")
                 break # connection successful
             except Exception as e:
                 print(f"Failed to init Gemini {model_name}: {e}")
                 llm = None
                 
    # Fallback to Hugging Face if Gemini not available or failed
    
    # Fallback to Hugging Face if Gemini not available or failed
    if llm is None:
        repo_id = "google/flan-t5-large"
        print(f"Initializing Cloud LLM ({repo_id})...")
        try:
            llm = HuggingFaceEndpoint(
                repo_id=repo_id,
                task="text2text-generation",
                max_new_tokens=512,
                temperature=0.3,
                huggingfacehub_api_token=HF_TOKEN
            )
        except Exception as e:
            print(f"Warning: LLM init failed, fallback mode enabled: {e}")
            llm = None

    # Define Prompt Template
    # Detect if LLM is Gemini (Chat model) or Flan-T5 (Completion model)
    is_chat_model = "ChatGoogleGenerativeAI" in str(type(llm)) if llm else False

    template = """Answer the question based on the context below.
    If the question is in French, answer in French.
    If the question is in Darija or Arabic, answer in Moroccan Darija.
    Keep the answer simple, practical, and step-by-step.
    
    Context:
    {context}
    
    Question: 
    {question}
    
    Answer:"""
    
    prompt = PromptTemplate.from_template(template)

    def format_docs(docs):
        return "\\n\\n".join(doc.page_content for doc in docs)

    # Build the RAG chain only when both LLM and retriever are ready.
    # This avoids `None | function` when vectorstore/retriever init fails.
    if llm is not None and retriever is not None:
        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
    else:
        chain = None
        if retriever is None:
            print("Warning: Retriever unavailable, running in fallback mode.")
        if llm is None:
            print("Warning: LLM unavailable, running in fallback mode.")

    print("RAG System Initialized Successfully (Cloud AI Mode).")

def get_answer(question: str) -> str:
    """
    Retrieves the answer for a given question using the RAG chain.
    """
    if retriever is None:
        return "سمح ليا، النظام مازال ما تسطابليش مزيان."
    
    try:
        if chain is not None:
            print(f"Invoking chain with question: {question}")
            response = chain.invoke(question)
            if response and str(response).strip():
                return str(response).strip()
        return _fallback_answer(question)
    except StopIteration:
        print("Warning: StopIteration in chain.invoke, using fallback answer")
        return _fallback_answer(question)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error generating answer: {e}")
        return _fallback_answer(question)


