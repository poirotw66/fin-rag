export type Citation = {
  doc_id: string;
  article: string;
  title: string;
};

export type RetrievedChunk = {
  doc_id: string;
  title: string;
  article: string;
  text: string;
  score: number;
};

export type AskResponse = {
  question: string;
  answer: string;
  refused: boolean;
  citation_hit: boolean;
  citations: Citation[];
  retrieved: RetrievedChunk[];
};
