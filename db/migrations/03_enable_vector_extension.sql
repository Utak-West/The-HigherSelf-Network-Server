-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notion_page_id TEXT,
    notion_database_id TEXT,
    content_type TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding_vector VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    embedding_provider TEXT NOT NULL,
    UNIQUE(content_hash, embedding_provider)
);

-- Create vector chunks table for text splitting
CREATE TABLE IF NOT EXISTS vector_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    embedding_id UUID REFERENCES embeddings(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_embedding VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(embedding_id, chunk_index)
);

-- Create indexes for similarity search
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_chunks_vector ON vector_chunks USING ivfflat (chunk_embedding vector_cosine_ops) WITH (lists = 100);
