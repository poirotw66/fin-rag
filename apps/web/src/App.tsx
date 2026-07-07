import { FormEvent, useState } from "react";

import { askQuestion } from "./api";
import type { AskResponse } from "./types";

export default function App() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AskResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await askQuestion(trimmed);
      setResult(response);
    } catch (submitError) {
      setResult(null);
      setError(submitError instanceof Error ? submitError.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Public regulation assistant</p>
        <h1>Fin RAG</h1>
        <p className="subtitle">
          Ask about AML and securities-trust rules with citations from the public corpus.
        </p>
        <form className="ask-form" onSubmit={handleSubmit}>
          <label htmlFor="question">Question</label>
          <textarea
            id="question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="例如：什麼是風險基礎方法？"
            rows={4}
          />
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? "Asking..." : "Ask"}
          </button>
        </form>
        {error ? <p className="error">{error}</p> : null}
      </section>

      {result ? (
        <>
          <section className="answer-card">
            <h2>Answer</h2>
            <p className="answer-text">{result.answer}</p>
            <p className="meta">
              Refused: {result.refused ? "yes" : "no"} · Citation hit:{" "}
              {result.citation_hit ? "yes" : "no"}
              {result.retrieval_confidence !== null ? (
                <> · Confidence: {result.retrieval_confidence.toFixed(4)}</>
              ) : null}
              {" · "}Round: {result.retrieval_round}
              {" · "}Attempts: {result.generation_attempts}
              {result.refusal_reason ? <> · Reason: {result.refusal_reason}</> : null}
            </p>
          </section>

          <section className="citations-card">
            <h2>Citations</h2>
            {result.citations.length === 0 ? (
              <p className="muted">No citations returned.</p>
            ) : (
              <ul>
                {result.citations.map((citation) => (
                  <li key={`${citation.doc_id}-${citation.article}`}>
                    <strong>{citation.title}</strong> · {citation.doc_id} · {citation.article}
                  </li>
                ))}
              </ul>
            )}
          </section>

          <details className="retrieved-card">
            <summary>Retrieved chunks ({result.retrieved.length})</summary>
            {result.retrieved.length === 0 ? (
              <p className="muted">No retrieved chunks.</p>
            ) : (
              <ul>
                {result.retrieved.map((chunk, index) => (
                  <li key={`${chunk.doc_id}-${chunk.article}-${index}`}>
                    <p className="chunk-heading">
                      [{index + 1}] {chunk.doc_id} / {chunk.article} / score={chunk.score}
                    </p>
                    <p className="chunk-text">{chunk.text}</p>
                  </li>
                ))}
              </ul>
            )}
          </details>
        </>
      ) : null}
    </main>
  );
}
