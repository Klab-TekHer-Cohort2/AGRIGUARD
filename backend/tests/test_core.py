import pytest
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.core.database import check_database_connection
from app.core.neo4j_client import neo4j_client


def test_settings_loaded():
    """Verifies environment settings are properly initialized."""
    assert settings.PROJECT_NAME == "AgriGuard"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.upload_path.exists()


def test_password_hashing():
    """Verifies secure bcrypt password hashing and verification."""
    password = "FarmerSecretPassword2026!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_creation_and_decoding():
    """Verifies JWT token encoding and payload verification."""
    phone = "+250788123456"
    role = "FARMER"
    token = create_access_token(subject=phone, role=role)
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == phone
    assert payload["role"] == role


def test_database_connection():
    """Verifies relational database connection check."""
    status = check_database_connection()
    assert status["status"] == "connected"


def test_neo4j_knowledge_graph_symptom_reasoning():
    """
    Verifies that the Neo4j AI Knowledge Graph client
    correctly infers pest from reported symptoms.
    """
    reported_symptoms = ["caterpillar in whorl", "ragged leaf feeding holes"]
    inference = neo4j_client.infer_pest_from_symptoms("Maize", reported_symptoms, language="en")

    assert inference is not None
    assert "predicted_pest" in inference
    assert inference["predicted_pest"] == "Fall Armyworm"
    assert inference["severity"] == "HIGH"
    assert inference["confidence"] > 0.5
    assert len(inference["recommendations"]) > 0


def test_neo4j_knowledge_graph_kinyarwanda_reasoning():
    """
    Verifies Kinyarwanda language support in the knowledge graph.
    """
    reported_symptoms = ["amabara yirabura asa n'atose ku mababi"]
    inference = neo4j_client.infer_pest_from_symptoms("Ibirayi", reported_symptoms, language="rw")

    assert inference is not None
    assert inference["predicted_pest_rw"] == "Imvura y'Ibirayi"
    assert inference["severity"] == "CRITICAL"
