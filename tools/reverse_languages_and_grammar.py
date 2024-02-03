"""Script to reverse language and grammar keys.

Replace:

```json
{
    "house": {
        "singular":
            "en": "house",
            "fi": "talo"
        },
        "plural":
            "en": "houses",
            "fi": "talot"
        }
    }
}
```

With:

```json
{
    "house": {
        "en": {
            "singular": "house",
            "plural": "houses",
        },
        "fi": {
            "singular": "talo",
            "plural": "talot",
        }
    }
}
```

Invoke from the root folder:
$ python tools/reverse_languages_and_grammar.py
"""

import json
import pathlib

CONCEPT_RELATIONS = [
    "answer",
    "answer-only",
    "antonym",
    "example",
    "holonym",
    "hypernym",
    "hyponym",
    "involved_by",
    "involves",
    "meronym",
    "roots",
]
LANGUAGES = ["en", "fi", "nl"]


def slice_concept(concept, language) -> dict:
    """Return the concept, but only for the specified language."""
    if language in concept:
        return concept[language]
    sliced = {}
    for key, value in concept.items():
        if key in LANGUAGES and key != language:
            continue
        if key in CONCEPT_RELATIONS:
            continue
        sliced[key] = slice_concept(value, language)
    return sliced


def reverse_concept(concept):
    """Reverse the languages and the grammar."""
    reversed_concept = {}
    for relation in CONCEPT_RELATIONS:
        if relation in concept:
            reversed_concept[relation] = concept[relation]
    for language in LANGUAGES:
        reversed_concept[language] = slice_concept(concept, language)
    return reversed_concept


for json_filename in pathlib.Path("src/concepts").glob("**/*.json"):
    with json_filename.open("r", encoding="utf-8") as json_file:
        contents = json.load(json_file)
    for concept_id, concept in contents.items():
        contents[concept_id] = reverse_concept(concept)

    print(json.dumps(contents, indent=4, ensure_ascii=False))

    """
    with json_filename.open("w", encoding="utf-8") as json_file:
        json.dump(contents, json_file, indent=4, ensure_ascii=False)
        json_file.write("\n")
    """
