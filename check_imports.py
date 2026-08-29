"""Simple import check"""
import sys

print("Python version:", sys.version)
print("\nChecking imports...")

try:
    from langchain_community.vectorstores import Chroma
    print("✓ Chroma")
except Exception as e:
    print(f"❌ Chroma: {e}")

try:
    from langchain_community.retrievers import BM25Retriever
    print("✓ BM25Retriever")
except Exception as e:
    print(f"❌ BM25Retriever: {e}")

try:
    from langchain.retrievers import EnsembleRetriever
    print("✓ EnsembleRetriever")
except Exception as e:
    print(f"❌ EnsembleRetriever: {e}")

try:
    from langchain_community.cross_encoders import HuggingFaceCrossEncoder
    print("✓ HuggingFaceCrossEncoder")
except Exception as e:
    print(f"❌ HuggingFaceCrossEncoder: {e}")

try:
    from langchain.retrievers.document_compressors import CrossEncoderReranker
    print("✓ CrossEncoderReranker")
except Exception as e:
    print(f"❌ CrossEncoderReranker: {e}")

try:
    import rank_bm25
    print("✓ rank_bm25")
except Exception as e:
    print(f"❌ rank_bm25: {e}")

print("\nDone!")
