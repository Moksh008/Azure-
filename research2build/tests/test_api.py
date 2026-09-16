import asyncio
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.app.main import app, get_llm_service
from backend.app.services.research_service import ResearchService


class MockLLMService:
    def generate(
        self,
        prompt,
        system_prompt=None,
        temperature=0.0,
    ):
        if "What dataset" in prompt:
            return """
            {
                "answer": "The authors use an image classification dataset for evaluation.",
                "evidence_ids": ["chunk-1"],
                "evidence_sufficient": true
            }
            """

        return """
        {
            "problem": {
                "text": "The paper addresses image classification.",
                "evidence_ids": ["chunk-1"]
            },
            "objective": {
                "text": "The study aims to improve classification.",
                "evidence_ids": ["chunk-1"]
            },
            "methodology": {
                "text": "The authors use a convolutional neural network.",
                "evidence_ids": ["chunk-1"]
            },
            "dataset": {
                "text": "The evaluation uses an image classification dataset.",
                "evidence_ids": ["chunk-1"]
            },
            "models": {
                "text": "A convolutional neural network is used.",
                "evidence_ids": ["chunk-1"]
            },
            "results": [],
            "limitations": [],
            "future_work": []
        }
        """


app.dependency_overrides[get_llm_service] = lambda: MockLLMService()

client = TestClient(app)


def test_analysis_endpoint():
    response = client.post(
        "/analysis",
        json={
            "paper_id": "paper-1",
            "paper_title": "Test Research Paper",
            "evidence": [
                {
                    "chunk_id": "chunk-1",
                    "paper_id": "paper-1",
                    "paper_title": "Test Research Paper",
                    "section": "Methodology",
                    "page": 4,
                    "text": (
                        "The authors use a convolutional neural "
                        "network for image classification."
                    ),
                }
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["paper_id"] == "paper-1"
    assert data["paper_title"] == "Test Research Paper"
    assert data["methodology"]["citations"][0]["chunk_id"] == "chunk-1"


def test_qa_endpoint():
    response = client.post(
        "/qa",
        json={
            "question": "What dataset did the authors use?",
            "evidence": [
                {
                    "chunk_id": "chunk-1",
                    "paper_id": "paper-1",
                    "paper_title": "Test Research Paper",
                    "section": "Dataset",
                    "page": 5,
                    "text": (
                        "The evaluation uses an image "
                        "classification dataset."
                    ),
                }
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "image classification dataset" in data["answer"]
    assert data["evidence_sufficient"] is True
    assert data["citations"][0]["chunk_id"] == "chunk-1"


def test_analysis_endpoint_rejects_empty_evidence():
    response = client.post(
        "/analysis",
        json={
            "paper_id": "paper-1",
            "paper_title": "Test Research Paper",
            "evidence": [],
        },
    )

    assert response.status_code == 400


def test_qa_endpoint_rejects_empty_question():
    response = client.post(
        "/qa",
        json={
            "question": "   ",
            "evidence": [
                {
                    "chunk_id": "chunk-1",
                    "paper_id": "paper-1",
                    "paper_title": "Test Research Paper",
                    "section": "Introduction",
                    "page": 2,
                    "text": "The paper discusses image classification.",
                }
            ],
        },
    )

    assert response.status_code == 400


def test_qa_retrieve_integrates_m2_with_m3():
    retrieved_chunk = type(
        "RetrievedChunk",
        (),
        {
            "chunk_id": "chunk-1",
            "paper_id": "paper-1",
            "title": "Test Research Paper",
            "section": "Dataset",
            "page_number": 5,
            "text": "The evaluation uses an image classification dataset.",
        },
    )()

    mock_retriever = AsyncMock()
    mock_retriever.retrieve.return_value = [retrieved_chunk]

    class MockLLMService:
        def generate(
            self,
            prompt,
            system_prompt=None,
            temperature=0.0,
        ):
            return """
            {
                "answer": "The paper uses an image classification dataset.",
                "evidence_ids": ["chunk-1"],
                "evidence_sufficient": true
            }
            """

    with patch(
        "backend.app.services.research_service.get_retriever",
        return_value=mock_retriever,
    ):
        service = ResearchService(MockLLMService())

        result = asyncio.run(
            service.answer_question(
                question="What dataset did the authors use?",
                top_k=5,
            )
        )

    assert result.answer == (
        "The paper uses an image classification dataset."
    )
    assert result.evidence_sufficient is True
    assert len(result.citations) == 1

    citation = result.citations[0]

    assert citation.chunk_id == "chunk-1"
    assert citation.paper_id == "paper-1"
    assert citation.paper_title == "Test Research Paper"
    assert citation.section == "Dataset"
    assert citation.page == 5
    assert citation.quote == (
        "The evaluation uses an image classification dataset."
    )

    mock_retriever.retrieve.assert_awaited_once_with(
        question="What dataset did the authors use?",
        top_k=5,
    )


def test_qa_retrieve_endpoint_integrates_m2_and_m3():
    retrieved_chunk = type(
        "RetrievedChunk",
        (),
        {
            "chunk_id": "chunk-1",
            "paper_id": "paper-1",
            "title": "Test Research Paper",
            "section": "Methodology",
            "page_number": 3,
            "text": "The authors use a transformer-based model.",
        },
    )()

    mock_retriever = AsyncMock()
    mock_retriever.retrieve.return_value = [retrieved_chunk]

    class MockLLMService:
        def generate(
            self,
            prompt,
            system_prompt=None,
            temperature=0.0,
        ):
            return """
            {
                "answer": "The authors use a transformer-based model.",
                "evidence_ids": ["chunk-1"],
                "evidence_sufficient": true
            }
            """

    with patch(
        "backend.app.services.research_service.get_retriever",
        return_value=mock_retriever,
    ):
        app.dependency_overrides[get_llm_service] = (
            lambda: MockLLMService()
        )

        try:
            response = client.post(
                "/qa/retrieve",
                json={
                    "question": "What model do the authors use?",
                    "top_k": 5,
                },
            )
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == (
        "The authors use a transformer-based model."
    )
    assert data["evidence_sufficient"] is True
    assert len(data["citations"]) == 1

    citation = data["citations"][0]

    assert citation["chunk_id"] == "chunk-1"
    assert citation["paper_id"] == "paper-1"
    assert citation["paper_title"] == "Test Research Paper"
    assert citation["section"] == "Methodology"
    assert citation["page"] == 3
    assert citation["quote"] == (
        "The authors use a transformer-based model."
    )

    mock_retriever.retrieve.assert_awaited_once_with(
        question="What model do the authors use?",
        top_k=5,
    )


def test_research_service_analyze_paper_integrates_m2_with_m3():
    retrieved_chunk = type(
        "RetrievedChunk",
        (),
        {
            "chunk_id": "chunk-analysis-1",
            "paper_id": "paper-1",
            "title": "Test Research Paper",
            "section": "Methodology",
            "page_number": 4,
            "text": "The proposed method uses a transformer architecture.",
        },
    )()

    mock_retriever = AsyncMock()
    mock_retriever.retrieve.return_value = [retrieved_chunk]

    class MockLLMService:
        def generate(
            self,
            prompt,
            system_prompt=None,
            temperature=0.0,
        ):
            return """
            {
                "problem": {
                    "text": "The paper investigates a research problem.",
                    "evidence_ids": ["chunk-analysis-1"]
                },
                "objective": null,
                "methodology": {
                    "text": "The proposed method uses a transformer architecture.",
                    "evidence_ids": ["chunk-analysis-1"]
                },
                "dataset": null,
                "models": null,
                "results": [],
                "limitations": [],
                "future_work": []
            }
            """

    with patch(
        "backend.app.services.research_service.get_retriever",
        return_value=mock_retriever,
    ):
        service = ResearchService(MockLLMService())

        result = asyncio.run(
            service.analyze_paper(
                paper_id="paper-1",
                paper_title="Test Research Paper",
                query="What methodology does the paper use?",
                top_k=5,
            )
        )

    assert result.paper_id == "paper-1"
    assert result.paper_title == "Test Research Paper"
    assert result.problem is not None
    assert result.problem.text == (
        "The paper investigates a research problem."
    )
    assert result.methodology is not None
    assert result.methodology.text == (
        "The proposed method uses a transformer architecture."
    )

    citation = result.methodology.citations[0]

    assert citation.chunk_id == "chunk-analysis-1"
    assert citation.paper_id == "paper-1"
    assert citation.paper_title == "Test Research Paper"
    assert citation.section == "Methodology"
    assert citation.page == 4
    assert citation.quote == (
        "The proposed method uses a transformer architecture."
    )

    mock_retriever.retrieve.assert_awaited_once_with(
        question="What methodology does the paper use?",
        top_k=5,
    )


def test_qa_retrieve_rejects_empty_question():
    app.dependency_overrides[get_llm_service] = lambda: MockLLMService()

    try:
        response = client.post(
            "/qa/retrieve",
            json={
                "question": "   ",
                "top_k": 5,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Question cannot be empty"


def test_qa_retrieve_rejects_invalid_top_k():
    app.dependency_overrides[get_llm_service] = lambda: MockLLMService()

    try:
        response = client.post(
            "/qa/retrieve",
            json={
                "question": "What is the methodology?",
                "top_k": 0,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_qa_retrieve_rejects_excessive_top_k():
    app.dependency_overrides[get_llm_service] = lambda: MockLLMService()

    try:
        response = client.post(
            "/qa/retrieve",
            json={
                "question": "What is the methodology?",
                "top_k": 21,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_qa_retrieve_returns_insufficient_evidence():
    class MockLLMService:
        def generate(
            self,
            prompt,
            system_prompt=None,
            temperature=0.0,
        ):
            raise AssertionError(
                "LLM should not be called when retrieval returns no evidence"
            )

    mock_retriever = AsyncMock()
    mock_retriever.retrieve.return_value = []

    with patch(
        "backend.app.services.research_service.get_retriever",
        return_value=mock_retriever,
    ):
        app.dependency_overrides[get_llm_service] = (
            lambda: MockLLMService()
        )

        try:
            response = client.post(
                "/qa/retrieve",
                json={
                    "question": "What methodology was used?",
                    "top_k": 5,
                },
            )
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["evidence_sufficient"] is False
    assert data["citations"] == []


def test_research_service_returns_insufficient_evidence_when_retrieval_is_empty():
    mock_retriever = AsyncMock()
    mock_retriever.retrieve.return_value = []

    class MockLLMService:
        def generate(
            self,
            prompt,
            system_prompt=None,
            temperature=0.0,
        ):
            raise AssertionError(
                "LLM should not be called without evidence"
            )

    with patch(
        "backend.app.services.research_service.get_retriever",
        return_value=mock_retriever,
    ):
        service = ResearchService(MockLLMService())

        result = asyncio.run(
            service.answer_question(
                question="What is the methodology?",
                top_k=5,
            )
        )

    assert result.evidence_sufficient is False
    assert result.citations == []
