"""Tests for the /deliverables/scaffold API route.

generate_mvp_scaffold() itself is covered in test_deliverables.py — this
file only covers the route that exposes it as a downloadable zip, which
previously didn't exist (DeliverablesPage.tsx said as much: "will be
exposed as a downloadable zip once a scaffold-download API route is
added").
"""

import io
import zipfile

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def _proposal_payload(**overrides) -> dict:
    defaults = dict(
        proposal_id="prop_1",
        title="Model Compression Toolkit",
        summary="Quantize and prune models to cut GPU memory usage.",
        source_opportunity_ids=["opp_1"],
        objectives=["Quantize weights"],
        proposed_methods=["BitsAndBytes quantization"],
        expected_outcomes=["Reproducible compression pipeline"],
        feasibility_notes="Looks doable with 2 people.",
        problem_statement="Large models are too expensive to run on consumer hardware.",
        technical_approach=["Python", "PyTorch"],
        key_features=["Quantization profiler"],
        paper_ids=["paper-1"],
        evidence=["Paper 2 reports OOM errors on consumer GPUs."],
        novelty_confidence="Requires human validation",
    )
    defaults.update(overrides)
    return defaults


def test_scaffold_route_returns_downloadable_zip_with_expected_files():
    response = client.post(
        "/deliverables/scaffold",
        json={"proposal": _proposal_payload()},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment; filename=" in response.headers["content-disposition"]

    archive = zipfile.ZipFile(io.BytesIO(response.content))
    names = set(archive.namelist())
    assert "README.md" in names
    assert "requirements.txt" in names
    assert "backend/app/main.py" in names

    readme = archive.read("README.md").decode("utf-8")
    assert "Model Compression Toolkit" in readme


def test_scaffold_route_includes_full_project_folder_tree():
    """Matches the vision doc's section 10 folder tree: backend/app/{api,
    agents, rag, models, services}, database/, tests/, docker-compose.yml,
    and frontend/src/{components,pages,services} — not just a flat
    README+requirements.txt+stub main.py."""
    response = client.post(
        "/deliverables/scaffold",
        json={"proposal": _proposal_payload()},
    )
    assert response.status_code == 200

    archive = zipfile.ZipFile(io.BytesIO(response.content))
    names = set(archive.namelist())

    for expected in [
        "backend/app/api/__init__.py",
        "backend/app/agents/__init__.py",
        "backend/app/rag/__init__.py",
        "backend/app/models/__init__.py",
        "backend/app/services/__init__.py",
        "database/README.md",
        "tests/test_health.py",
        "docker-compose.yml",
        "frontend/src/components/.gitkeep",
        "frontend/src/pages/.gitkeep",
        "frontend/src/services/.gitkeep",
    ]:
        assert expected in names, f"missing {expected}"


def test_scaffold_route_filename_is_slugified_from_title():
    response = client.post(
        "/deliverables/scaffold",
        json={"proposal": _proposal_payload(title="Édge Café: Realtime!! Sync")},
    )

    assert response.status_code == 200
    disposition = response.headers["content-disposition"]
    assert "-scaffold.zip" in disposition
    assert " " not in disposition.split("filename=")[1]
