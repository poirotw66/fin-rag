import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";

import App from "./App";
import * as api from "./api";
import type { AskResponse } from "./types";

test("renders product heading", () => {
  render(<App />);
  expect(screen.getByText(/Fin RAG/i)).toBeInTheDocument();
});

test("submits a question and renders answer details", async () => {
  const user = userEvent.setup();
  const mockResponse: AskResponse = {
    question: "什麼是風險基礎方法？",
    answer: "風險基礎方法係指依客戶及交易風險採取差異化措施。（aml-finst 第 2 條）",
    refused: false,
    citation_hit: true,
    citations: [
      { doc_id: "aml-finst", article: "第 2 條", title: "金融機構防制洗錢辦法" },
    ],
    retrieved: [
      {
        doc_id: "aml-finst",
        title: "金融機構防制洗錢辦法",
        article: "第 2 條",
        text: "本辦法所稱風險基礎方法，指依客戶及交易風險採取差異化措施。",
        score: 0.9,
      },
    ],
  };
  vi.spyOn(api, "askQuestion").mockResolvedValue(mockResponse);

  render(<App />);
  await user.type(screen.getByLabelText(/question/i), "什麼是風險基礎方法？");
  await user.click(screen.getByRole("button", { name: /ask/i }));

  expect(await screen.findByRole("heading", { name: "Answer" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Citations" })).toBeInTheDocument();
  await waitFor(() => {
    expect(screen.getByText(/風險基礎方法係指依客戶及交易風險採取差異化措施/)).toBeInTheDocument();
  });
});
