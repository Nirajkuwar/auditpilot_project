"""
Deterministic Corporate Policy Retrieval Tool using TF-IDF and Cosine Similarity.
Parses corporate standard operating procedure (SOP) documents into structured clause chunks
and performs semantic ranking with zero external API calls or LLM dependencies.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Any, Protocol
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class PolicyClause:
    """Structured representation of an individual policy clause."""

    clause_id: str
    section: str
    title: str
    text: str
    search_text: str = field(repr=False)


class PolicyCorpus:
    """Parser and container for markdown policy documents structured by section and clause."""

    def __init__(self, policy_path: str | Path = "data/policy.md") -> None:
        self.path = Path(policy_path)
        self.clauses: list[PolicyClause] = []
        if self.path.exists():
            self._parse()

    def _parse(self) -> None:
        content = self.path.read_text(encoding="utf-8")
        curr_section = ""
        clause_blocks: list[dict[str, Any]] = []

        for line in content.splitlines():
            # Match section headers: ### Section X: ...
            sec_match = re.match(r"###\s+(Section\s+[0-9]+:\s+.*)", line)
            if sec_match:
                curr_section = sec_match.group(1).strip()
                continue

            # Match clause headers: - **Clause X.Y: Title**
            clause_match = re.match(r"-\s+\*\*Clause\s+([0-9]+\.[0-9]+):\s+([^*]+)\*\*", line)
            if clause_match:
                cid = f"Clause {clause_match.group(1)}"
                title = clause_match.group(2).strip()
                clause_blocks.append(
                    {
                        "clause_id": cid,
                        "section": curr_section,
                        "title": title,
                        "lines": [],
                    }
                )
            elif clause_blocks and line.strip() and not line.startswith("---"):
                clause_blocks[-1]["lines"].append(line.strip())

        self.clauses = []
        for block in clause_blocks:
            body_text = " ".join(block["lines"]).strip()
            # Rich search representation prioritizing clause ID, title, parent section, and body
            search_text = (
                f"{block['clause_id']} {block['title']} {block['title']} "
                f"{block['section']} {body_text}"
            )
            self.clauses.append(
                PolicyClause(
                    clause_id=block["clause_id"],
                    section=block["section"],
                    title=block["title"],
                    text=body_text,
                    search_text=search_text,
                )
            )


class PolicyRetriever(Protocol):
    """Abstract protocol for policy clause retrievers (e.g. TF-IDF, dense embeddings)."""

    def retrieve(self, query: str, k: int = 3) -> list[dict[str, Any]]: ...


class TfidfPolicyRetriever:
    """Deterministic policy retriever based on scikit-learn TF-IDF and cosine similarity."""

    def __init__(self, corpus: PolicyCorpus) -> None:
        self.corpus = corpus
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b[a-zA-Z0-9_\-\.]+\b",
            sublinear_tf=True,
        )
        if self.corpus.clauses:
            docs = [c.search_text for c in self.corpus.clauses]
            self.matrix = self.vectorizer.fit_transform(docs)
        else:
            self.matrix = None

    def retrieve(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        """Retrieve top-k relevant policy clauses for a given query string."""
        if not self.corpus.clauses or self.matrix is None or not query.strip():
            return []

        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix)[0]

        # Rank indices by descending similarity score
        top_indices = sims.argsort()[::-1][:k]
        results: list[dict[str, Any]] = []

        for idx in top_indices:
            score = float(sims[idx])
            clause = self.corpus.clauses[idx]
            results.append(
                {
                    "clause_id": clause.clause_id,
                    "title": clause.title,
                    "quote": clause.text,
                    "score": round(score, 4),
                }
            )

        return results


# Global singleton cache keyed by (normalized_path, mtime)
_RETRIEVER_CACHE: dict[tuple[str, float], TfidfPolicyRetriever] = {}


def _get_retriever(policy_path: str | Path) -> TfidfPolicyRetriever:
    p = Path(policy_path)
    if not p.exists():
        return TfidfPolicyRetriever(PolicyCorpus(p))

    mtime = p.stat().st_mtime
    key = (str(p.resolve()), mtime)
    if key not in _RETRIEVER_CACHE:
        corpus = PolicyCorpus(p)
        _RETRIEVER_CACHE[key] = TfidfPolicyRetriever(corpus)
    return _RETRIEVER_CACHE[key]


def retrieve_policy(
    query: str,
    k: int = 3,
    policy_path: str = "data/policy.md",
) -> dict[str, Any]:
    """Retrieve corporate policy clauses relevant to an audit compliance query using TF-IDF.

    Parses the policy SOP markdown document into structured clause chunks and matches
    queries against clause headings and requirements using deterministic cosine similarity.

    Args:
        query: Audit compliance question or search keywords (e.g. 'self approval segregation of duties').
        k: Maximum number of top matching clauses to return (default: 3).
        policy_path: Path to the corporate policy markdown file (default: 'data/policy.md').

    Returns:
        A dictionary with keys:
            - test: Name of the audit test ('retrieve_policy').
            - query: The query string searched.
            - results: List of top matching clauses, each containing clause_id, title, quote, and score.
            - notes: Summary of retrieval results.
    """
    path = Path(policy_path)
    if not path.exists():
        return {
            "test": "retrieve_policy",
            "query": query,
            "results": [],
            "notes": f"Policy file not found at path: {policy_path}",
        }

    retriever = _get_retriever(path)
    results = retriever.retrieve(query=query, k=k)

    if results:
        top = results[0]
        notes = (
            f"Retrieved {len(results)} relevant policy clauses for query: '{query}'. "
            f"Top match: {top['clause_id']} - {top['title']} (Score: {top['score']})."
        )
    else:
        notes = f"No matching policy clauses found for query: '{query}'."

    return {
        "test": "retrieve_policy",
        "query": query,
        "results": results,
        "notes": notes,
    }
