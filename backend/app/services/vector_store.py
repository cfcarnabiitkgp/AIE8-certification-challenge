"""Vector store service using Qdrant."""
import uuid
import logging
from typing import List, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import settings
from app.models.schemas import DocType

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vector embeddings and retrieval."""
    
    def __init__(self):
        """Initialize the vector store service."""
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key if settings.qdrant_api_key else None
        )
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key
        )
        self.collection_name = settings.qdrant_collection_name
        self._ensure_collection()
    
    def _ensure_collection(self) -> None:
        """Ensure the collection exists, create if not."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                logger.info("Creating collection: %s", self.collection_name)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI text-embedding-3-small dimension
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            logger.error("Error ensuring collection: %s", e)
            raise
    
    async def add_documents(
        self, 
        texts: List[str], 
        metadatas: Optional[List[dict]] = None
    ) -> int:
        """
        Add documents to the vector store.
        
        Args:
            texts: List of text chunks to add
            metadatas: Optional metadata for each chunk
            
        Returns:
            Number of documents added
        """
        if not texts:
            return 0
        
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        try:
            # Generate embeddings
            embeddings = self.embeddings.embed_documents(texts)
            
            # Create points
            points = []
            for text, embedding, metadata in zip(texts, embeddings, metadatas):
                point_id = str(uuid.uuid4())
                payload = {
                    "text": text,
                    **metadata
                }
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                )
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info("Added %d documents to vector store", len(points))
            return len(points)
        
        except Exception as e:
            logger.error("Error adding documents: %s", e)
            raise
    
    def create_doc_type_filter(self, doc_type: Union[DocType, str]) -> Filter:
        """
        Create a Qdrant filter for document type.

        Args:
            doc_type: DocType enum or string value

        Returns:
            Qdrant Filter object
        """
        doc_type_value = doc_type.value if isinstance(doc_type, DocType) else doc_type
        return Filter(
            must=[
                FieldCondition(
                    key="doc_type",
                    match=MatchValue(value=doc_type_value)
                )
            ]
        )

    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[dict] = None,
        doc_type: Optional[Union[DocType, str]] = None
    ) -> List[dict]:
        """
        Perform similarity search.

        Args:
            query: Query text
            k: Number of results to return
            filter_dict: Optional filter conditions (legacy support)
            doc_type: Optional DocType enum to filter by document type

        Returns:
            List of search results with text and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)

            # Build filter
            query_filter = None
            if doc_type is not None:
                query_filter = self.create_doc_type_filter(doc_type)
            elif filter_dict is not None:
                query_filter = filter_dict

            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=k,
                query_filter=query_filter
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "text": result.payload.get("text", ""),
                    "score": result.score,
                    "metadata": {k: v for k, v in result.payload.items() if k != "text"}
                })

            return formatted_results

        except Exception as e:
            logger.error("Error in similarity search: %s", e)
            return []
    
    async def process_pdf(self, pdf_path: str, metadata: Optional[dict] = None) -> int:
        """
        Process a PDF file and add it to the vector store using PyMuPDF.

        Args:
            pdf_path: Path to the PDF file
            metadata: Optional metadata to attach to chunks

        Returns:
            Number of chunks indexed
        """
        try:
            from langchain_community.document_loaders import PyMuPDFLoader

            # Load PDF using PyMuPDF
            loader = PyMuPDFLoader(pdf_path)
            documents = loader.load()

            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            split_docs = text_splitter.split_documents(documents)

            # Extract text and merge metadata
            texts = [doc.page_content for doc in split_docs]
            chunk_metadata = metadata or {}
            metadatas = []
            for doc in split_docs:
                # Merge loader metadata (page numbers, etc.) with custom metadata
                merged_metadata = {**doc.metadata, **chunk_metadata}
                metadatas.append(merged_metadata)

            # Add to vector store
            count = await self.add_documents(texts, metadatas)
            return count

        except Exception as e:
            logger.error("Error processing PDF: %s", e)
            raise

