
import re
from io import BytesIO

from pypdf import PdfReader


def extract_pdf_text(uploaded_file):
    """Extract readable text from a PDF upload or PDF bytes."""
    if isinstance(uploaded_file, bytes):
        pdf_bytes = uploaded_file
    elif hasattr(uploaded_file, "getvalue"):
        pdf_bytes = uploaded_file.getvalue()
    else:
        raise TypeError("Please upload a PDF file.")

    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    try:
        reader = PdfReader(BytesIO(pdf_bytes))

        if reader.is_encrypted:
            try:
                result = reader.decrypt("")
                if not result:
                    raise ValueError(
                        "This PDF is password-protected."
                    )
            except ValueError:
                raise
            except Exception as exc:
                raise ValueError(
                    "This PDF is password-protected."
                ) from exc

        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")

        text = "\n\n".join(pages).strip()

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(
            "Could not read this PDF. Please try another PDF."
        ) from exc

    if not text:
        raise ValueError(
            "No readable text was found. This may be a scanned "
            "PDF that requires OCR."
        )

    return text


def split_sentences(text):
    """Split extracted text into usable sentences."""
    cleaned = re.sub(r"\s+", " ", text).strip()

    if not cleaned:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)

    return [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) >= 20
    ]


def generate_flashcards(text, limit=10):
    """Create simple revision cards from PDF sentences."""
    sentences = split_sentences(text)
    cards = []

    for sentence in sentences[:limit]:
        cards.append({
            "question": "What key point does the document explain?",
            "answer": sentence,
        })

    return cards


def generate_quiz(text, limit=10):
    """Create fill-in-the-blank questions from PDF sentences."""
    sentences = split_sentences(text)
    questions = []

    common_words = {
        "about", "after", "again", "also", "among", "because",
        "before", "being", "between", "could", "during", "every",
        "first", "found", "from", "have", "into", "itself",
        "more", "most", "other", "over", "same", "should",
        "some", "such", "than", "that", "their", "there",
        "these", "they", "this", "those", "through", "under",
        "very", "were", "what", "when", "where", "which",
        "while", "with", "would", "your",
    }

    for sentence in sentences:
        words = re.findall(r"\b[A-Za-z][A-Za-z-]*\b", sentence)

        candidates = [
            word for word in words
            if len(word) >= 5
            and word.lower() not in common_words
        ]

        if not candidates:
            continue

        answer = max(candidates, key=len)
        pattern = re.compile(re.escape(answer), re.IGNORECASE)
        question_text = pattern.sub("____", sentence, count=1)

        questions.append({
            "question": question_text,
            "answer": answer,
        })

        if len(questions) >= limit:
            break

    return questions
