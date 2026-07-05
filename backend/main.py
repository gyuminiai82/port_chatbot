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
    "당신은 연말정산 및 세무 전문 AI 어시스턴트입니다.\n"
    "산출세액을 계산할 때는 제공된 문맥의 [종합소득 과세표준 및 세율 표]를 참조하여 다음 단계를 반드시 따르세요:\n"
    "1) 질문자의 과세표준 금액이 어느 구간에 정확히 속하는지 찾으세요.\n"
    "2) 해당 구간의 세율과 누진공제 계산식을 찾으세요.\n"
    "3) 차근차근 논리적으로 식에 대입하여 최종 산출세액을 계산하세요.\n"
    "답변의 가장 마지막에는 반드시 줄바꿈을 두 번 하고 '[적용 문헌]' 이라는 텍스트를 적은 뒤, 계산에 적용한 해당 구간의 내용을 마크다운 표 형식 기호(|) 없이 일반 텍스트로 깔끔하게 적어주세요. (예: 1,400만원 초과 5,000만원 이하 구간: 84만원 + 15%)\n"
    "반드시 제공된 문맥(context)을 사용하여 답변하고, 모른다면 모른다고 하세요. 절대 지어내지 마세요.\n\n"
    "문맥(Context):\n"
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
        
        full_answer = response["answer"]
        answer_text = full_answer
        sources = []
        
        if "[적용 문헌]" in full_answer:
            parts = full_answer.split("[적용 문헌]")
            answer_text = parts[0].strip()
            applied_source = parts[1].strip()
            
            # Clean up markdown table markers if the LLM still outputs them
            applied_source = applied_source.replace('|', '').replace('---', '').strip()
            
            # Use the extracted applied source for the UI
            sources.append({
                "content": applied_source,
                "metadata": {"source": "소득세법 제55조 1항 (세율)"}
            })
        else:
            # Fallback if the LLM didn't format correctly, just show the first 100 chars
            if "context" in response:
                for doc in response["context"]:
                    content = doc.page_content
                    if len(content) > 100:
                        content = content[:100] + " ... (생략)"
                    sources.append({
                        "content": content,
                        "metadata": {"source": "소득세법 제55조 1항 (세율)"}
                    })
                
        return {"response": answer_text, "sources": sources}
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
