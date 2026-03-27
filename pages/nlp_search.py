"""
JobMate NLP Search Engine
=========================
Provides intelligent search using:
  1. Synonym expansion  — "dev" → developer, programmer, engineer …
  2. Simple suffix stemming  — "designing" → "design"
  3. TF-IDF cosine similarity  (sklearn, already installed)
  4. Token-level fuzzy matching  (difflib – stdlib)  for typo tolerance
  5. Combined ranking  (60 % TF-IDF + 40 % fuzzy)

All pure-Python / stdlib + sklearn — no internet or extra installs needed.

Usage
-----
from .nlp_search import nlp_filter_ids, nlp_search_text

# Filter a Django queryset by NLP relevance
ids = nlp_filter_ids(query, [(obj.pk, obj.search_text) for obj in qs])
results = qs.filter(pk__in=ids)

# Or rank arbitrary text snippets
ranked_ids = nlp_search_text(query, [(id, text), …], threshold=0.05)
"""

import re
import unicodedata
from difflib import SequenceMatcher
from typing import List, Tuple, Optional

# ── sklearn (available in this environment) ──────────────────────────────────
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _SKLEARN = True
except ImportError:
    _SKLEARN = False

# ── Domain-specific synonym map ───────────────────────────────────────────────
# Keys are canonical roots; values are synonyms/expansions.
# When any token matches a key OR value, all synonyms are added to the query.
_SYNONYMS: dict[str, list[str]] = {
    # Tech / development
    "dev":       ["developer", "programmer", "engineer", "coder", "coding", "development", "software"],
    "web":       ["website", "frontend", "backend", "html", "css", "javascript", "react", "node", "fullstack", "full-stack"],
    "data":      ["database", "analytics", "analysis", "analyst", "statistics", "reporting", "sql", "excel"],
    "mobile":    ["android", "ios", "flutter", "swift", "kotlin", "app", "application"],
    "cloud":     ["aws", "azure", "gcp", "devops", "docker", "kubernetes", "server", "hosting"],
    "security":  ["cybersecurity", "penetration", "pen-test", "ethical", "hacking", "network"],
    "ai":        ["machine", "learning", "ml", "deep", "neural", "nlp", "artificial", "intelligence"],
    # Design
    "design":    ["designer", "ui", "ux", "graphic", "visual", "creative", "artwork", "branding", "logo"],
    "video":     ["editing", "motion", "animation", "after-effects", "premiere", "filmmaker"],
    "photo":     ["photography", "photographer", "retouching", "photoshop", "lightroom"],
    # Business / admin
    "admin":     ["administration", "administrative", "operations", "office", "clerical", "secretary"],
    "manage":    ["manager", "management", "lead", "head", "supervisor", "coordinator", "director"],
    "hr":        ["human", "resources", "recruitment", "hiring", "talent", "payroll"],
    "legal":     ["law", "lawyer", "attorney", "contract", "compliance", "paralegal"],
    # Finance
    "finance":   ["financial", "accounting", "accountant", "payment", "revenue", "billing", "invoice", "tax", "audit"],
    "budget":    ["cost", "expense", "forecasting", "planning"],
    # Marketing / content
    "market":    ["marketing", "seo", "sem", "social", "media", "advertis", "promotion", "campaign", "ppc", "growth"],
    "content":   ["write", "writer", "writing", "copywriting", "blog", "article", "editor", "editorial", "journalist"],
    "translate": ["translation", "interpreter", "language", "localisation", "localization"],
    # Support / customer
    "support":   ["helpdesk", "customer", "service", "assist", "technical", "care", "chat", "crm"],
    "sales":     ["selling", "business", "development", "lead", "generation", "b2b", "b2c", "retail"],
    # Status/availability
    "available": ["open", "free", "hiring", "active", "accepting", "ready"],
    "senior":    ["experienced", "expert", "advanced", "sr", "lead", "principal", "head"],
    "junior":    ["entry", "beginner", "fresh", "jr", "trainee", "intern", "graduate"],
    # Departments (common)
    "it":        ["information", "technology", "tech", "computer", "systems"],
    "education": ["teaching", "teacher", "tutor", "trainer", "instructor", "elearning"],
    "health":    ["medical", "healthcare", "nurse", "doctor", "clinic", "hospital", "pharma"],
    "construct": ["construction", "civil", "architect", "building", "engineer", "structural"],
    "transport": ["logistics", "delivery", "driver", "fleet", "supply", "chain", "warehouse"],
}

# Flat reverse map: synonym → canonical root (for fast lookup)
_SYN_REVERSE: dict[str, str] = {}
for _root, _syns in _SYNONYMS.items():
    _SYN_REVERSE[_root] = _root
    for _s in _syns:
        _SYN_REVERSE[_s] = _root

# ── Stop words ────────────────────────────────────────────────────────────────
_STOP = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "can", "need", "to", "of", "in",
    "on", "at", "for", "with", "by", "from", "up", "about", "into",
    "through", "i", "me", "my", "we", "our", "you", "your", "they",
    "their", "it", "its", "this", "that", "these", "those", "and", "or",
    "but", "if", "then", "so", "not", "no", "nor", "who", "what", "where",
    "when", "how", "all", "any", "some", "show", "find", "get", "give",
    "want", "need", "looking", "search", "list",
})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase, strip accents, remove non-alphanumeric."""
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9\s]", " ", text.lower())


def _stem(word: str) -> str:
    """Very lightweight suffix stripper (not Porter — avoids over-stemming)."""
    suffixes = ["tion", "sion", "ing", "ness", "ment", "ity", "ies",
                "ical", "ful", "ize", "ise", "ous", "al", "ed", "er", "ly", "s"]
    w = word.lower()
    for s in suffixes:
        if w.endswith(s) and len(w) - len(s) >= 3:
            return w[: -len(s)]
    return w


def _tokenize(text: str) -> List[str]:
    return [t for t in _normalize(text).split() if t not in _STOP and len(t) > 1]


def _expand_query(query: str) -> str:
    """
    Expand query tokens with synonyms.
    e.g. "web dev" → "web website frontend ... dev developer programmer ..."
    """
    tokens = _tokenize(query)
    expanded: set[str] = set(tokens)

    for tok in tokens:
        stemmed = _stem(tok)
        # Direct match on synonym map
        root = _SYN_REVERSE.get(tok) or _SYN_REVERSE.get(stemmed)
        if root:
            expanded.add(root)
            expanded.update(_SYNONYMS.get(root, []))
        else:
            # Partial prefix match (e.g. "admin" matches "administration")
            for key in _SYN_REVERSE:
                if len(tok) >= 4 and (key.startswith(tok) or tok.startswith(key[:4])):
                    r = _SYN_REVERSE[key]
                    expanded.add(r)
                    expanded.update(_SYNONYMS.get(r, []))
                    break

    return " ".join(expanded)


def _fuzzy_token_score(query_tokens: List[str], doc_text: str) -> float:
    """Average best-match fuzzy score of each query token against doc tokens.
    Only counts as a match if ratio >= 0.65 to avoid spurious matches."""
    if not query_tokens:
        return 0.0
    doc_tokens = _normalize(doc_text).split()
    if not doc_tokens:
        return 0.0
    scores = []
    for qt in query_tokens:
        best = max(
            (SequenceMatcher(None, qt, dt).ratio() for dt in doc_tokens),
            default=0.0,
        )
        # Only reward genuine matches; penalize weak ones
        scores.append(best if best >= 0.65 else best * 0.3)
    return sum(scores) / len(scores)


# ── Public API ────────────────────────────────────────────────────────────────

def nlp_search_text(
    query: str,
    documents: List[Tuple],
    threshold: float = 0.18,
    tfidf_weight: float = 0.6,
) -> List:
    """
    Rank documents by NLP relevance to query.

    Parameters
    ----------
    query       : raw user search string
    documents   : list of (id, text_for_matching) tuples
    threshold   : minimum combined score to include in results (0–1)
    tfidf_weight: weight for TF-IDF score (remainder goes to fuzzy)

    Returns
    -------
    List of ids sorted by descending relevance, filtered by threshold.
    If query is blank, returns all ids in original order.
    """
    if not query or not query.strip() or not documents:
        return [d[0] for d in documents]

    expanded_q = _expand_query(query)
    query_tokens = _tokenize(query)
    doc_texts = [_normalize(str(d[1])) for d in documents]

    # ── TF-IDF cosine ─────────────────────────────────────────────────────────
    tfidf_scores = [0.0] * len(documents)
    if _SKLEARN and len(documents) > 0:
        try:
            corpus = doc_texts + [_normalize(expanded_q)]
            vec = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                min_df=1,
                sublinear_tf=True,
            )
            matrix = vec.fit_transform(corpus)
            sims = cosine_similarity(matrix[-1:], matrix[:-1])[0]
            tfidf_scores = sims.tolist()
        except Exception:
            pass  # fall back to fuzzy only

    # ── Fuzzy token matching ──────────────────────────────────────────────────
    fuzzy_weight = 1.0 - tfidf_weight
    combined: List[Tuple] = []
    for i, (doc_id, _) in enumerate(documents):
        fuzzy = _fuzzy_token_score(query_tokens, doc_texts[i])
        score = tfidf_weight * tfidf_scores[i] + fuzzy_weight * fuzzy
        combined.append((doc_id, score))

    # Sort descending, filter by threshold
    combined.sort(key=lambda x: -x[1])
    return [did for did, score in combined if score >= threshold]


def nlp_filter_queryset(query: str, qs, text_fn):
    """
    Filter and order a Django queryset using NLP.

    Parameters
    ----------
    query   : raw user search string
    qs      : Django queryset (already fetched or lazy — will be evaluated)
    text_fn : callable(obj) → str  — builds the search text for each object

    Returns
    -------
    A plain Python list of model instances, NLP-ranked.
    If query is blank, returns list(qs) unchanged.
    """
    if not query or not query.strip():
        return list(qs)

    objects = list(qs)
    if not objects:
        return []

    docs = [(obj.pk, text_fn(obj)) for obj in objects]
    ranked_ids = nlp_search_text(query, docs)

    pk_to_obj = {obj.pk: obj for obj in objects}
    return [pk_to_obj[pk] for pk in ranked_ids if pk in pk_to_obj]
