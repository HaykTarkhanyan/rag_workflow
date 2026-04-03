# Prompt: Generate Test QA Pairs for RAG Evaluation

Use this prompt with Gemini (or another model that handles Armenian well).
Copy-paste this prompt, then attach the file `scraped_data/chunks_paragraph.json`.

---

## Prompt

You are an expert in Armenian language and investigative journalism. I'm building a RAG (Retrieval-Augmented Generation) system over Armenian investigative articles from Infocom.am. I need test data to evaluate retrieval quality.

I'm attaching a JSON file (`chunks_paragraph.json`) containing text chunks from 65 investigative articles. Each chunk has a `chunk_id`, `article_id`, `text`, and `metadata` (title, author, date, etc.).

**Your task:** Generate exactly 20 question-answer-chunk triplets for testing RAG retrieval. For each triplet, provide:

1. **question** — A natural Armenian question that a user might ask. Vary the types:
   - **Part A: 10 Varied Questions**
     - 3 factual questions (specific numbers, names, dates)
     - 3 analytical questions (why something happened, what patterns exist)
     - 2 comparison questions (comparing municipalities, amounts, time periods)
     - 2 broad topic questions (what investigations cover a topic area)
   - **Part B: 10 Short-Answer Questions**
     - These must be very easy to check automatically.
     - The answer should be ONLY a single number, a single name, or a short phrase (1-3 words).
     - These should have a "category": "short_answer".

2. **expected_chunk_ids** — A list of 1-3 chunk_ids that contain the answer. These must be real chunk_ids from the file.

3. **answer** — The correct answer in Armenian, based strictly on the chunk text. Keep it 1-3 sentences.

4. **difficulty** — One of: "easy" (answer is stated explicitly in one chunk), "medium" (requires reading across the chunk), "hard" (requires connecting information from multiple chunks or inference)

**Output format:** Return valid JSON exactly like this:

```json
{
  "test_pairs": [
    {
      "id": "test_001",
      "question": "Armenian question here?",
      "expected_chunk_ids": ["infocom_XXXXX_chunk_000"],
      "answer": "Armenian answer here.",
      "difficulty": "easy",
      "category": "factual"
    }
  ]
}
```

**Important rules:**
- All questions and answers MUST be in Armenian
- Every `expected_chunk_ids` value MUST be a real chunk_id from the attached file
- Answers must be grounded in the actual chunk text, not hallucinated
- Cover at least 10 different articles across the 20 questions
- Include questions with different specificity levels (some should match one chunk precisely, others could match several)
- Think about what a journalist, researcher, or citizen would actually want to know from these investigations

---

## After generating

Save the output as `test_data/qa_pairs.json` in the repo. The evaluation script will use it to:
1. Embed each question with the same model
2. Retrieve top-k chunks from ChromaDB
3. Check if `expected_chunk_ids` appear in retrieved results
4. Measure recall@k, MRR, and precision
