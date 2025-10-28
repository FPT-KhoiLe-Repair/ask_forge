
def build_queries_prompt(seed_question,contexts, n, lang):
    ctx = contexts.strip()[:4000] if contexts else ""
    return f"""
Generate {n} thought follow-up questions in {lang} that help the learner think deeper.
Seed question: "{seed_question}".

Context (optional, maybe empty):
{ctx}

Constraints:
- Open-ended, diverse angles (why/how/what-if/counterfactual/compare).
- Avoid repeating the seed question.
- One question per line, no numbering.
"""
#     return f"""
# Answer in {lang}
# Question: {seed_question}
# Context: {ctx}
# Answer:"""