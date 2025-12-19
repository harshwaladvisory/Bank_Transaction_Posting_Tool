# -*- coding: utf-8 -*-
"""
ChromaDB-based Learning Store

Stores transaction patterns and enables similarity search for GL code suggestions.
All data stays LOCAL - no external API calls for banking data security.

Features:
- Vector embedding for transaction descriptions
- Similarity search to find matching past transactions
- Learning from user corrections
- Pattern export/import for backup
"""

import os
import re
import sys
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

# Add custom library path for Windows systems with long path issues
if 'C:\\py_libs' not in sys.path:
    sys.path.insert(0, 'C:\\py_libs')

# Try to import ChromaDB and sentence-transformers
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("[WARNING] chromadb not installed. Run: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDER_AVAILABLE = True
except ImportError:
    EMBEDDER_AVAILABLE = False
    print("[WARNING] sentence-transformers not installed. Run: pip install sentence-transformers")


class ChromaLearningStore:
    """
    ChromaDB-based learning store for transaction patterns.

    Stores transaction descriptions as vector embeddings and enables
    similarity search to suggest GL codes based on past transactions.

    Usage:
        store = ChromaLearningStore()

        # Learn from a transaction
        store.learn_transaction(
            description="HUD TREAS NAHASDA",
            gl_code="3001",
            transaction_type="deposit",
            module="CR",
            bank_name="PNC"
        )

        # Get suggestions for new transaction
        suggestions = store.suggest_gl_code("HUD TREASURY PAYMENT")
        # Returns: [{'gl_code': '3001', 'confidence': 92.5, ...}]
    """

    def __init__(self, persist_directory: str = None):
        """
        Initialize ChromaDB with persistent storage.

        Args:
            persist_directory: Path for ChromaDB storage. Defaults to data/chroma_db/
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb package not installed. Run: pip install chromadb")

        # Set default persist directory
        if persist_directory is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            persist_directory = os.path.join(base_dir, 'data', 'chroma_db')

        # Create persist directory if needed
        os.makedirs(persist_directory, exist_ok=True)

        self.persist_directory = persist_directory

        # Initialize ChromaDB with persistence
        try:
            # Try new ChromaDB API first (v0.4+)
            self.client = chromadb.PersistentClient(path=persist_directory)
        except (TypeError, AttributeError):
            # Fall back to old API (v0.3.x)
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_directory,
                anonymized_telemetry=False
            ))

        # Create or get collections
        self.transactions = self.client.get_or_create_collection(
            name="transaction_patterns",
            metadata={"description": "Learned transaction to GL code mappings"}
        )

        self.bank_formats = self.client.get_or_create_collection(
            name="bank_formats",
            metadata={"description": "Learned bank statement formats"}
        )

        # Initialize embedding model (runs locally, free!)
        self.embedder = None
        if EMBEDDER_AVAILABLE:
            try:
                # Use a small, fast model for embeddings
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                print(f"[INFO] Embedding model loaded: all-MiniLM-L6-v2")
            except Exception as e:
                print(f"[WARNING] Failed to load embedding model: {e}")

        pattern_count = self.transactions.count()
        print(f"[INFO] ChromaDB initialized with {pattern_count} learned patterns")

    def embed_text(self, text: str) -> List[float]:
        """
        Convert text to vector embedding.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if self.embedder is None:
            # Fallback: simple hash-based pseudo-embedding
            return self._simple_embedding(text)

        return self.embedder.encode(text).tolist()

    def _simple_embedding(self, text: str) -> List[float]:
        """
        Simple fallback embedding when sentence-transformers not available.
        Uses character frequencies and word hashing.
        """
        import hashlib

        text = text.upper()

        # Character frequency features (26 letters + 10 digits)
        char_freq = [0.0] * 36
        for c in text:
            if 'A' <= c <= 'Z':
                char_freq[ord(c) - ord('A')] += 1
            elif '0' <= c <= '9':
                char_freq[26 + ord(c) - ord('0')] += 1

        # Normalize
        total = sum(char_freq) or 1
        char_freq = [f / total for f in char_freq]

        # Word hash features
        words = text.split()
        word_hashes = []
        for word in words[:10]:  # First 10 words
            h = int(hashlib.md5(word.encode()).hexdigest()[:8], 16)
            word_hashes.append((h % 1000) / 1000.0)

        # Pad to consistent length
        while len(word_hashes) < 10:
            word_hashes.append(0.0)

        # Combine features
        embedding = char_freq + word_hashes[:10]

        # Pad to 384 dimensions to match MiniLM
        while len(embedding) < 384:
            embedding.append(0.0)

        return embedding[:384]

    # ═══════════════════════════════════════════════════════════════
    # LEARNING: Store patterns from user actions
    # ═══════════════════════════════════════════════════════════════

    def learn_transaction(self, description: str, gl_code: str,
                         transaction_type: str, module: str,
                         bank_name: str, amount: float = None,
                         user_corrected: bool = False) -> str:
        """
        Store a transaction pattern for future matching.
        Called when user approves or corrects a GL code.

        Args:
            description: Transaction description
            gl_code: Assigned GL code
            transaction_type: 'deposit' or 'withdrawal'
            module: 'CR', 'CD', or 'JV'
            bank_name: Name of the bank
            amount: Transaction amount (optional)
            user_corrected: True if user changed the suggestion

        Returns:
            Document ID for the stored pattern
        """
        # Clean description for better matching
        clean_desc = self._clean_description(description)

        if not clean_desc:
            return None

        # Create embedding
        embedding = self.embed_text(clean_desc)

        # Generate unique ID
        doc_id = f"txn_{uuid.uuid4().hex[:12]}"

        # Store in ChromaDB
        self.transactions.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[clean_desc],
            metadatas=[{
                "gl_code": str(gl_code),
                "transaction_type": transaction_type,
                "module": module,
                "bank": bank_name,
                "original_description": description[:200],
                "amount_range": self._get_amount_range(amount) if amount else "unknown",
                "user_corrected": user_corrected,
                "learned_at": datetime.now().isoformat(),
                "match_count": 0
            }]
        )

        # Persist (for older ChromaDB versions)
        try:
            self.client.persist()
        except AttributeError:
            pass  # Newer versions auto-persist

        print(f"[INFO] Learned: '{clean_desc[:40]}...' -> GL {gl_code}")
        return doc_id

    def learn_batch(self, transactions: List[Dict]) -> int:
        """
        Learn from multiple transactions at once (faster).

        Args:
            transactions: List of transaction dicts with keys:
                - description, gl_code, type, module, bank

        Returns:
            Number of patterns learned
        """
        if not transactions:
            return 0

        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for txn in transactions:
            clean_desc = self._clean_description(txn.get('description', ''))
            if not clean_desc:
                continue

            ids.append(f"txn_{uuid.uuid4().hex[:12]}")
            embeddings.append(self.embed_text(clean_desc))
            documents.append(clean_desc)
            metadatas.append({
                "gl_code": str(txn.get('gl_code', '')),
                "transaction_type": txn.get('type', 'unknown'),
                "module": txn.get('module', 'unknown'),
                "bank": txn.get('bank', 'unknown'),
                "original_description": txn.get('description', '')[:200],
                "learned_at": datetime.now().isoformat(),
                "match_count": 0
            })

        if ids:
            self.transactions.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

            try:
                self.client.persist()
            except AttributeError:
                pass

        print(f"[INFO] Learned {len(ids)} transaction patterns")
        return len(ids)

    # ═══════════════════════════════════════════════════════════════
    # SUGGESTION: Find similar transactions and suggest GL codes
    # ═══════════════════════════════════════════════════════════════

    def suggest_gl_code(self, description: str,
                       transaction_type: str = None,
                       bank_name: str = None,
                       n_results: int = 5) -> List[Dict]:
        """
        Find similar past transactions and suggest GL code.

        Args:
            description: Transaction description to match
            transaction_type: Filter by 'deposit' or 'withdrawal'
            bank_name: Filter by bank name
            n_results: Number of suggestions to return

        Returns:
            List of suggestions with confidence scores:
            [{
                'gl_code': '3001',
                'module': 'CR',
                'confidence': 92.5,
                'confidence_level': 'high',
                'matched_description': 'HUD TREAS NAHASDA',
                'bank': 'PNC'
            }, ...]
        """
        if self.transactions.count() == 0:
            return []

        # Clean and embed the input
        clean_desc = self._clean_description(description)
        if not clean_desc:
            return []

        embedding = self.embed_text(clean_desc)

        # Build filter conditions
        where_filter = None
        if transaction_type:
            where_filter = {"transaction_type": transaction_type}

        # Search ChromaDB
        try:
            results = self.transactions.query(
                query_embeddings=[embedding],
                n_results=min(n_results, self.transactions.count()),
                where=where_filter
            )
        except Exception as e:
            print(f"[ERROR] ChromaDB query failed: {e}")
            return []

        # Process results
        suggestions = []
        if results and results.get('documents') and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                # Convert distance to similarity (0-100 scale)
                distance = results['distances'][0][i] if results.get('distances') else 0

                # ChromaDB uses L2 distance by default
                # Convert to similarity percentage
                similarity = max(0, 100 * (1 - distance / 2))

                metadata = results['metadatas'][0][i]

                suggestions.append({
                    'gl_code': metadata.get('gl_code', ''),
                    'module': metadata.get('module', 'unknown'),
                    'confidence': round(similarity, 1),
                    'confidence_level': self._get_confidence_level(similarity / 100),
                    'matched_description': doc,
                    'original_description': metadata.get('original_description', doc),
                    'bank': metadata.get('bank', 'unknown'),
                    'match_count': metadata.get('match_count', 0),
                    'user_corrected': metadata.get('user_corrected', False)
                })

        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)

        return suggestions

    def get_best_suggestion(self, description: str,
                           transaction_type: str = None,
                           min_confidence: float = 60) -> Optional[Dict]:
        """
        Get single best GL code suggestion if confidence is high enough.

        Args:
            description: Transaction description
            transaction_type: 'deposit' or 'withdrawal'
            min_confidence: Minimum confidence threshold (0-100)

        Returns:
            Best suggestion dict or None if no good match
        """
        suggestions = self.suggest_gl_code(
            description,
            transaction_type=transaction_type,
            n_results=3
        )

        if suggestions and suggestions[0]['confidence'] >= min_confidence:
            best = suggestions[0]
            return {
                'gl_code': best['gl_code'],
                'module': best['module'],
                'confidence': best['confidence'],
                'confidence_level': best['confidence_level'],
                'reason': f"Similar to: {best['matched_description'][:50]}..."
            }

        return None

    # ═══════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════

    def _clean_description(self, description: str) -> str:
        """
        Clean transaction description for better matching.
        Removes noise like reference numbers, dates, etc.
        """
        if not description:
            return ''

        # Convert to uppercase
        cleaned = description.upper()

        # Remove reference numbers (long digit sequences)
        cleaned = re.sub(r'\b\d{8,}\b', '', cleaned)

        # Remove dates
        cleaned = re.sub(r'\b\d{1,2}/\d{1,2}(/\d{2,4})?\b', '', cleaned)

        # Remove special characters but keep spaces
        cleaned = re.sub(r'[^\w\s]', ' ', cleaned)

        # Remove common noise words
        noise_words = ['THE', 'FOR', 'AND', 'FROM', 'TO', 'OF', 'IN', 'ON', 'AT']
        words = cleaned.split()
        words = [w for w in words if w not in noise_words and len(w) > 1]

        # Normalize whitespace
        cleaned = ' '.join(words)

        return cleaned.strip()

    def _get_confidence_level(self, similarity: float) -> str:
        """Convert similarity score (0-1) to confidence level."""
        if similarity >= 0.85:
            return "high"
        elif similarity >= 0.70:
            return "medium"
        elif similarity >= 0.50:
            return "low"
        else:
            return "none"

    def _get_amount_range(self, amount: float) -> str:
        """Categorize amount into ranges for filtering."""
        if amount is None:
            return "unknown"
        amount = abs(amount)
        if amount < 100:
            return "small"
        elif amount < 1000:
            return "medium"
        elif amount < 10000:
            return "large"
        else:
            return "very_large"

    # ═══════════════════════════════════════════════════════════════
    # STATISTICS & REPORTING
    # ═══════════════════════════════════════════════════════════════

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get learning statistics.

        Returns:
            Dictionary with pattern counts, GL code distribution, etc.
        """
        count = self.transactions.count()

        if count == 0:
            return {
                'total_patterns': 0,
                'status': 'empty - needs training data',
                'gl_code_distribution': {},
                'bank_distribution': {}
            }

        # Get sample to analyze
        try:
            sample = self.transactions.get(limit=min(count, 500))
        except Exception:
            sample = self.transactions.peek(min(count, 100))

        gl_codes = {}
        banks = {}
        user_corrected = 0

        for meta in sample.get('metadatas', []):
            gl = meta.get('gl_code', 'unknown')
            bank = meta.get('bank', 'unknown')

            gl_codes[gl] = gl_codes.get(gl, 0) + 1
            banks[bank] = banks.get(bank, 0) + 1

            if meta.get('user_corrected'):
                user_corrected += 1

        return {
            'total_patterns': count,
            'gl_code_distribution': gl_codes,
            'bank_distribution': banks,
            'user_corrected_count': user_corrected,
            'status': 'active'
        }

    def export_patterns(self, filepath: str) -> int:
        """
        Export all learned patterns to JSON file.

        Args:
            filepath: Path to save JSON file

        Returns:
            Number of patterns exported
        """
        all_data = self.transactions.get()

        patterns = []
        for i, doc in enumerate(all_data.get('documents', [])):
            patterns.append({
                'description': doc,
                'metadata': all_data['metadatas'][i]
            })

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, indent=2, default=str)

        print(f"[INFO] Exported {len(patterns)} patterns to {filepath}")
        return len(patterns)

    def import_patterns(self, filepath: str) -> int:
        """
        Import patterns from JSON file (for backup/restore).

        Args:
            filepath: Path to JSON file

        Returns:
            Number of patterns imported
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            patterns = json.load(f)

        count = 0
        for pattern in patterns:
            meta = pattern.get('metadata', {})
            self.learn_transaction(
                description=pattern.get('description', ''),
                gl_code=meta.get('gl_code', ''),
                transaction_type=meta.get('transaction_type', 'unknown'),
                module=meta.get('module', 'unknown'),
                bank_name=meta.get('bank', 'unknown')
            )
            count += 1

        print(f"[INFO] Imported {count} patterns from {filepath}")
        return count

    def clear_all(self) -> int:
        """
        Clear all learned patterns. USE WITH CAUTION!

        Returns:
            Number of patterns deleted
        """
        count = self.transactions.count()

        if count > 0:
            # Delete collection and recreate
            self.client.delete_collection("transaction_patterns")
            self.transactions = self.client.get_or_create_collection(
                name="transaction_patterns",
                metadata={"description": "Learned transaction to GL code mappings"}
            )

        print(f"[WARNING] Cleared {count} learned patterns")
        return count


# ═══════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════

_store_instance = None

def get_chroma_store() -> ChromaLearningStore:
    """
    Get singleton ChromaDB store instance.

    Returns:
        ChromaLearningStore instance
    """
    global _store_instance
    if _store_instance is None:
        _store_instance = ChromaLearningStore()
    return _store_instance


# ═══════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test the ChromaDB store
    print("=" * 60)
    print("Testing ChromaDB Learning Store")
    print("=" * 60)

    store = get_chroma_store()

    # Check stats
    stats = store.get_statistics()
    print(f"\nCurrent Statistics:")
    print(f"  Total patterns: {stats['total_patterns']}")
    print(f"  Status: {stats['status']}")

    # Add some test patterns
    print("\nAdding test patterns...")
    store.learn_transaction(
        description="HUD TREAS NAHASDA GRANT PAYMENT",
        gl_code="3001",
        transaction_type="deposit",
        module="CR",
        bank_name="PNC"
    )

    store.learn_transaction(
        description="BLUE CROSS BCBS HEALTHCARE PREMIUM",
        gl_code="4080",
        transaction_type="deposit",
        module="CR",
        bank_name="PNC"
    )

    store.learn_transaction(
        description="INTUIT PAYROLL SERVICES",
        gl_code="6601",
        transaction_type="withdrawal",
        module="CD",
        bank_name="PNC"
    )

    # Test suggestions
    print("\nTesting GL code suggestions...")

    test_descriptions = [
        "HUD TREASURY PAYMENT FOR HOUSING",
        "BCBS HEALTH INSURANCE CONTRIBUTION",
        "QUICKBOOKS PAYROLL DIRECT DEPOSIT"
    ]

    for desc in test_descriptions:
        suggestions = store.suggest_gl_code(desc, n_results=3)
        print(f"\n  '{desc[:40]}...'")
        if suggestions:
            best = suggestions[0]
            print(f"    -> GL {best['gl_code']} ({best['confidence']:.1f}% confidence)")
            print(f"       Matched: {best['matched_description'][:40]}...")
        else:
            print("    -> No match found")

    # Final stats
    stats = store.get_statistics()
    print(f"\nFinal Statistics:")
    print(f"  Total patterns: {stats['total_patterns']}")
    print(f"  GL codes: {stats['gl_code_distribution']}")
    print(f"  Banks: {stats['bank_distribution']}")
