from pathlib import Path

import pymupdf
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# ============================================================
# PDF LOADING
# ============================================================

def load_policy_pages():
    """
    Read every PDF in the data folder page-by-page.

    Every extracted page keeps:
    - PDF filename
    - page number
    - extracted text

    This provenance is important because INSUREAI must be able
    to trace generated claims back to the original brochure.
    """

    pages = []

    for pdf_path in DATA_DIR.glob("*.pdf"):

        document = pymupdf.open(pdf_path)

        for page_number, page in enumerate(document, start=1):

            text = page.get_text("text").strip()

            if text:
                pages.append(
                    {
                        "file": pdf_path.name,
                        "page": page_number,
                        "text": text,
                    }
                )

        document.close()

    return pages


# ============================================================
# TF-IDF INDEX
# ============================================================

def build_retriever(pages):
    """
    Convert policy pages into TF-IDF vectors.

    Unigrams and bigrams are used so both individual words and
    phrases such as "waiting period" can contribute to retrieval.
    """

    texts = [
        page["text"]
        for page in pages
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
    )

    page_vectors = vectorizer.fit_transform(
        texts
    )

    return vectorizer, page_vectors


# ============================================================
# SEARCH
# ============================================================

def search_policies(
    query,
    pages,
    vectorizer,
    page_vectors,
    top_k=3,
):
    """
    Return the policy pages whose wording is most relevant
    to the supplied query.

    Cosine similarity is a RETRIEVAL score only.

    It must not be interpreted as factual confidence.
    """

    query_vector = vectorizer.transform(
        [query]
    )

    scores = cosine_similarity(
        query_vector,
        page_vectors,
    ).flatten()

    best_indices = scores.argsort()[::-1][
        :top_k
    ]

    results = []

    for index in best_indices:

        results.append(
            {
                "file": pages[index]["file"],
                "page": pages[index]["page"],
                "score": round(
                    float(scores[index]),
                    4,
                ),
                "text": pages[index]["text"],
            }
        )

    return results