"""
Enhanced text chunking strategies for The HigherSelf Network Server.

This module provides advanced text chunking strategies for better
retrieval performance in RAG applications.
"""

import re
from typing import List, Dict, Any, Optional, Union, Callable
from loguru import logger
import nltk
from nltk.tokenize import sent_tokenize
from nltk.tokenize.punkt import PunktSentenceTokenizer
import hashlib

# Ensure NLTK resources are available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


class ChunkingStrategy:
    """Base class for text chunking strategies."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the chunking strategy.
        
        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: Text to split into chunks
            
        Returns:
            List of text chunks
        """
        raise NotImplementedError("Subclasses must implement chunk_text")


class SimpleChunker(ChunkingStrategy):
    """Simple chunking strategy that splits text by character count."""
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks by character count.
        
        Args:
            text: Text to split into chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            # Find the end of the chunk
            end = min(start + self.chunk_size, text_len)
            
            # If we're not at the end of the text, try to break at a newline or space
            if end < text_len:
                # Look for a newline
                newline_pos = text.rfind('\n', start, end)
                if newline_pos > start:
                    end = newline_pos + 1
                else:
                    # Look for a space
                    space_pos = text.rfind(' ', start, end)
                    if space_pos > start:
                        end = space_pos + 1
            
            # Add the chunk
            chunks.append(text[start:end].strip())
            
            # Move to the next chunk with overlap
            start = end - self.chunk_overlap if end < text_len else text_len
        
        return chunks


class SentenceChunker(ChunkingStrategy):
    """Chunking strategy that respects sentence boundaries."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the sentence chunker.
        
        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
        """
        super().__init__(chunk_size, chunk_overlap)
        self.tokenizer = PunktSentenceTokenizer()
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks respecting sentence boundaries.
        
        Args:
            text: Text to split into chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # Split text into sentences
        try:
            sentences = self.tokenizer.tokenize(text)
        except Exception as e:
            logger.warning(f"Error tokenizing text into sentences: {e}. Falling back to simple chunking.")
            return SimpleChunker(self.chunk_size, self.chunk_overlap).chunk_text(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # If a single sentence is larger than chunk_size, split it
            if sentence_size > self.chunk_size:
                # Add the current chunk if it's not empty
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split the long sentence using simple chunking
                sentence_chunks = SimpleChunker(self.chunk_size, self.chunk_overlap).chunk_text(sentence)
                chunks.extend(sentence_chunks)
                continue
            
            # If adding this sentence would exceed the chunk size, start a new chunk
            if current_size + sentence_size > self.chunk_size:
                chunks.append(' '.join(current_chunk))
                
                # Start a new chunk with overlap
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap // 20)  # Approximate by words
                current_chunk = current_chunk[overlap_start:]
                current_size = sum(len(s) for s in current_chunk)
            
            # Add the sentence to the current chunk
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks


class ParagraphChunker(ChunkingStrategy):
    """Chunking strategy that respects paragraph boundaries."""
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks respecting paragraph boundaries.
        
        Args:
            text: Text to split into chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # Split text into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            paragraph_size = len(paragraph)
            
            # If a single paragraph is larger than chunk_size, split it using sentence chunking
            if paragraph_size > self.chunk_size:
                # Add the current chunk if it's not empty
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split the long paragraph using sentence chunking
                paragraph_chunks = SentenceChunker(self.chunk_size, self.chunk_overlap).chunk_text(paragraph)
                chunks.extend(paragraph_chunks)
                continue
            
            # If adding this paragraph would exceed the chunk size, start a new chunk
            if current_size + paragraph_size > self.chunk_size:
                chunks.append('\n\n'.join(current_chunk))
                
                # Start a new chunk with overlap
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap // 50)  # Approximate by paragraphs
                current_chunk = current_chunk[overlap_start:]
                current_size = sum(len(p) for p in current_chunk)
            
            # Add the paragraph to the current chunk
            current_chunk.append(paragraph)
            current_size += paragraph_size
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks


class SemanticChunker(ChunkingStrategy):
    """
    Chunking strategy that attempts to maintain semantic coherence.
    
    This chunker uses a combination of paragraph and sentence boundaries,
    along with heuristics to identify topic changes.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the semantic chunker.
        
        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
        """
        super().__init__(chunk_size, chunk_overlap)
        self.paragraph_chunker = ParagraphChunker(chunk_size, chunk_overlap)
        self.sentence_chunker = SentenceChunker(chunk_size, chunk_overlap)
        
        # Topic change indicators
        self.topic_indicators = [
            r'\b(?:however|nevertheless|conversely|on the other hand)\b',
            r'\b(?:first|second|third|fourth|finally|lastly)\b',
            r'\b(?:in conclusion|to summarize|in summary)\b',
            r'^\s*(?:#+)\s+',  # Markdown headers
            r'^\s*(?:\d+\.|\*|\-)\s+'  # List items
        ]
        self.topic_pattern = re.compile('|'.join(self.topic_indicators), re.IGNORECASE | re.MULTILINE)
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into semantically coherent chunks.
        
        Args:
            text: Text to split into chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # First, split by paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            paragraph_size = len(paragraph)
            
            # Check for topic change indicators
            is_topic_change = bool(self.topic_pattern.search(paragraph))
            
            # If this paragraph starts a new topic and we have content,
            # or if adding this paragraph would exceed the chunk size,
            # start a new chunk
            if ((is_topic_change and current_chunk) or 
                (current_size + paragraph_size > self.chunk_size)):
                
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
            
            # If a single paragraph is larger than chunk_size, split it
            if paragraph_size > self.chunk_size:
                # Split the long paragraph using sentence chunking
                paragraph_chunks = self.sentence_chunker.chunk_text(paragraph)
                
                # If we have content in the current chunk, add the first part of the split paragraph
                if current_chunk and paragraph_chunks:
                    current_chunk.append(paragraph_chunks[0])
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                    
                    # Add the remaining paragraph chunks
                    chunks.extend(paragraph_chunks[1:])
                else:
                    # Add all paragraph chunks
                    chunks.extend(paragraph_chunks)
                
                continue
            
            # Add the paragraph to the current chunk
            current_chunk.append(paragraph)
            current_size += paragraph_size
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks


def get_chunker(strategy: str = "semantic", chunk_size: int = 1000, chunk_overlap: int = 200) -> ChunkingStrategy:
    """
    Get a chunker instance based on the specified strategy.
    
    Args:
        strategy: Chunking strategy ("simple", "sentence", "paragraph", or "semantic")
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters
        
    Returns:
        ChunkingStrategy instance
    """
    strategies = {
        "simple": SimpleChunker,
        "sentence": SentenceChunker,
        "paragraph": ParagraphChunker,
        "semantic": SemanticChunker
    }
    
    chunker_class = strategies.get(strategy.lower(), SemanticChunker)
    return chunker_class(chunk_size, chunk_overlap)
