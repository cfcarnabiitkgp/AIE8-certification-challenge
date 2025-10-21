"""Vector store service using Qdrant."""
import uuid
import logging
from typing import List, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain.schema import Document
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
            openai_api_key=settings.openai_api_key,
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
    
    def _create_text_splitter(self):
        """
        Create text splitter based on chunking strategy in config.

        Returns:
            Text splitter instance (RecursiveCharacterTextSplitter or SemanticChunker)
        """
        if settings.chunking_strategy == "semantic":
            logger.info("Using SEMANTIC chunking strategy")
            logger.info(f"  - Breakpoint type: {settings.semantic_breakpoint_threshold_type}")
            logger.info(f"  - Breakpoint threshold: {settings.semantic_breakpoint_threshold_amount}")

            return SemanticChunker(
                embeddings=self.embeddings,
                breakpoint_threshold_type=settings.semantic_breakpoint_threshold_type,
                breakpoint_threshold_amount=settings.semantic_breakpoint_threshold_amount,
            )
        else:
            logger.info("Using FIXED-SIZE chunking strategy")
            logger.info(f"  - Chunk size: {settings.fixed_chunk_size}")
            logger.info(f"  - Overlap: {settings.fixed_chunk_overlap}")

            return RecursiveCharacterTextSplitter(
                chunk_size=settings.fixed_chunk_size,
                chunk_overlap=settings.fixed_chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )

    def _enforce_chunk_size_limits(self, chunks: List[Document]) -> List[Document]:
        """
        Enforce min/max chunk size limits for semantic chunking.

        For chunks exceeding max_size, split them using recursive splitter.
        For chunks below min_size, merge with adjacent chunks if possible.

        Args:
            chunks: List of document chunks

        Returns:
            List of size-constrained chunks
        """
        if settings.chunking_strategy != "semantic":
            return chunks  # Only apply to semantic chunks

        min_size = settings.semantic_min_chunk_size
        max_size = settings.semantic_max_chunk_size

        processed_chunks = []

        for chunk in chunks:
            chunk_len = len(chunk.page_content)

            # If chunk is too large, split it
            if chunk_len > max_size:
                logger.debug(f"Splitting large chunk ({chunk_len} chars) into smaller pieces")
                fallback_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=max_size,
                    chunk_overlap=200,
                    length_function=len,
                    separators=["\n\n", "\n", " ", ""]
                )
                sub_chunks = fallback_splitter.split_documents([chunk])
                processed_chunks.extend(sub_chunks)

            # If chunk is too small, still keep it (better than discarding)
            # Merging with adjacent chunks would break semantic boundaries
            elif chunk_len < min_size:
                logger.debug(f"Small chunk ({chunk_len} chars) kept as-is to preserve semantic boundary")
                processed_chunks.append(chunk)

            else:
                processed_chunks.append(chunk)

        return processed_chunks

    async def process_pdf(self, pdf_path: str, metadata: Optional[dict] = None) -> int:
        """
        Process a PDF file and add it to the vector store using PyMuPDF.

        Uses chunking strategy from config (semantic or fixed-size).

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

            # Create appropriate text splitter based on config
            text_splitter = self._create_text_splitter()

            # Split documents into chunks
            split_docs = text_splitter.split_documents(documents)

            # Enforce size limits for semantic chunks
            if settings.chunking_strategy == "semantic":
                split_docs = self._enforce_chunk_size_limits(split_docs)

                # Log chunk size statistics
                chunk_sizes = [len(doc.page_content) for doc in split_docs]
                logger.info(f"Semantic chunking stats:")
                logger.info(f"  - Total chunks: {len(chunk_sizes)}")
                logger.info(f"  - Avg chunk size: {sum(chunk_sizes) / len(chunk_sizes):.0f} chars")
                logger.info(f"  - Min chunk size: {min(chunk_sizes)} chars")
                logger.info(f"  - Max chunk size: {max(chunk_sizes)} chars")

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

