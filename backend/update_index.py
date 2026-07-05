import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

print("Initializing Pinecone...")
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index_name = "chatbot-tax-index"
index = pc.Index(index_name)

print("Clearing existing vectors...")
try:
    index.delete(delete_all=True)
except Exception as e:
    print(f"Warning during delete: {e}")

print("Loading tax_data.md...")
md_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tax_data.md")
with open(md_path, "r", encoding="utf-8") as f:
    text = f.read()

# We use a single chunk because the document is very small (less than 2000 chars)
# and we want to keep the entire table context intact for the LLM.
doc = Document(page_content=text, metadata={"source": "tax_data.md"})

print("Embedding and uploading to Pinecone...")
embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
vectorstore = PineconeVectorStore.from_documents(
    [doc],
    embeddings,
    index_name=index_name
)

print("Index updated successfully!")
