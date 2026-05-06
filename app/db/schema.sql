create extension if not exists vector;
create extension if not exists pgcrypto;

create table if not exists conversations (
  id uuid primary key default gen_random_uuid(),
  whatsapp_user_id text not null unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists chat_messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references conversations(id) on delete cascade,
  role text not null check (role in ('system', 'user', 'assistant', 'tool')),
  content text not null,
  wa_message_id text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists knowledge_chunks (
  id uuid primary key default gen_random_uuid(),
  source text not null,
  chunk_index int not null default 0,
  content text not null,
  embedding vector(384) not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists knowledge_chunks_embedding_idx
on knowledge_chunks
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

create index if not exists chat_messages_conversation_created_idx
on chat_messages (conversation_id, created_at desc);