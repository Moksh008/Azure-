from app.embeddings.provider import (
    AzureOpenAIEmbeddingProvider,
    HashEmbeddingProvider,
)


def test_hash_embedding_provider():
    provider = HashEmbeddingProvider(vector_dim=64)
    vec1 = provider.embed("machine learning in healthcare")
    vec2 = provider.embed("machine learning in healthcare")
    vec3 = provider.embed("quantum physics and black holes")

    assert len(vec1) == 64
    assert vec1 == vec2  # Deterministic
    assert vec1 != vec3


def test_hash_embedding_batch():
    provider = HashEmbeddingProvider(vector_dim=32)
    texts = ["hello world", "fake news detection"]
    batch_vecs = provider.embed_batch(texts)

    assert len(batch_vecs) == 2
    assert len(batch_vecs[0]) == 32
    assert len(batch_vecs[1]) == 32


def test_azure_openai_embedding_provider_fallback():
    provider = AzureOpenAIEmbeddingProvider()
    vec = provider.embed("test text without credentials")
    assert len(vec) == 128
