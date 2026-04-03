# Test Data

QA pairs for evaluating RAG retrieval quality.

## How to generate

1. Open Gemini (or any model that handles Armenian well)
2. Copy the prompt from `prompts/generate_test_qa_pairs.md`
3. Attach `scraped_data/chunks_paragraph.json` as context
4. Save the output as `test_data/qa_pairs.json`

## Expected format

```json
{
  "test_pairs": [
    {
      "id": "test_001",
      "question": "Armenian question",
      "expected_chunk_ids": ["infocom_XXXXX_chunk_000"],
      "answer": "Armenian answer",
      "difficulty": "easy|medium|hard",
      "category": "factual|analytical|comparison|broad"
    }
  ]
}
```
