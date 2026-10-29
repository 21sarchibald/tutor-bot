from server.services.study_context import retrieve_context, save_study_context


def test_retrieves_relevant_source_sections(tmp_path, monkeypatch):
    monkeypatch.setattr("server.services.study_context.CONTEXTS_DIR", tmp_path)
    context_id = save_study_context(
        "biology.txt",
        "Photosynthesis converts light energy into chemical energy.\n\n"
        "Mitosis produces two genetically identical daughter cells.",
    )

    result = retrieve_context(context_id, "How does photosynthesis use light energy?")

    assert result["filename"] == "biology.txt"
    assert result["sources"]
    assert "Photosynthesis" in result["sources"][0]["text"]


def test_missing_context_is_safe():
    result = retrieve_context("does-not-exist", "What is this?")

    assert result == {"filename": "", "sources": []}
