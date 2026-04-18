-- Run this in your Supabase SQL editor to create the papers table

create table if not exists papers (
  id uuid primary key default gen_random_uuid(),
  arxiv_id text not null unique,
  title text not null,
  authors jsonb not null default '[]',
  abstract text not null,
  published_date date,
  arxiv_url text,
  pdf_url text,
  status text not null default 'unread' check (status in ('unread', 'reading', 'read')),
  analysis jsonb,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Index for faster keyword search inside analysis JSON
create index if not exists papers_analysis_keywords_idx on papers using gin ((analysis->'keywords'));

-- Auto-update updated_at
create or replace function update_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger papers_updated_at
  before update on papers
  for each row execute function update_updated_at();
