import os
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from config import Config

class RAGTool:
    def __init__(self):
        self.config = Config()
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.config.EMBEDDING_MODEL
        )
        self.llm = Ollama(
            model=self.config.LLM_MODEL,
            base_url=self.config.OLLAMA_BASE_URL
        )
        self.vectorstore = None
        self.qa_chain = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    
    def load_and_split_documents(self, pdf_path: str) -> List:
        """Load PDF and split into chunks"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
        
        splits = text_splitter.split_documents(documents)
        print(f"Split {len(documents)} documents into {len(splits)} chunks")
        
        return splits
    
    def create_vectorstore(self, documents: List):
        """Create Chroma vectorstore"""
        persist_directory = self.config.VECTOR_DB_PATH
        
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=persist_directory
        )
        
        print(f"Created vectorstore with {len(documents)} documents")
    
    def load_vectorstore(self):
        """Load existing vectorstore"""
        if os.path.exists(self.config.VECTOR_DB_PATH):
            self.vectorstore = Chroma(
                persist_directory=self.config.VECTOR_DB_PATH,
                embedding_function=self.embeddings
            )
            print("Loaded existing vectorstore")
        else:
            print("No existing vectorstore found")
    
    def setup_qa_chain(self):
        """Setup conversational retrieval chain"""
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized")
        
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )
        
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.memory,
            return_source_documents=True,
            verbose=True
        )
    
    def initialize(self, pdf_path: str = None):
        """Initialize RAG tool"""
        # Load existing vectorstore or create new one
        self.load_vectorstore()
        
        if not self.vectorstore and pdf_path:
            documents = self.load_and_split_documents(pdf_path)
            self.create_vectorstore(documents)
        
        if self.vectorstore:
            self.setup_qa_chain()
            print("RAG tool initialized successfully")
        else:
            print("Failed to initialize RAG tool - no documents available")
    
    def ask_question(self, question: str) -> Dict[str, str]:
        """Ask a question using RAG"""
        if not self.qa_chain:
            return {
                "answer": "RAG tool not initialized. Please load documents first.",
                "sources": []
            }
        
        try:
            result = self.qa_chain({
                "question": question,
                "chat_history": []
            })
            
            sources = []
            if result.get("source_documents"):
                sources = [
                    {
                        "content": doc.page_content[:200] + "...",
                        "page": doc.metadata.get("page", "Unknown")
                    }
                    for doc in result["source_documents"]
                ]
            
            return {
                "answer": result["answer"],
                "sources": sources
            }
        
        except Exception as e:
            return {
                "answer": f"Error processing question: {str(e)}",
                "sources": []
            }

if __name__ == "__main__":
    rag = RAGTool()
    pdf_path = "data/general_notes.pdf"
    
    if os.path.exists(pdf_path):
        rag.initialize(pdf_path)
        
        # Test question
        result = rag.ask_question("What is United States-Israel Free Trade?")
        print("Answer:", result["answer"])
        print("Sources:", len(result["sources"]))