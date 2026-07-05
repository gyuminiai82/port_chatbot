from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# RAG specific imports
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_upstage import ChatUpstage
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Load .env from the root directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)


app = FastAPI(title="Chatbot API")

class ChatRequest(BaseModel):
    message: str

# Initialize RAG components globally
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index_name = "chatbot-tax-index"

# embeddings
embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")

# vectorstore
vectorstore = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

# LLM
llm = ChatUpstage(model="solar-1-mini-chat")
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

system_prompt = (
    "당신은 연말정산 및 세무 전문 AI 어시스턴트입니다. "
    "반드시 제공된 문맥(context)을 사용하여 질문에 답변하세요. "
    "답을 모른다면 모른다고 명확히 답하고, 지어내지 마세요. "
    "친절하고 간결하게 답변해 주세요.\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        response = rag_chain.invoke({"input": request.message})
        return {"response": response["answer"]}
    except Exception as e:
        return {"response": f"오류가 발생했습니다: {str(e)}"}

# Serve Next.js frontend (static files)
# The frontend will be built to the 'frontend/out' directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "out")

if os.path.exists(FRONTEND_DIR):
    app.mount("/_next", StaticFiles(directory=os.path.join(FRONTEND_DIR, "_next")), name="_next")
    # For serving static assets like images, favicon, etc. if they exist
    # (Optional) app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    # Serve static HTML files and index.html for root
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if not full_path or full_path == "/":
            return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
        
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.exists(file_path):
            return FileResponse(file_path)
        elif os.path.exists(file_path + ".html"):
            return FileResponse(file_path + ".html")
        else:
            # Fallback for SPA routing if needed (though next export usually creates .html files)
            return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
else:
    print(f"Warning: Frontend directory {FRONTEND_DIR} not found. Build the frontend first.")
