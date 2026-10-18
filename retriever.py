
import re
from pathlib import Path

KNOWLEDGE_FILE = Path(__file__).parent / "knowledge.txt"

STOP_WORDS = {
    "the", "a", "an", "is", "are", "to", "do",
    "i", "you", "my", "how", "what", "when",
    "can", "does", "in", "of", "for", "and",
    "with", "it", "on", "me"
}


def get_sections():
    text = KNOWLEDGE_FILE.read_text(encoding="utf-8")

    # Split at the numbered knowledge headings
    parts = re.split(r"(?m)^(?=\d+\.\s+[A-Z])", text)

    sections = []

    for part in parts:
        part = part.strip()

        if re.match(r"^\d+\.\s+[A-Z]", part):
            sections.append(part)

    return sections



def get_words(text):
    text = text.lower()

    text = text.replace("workorder", "work order")
    text = text.replace("work-order", "work order")
    text = text.replace("creating", "create")
    text = text.replace("adding", "add")

    words = re.findall(r"[a-z0-9]+", text)

    synonyms = {
        "add": "create",
        "submit": "create",
        "report": "create",
        "request": "order",
        "ticket": "order",
        "priorities": "priority",
    }

    return {
        synonyms.get(word, word)
        for word in words
        if word not in STOP_WORDS and len(word) > 2
    }


def retrieve(question, top_k=2):
    question_words = get_words(question)
    results = []

    for section in get_sections():
        # Compare question words with section words
        section_words = get_words(section)
        score = len(question_words & section_words)

        if score > 0:
            results.append((score, section))

    # Highest matching score first
    results.sort(key=lambda item: item[0], reverse=True)

    return [section for score, section in results[:top_k]]


if __name__ == "__main__":
    question = input("Ask a RoadOps question: ")

    matches = retrieve(question)

    if matches:
        for section in matches:
            print("\n", section)
    else:
        print("No matching documentation found.")
