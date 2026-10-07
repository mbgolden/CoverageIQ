from coverageiq.retrieval.tokenize import tokenize


def test_lowercases_and_drops_punctuation() -> None:
    assert tokenize("Ozempic (semaglutide), Tier 3.") == ["ozempic", "semaglutide", "tier", "3"]


def test_keeps_codes_whole() -> None:
    assert tokenize("CPT 45378 and J1817") == ["cpt", "45378", "j1817"]


def test_drops_stopwords() -> None:
    assert tokenize("What is my deductible?") == ["deductible"]


def test_query_and_document_tokenize_the_same() -> None:
    assert tokenize("Is OZEMPIC covered?") == tokenize("ozempic covered")


def test_drops_domain_words_every_question_contains() -> None:
    assert tokenize("Does my plan cover Ozempic?") == ["ozempic"]
    assert tokenize("Is a colonoscopy covered?") == ["colonoscopy"]
