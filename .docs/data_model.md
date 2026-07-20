# data_model.md: Database & Storage Model

## 1. SQLite Auth Database (storage/auth.db)
### Table: users
| Column         | Type    | Description                              | Constraints                  |
|----------------|---------|--------------------------------------|----------------------------|
| user_id        | TEXT    | Unique user identifier (primary key)        | PRIMARY KEY                |
| email          | TEXT    | User's email address (unique)           | UNIQUE, NOT NULL          |
| display_name   | TEXT    | Display name (defaults to email local part    | NULLABLE                  |
| created_at     | TEXT    | ISO 8601 UTC timestamp of account creation | NOT NULL                 |
| last_login     | TEXT    | ISO 8601 UTC timestamp of last login | NULLABLE                  |

### Table: sessions
| Column         | Type    | Description                              | Constraints                  |
|----------------|---------|--------------------------------------|----------------------------|
| session_id     | TEXT    | Unique session identifier (primary key)       | PRIMARY KEY                |
| user_id        | TEXT    | Foreign key to users.user_id                | FOREIGN KEY, NOT NULL         |
| created_at     | TEXT    | ISO 8601 UTC timestamp of session creation | NOT NULL                 |
| expires_at     | TEXT    | ISO 8601 UTC timestamp of session expiration | NOT NULL                 |
| is_active      | INTEGER | 1 = active, 0 = revoked                | DEFAULT 1, NOT NULL          |

### Table: magic_tokens
| Column         | Type    | Description                              | Constraints                  |
|----------------|---------|--------------------------------------|----------------------------|
| token          | TEXT    | Magic link token (primary key)           | PRIMARY KEY                |
| email          | TEXT    | Email address the token is for            | NOT NULL                 |
| created_at     | TEXT    | ISO 8601 UTC timestamp of token creation | NOT NULL                 |
| expires_at     | TEXT    | ISO 8601 UTC timestamp of token expiration | NOT NULL                 |
| used           | INTEGER | 1 = used, 0 = unused                  | DEFAULT 0, NOT NULL          |

## 2. FAISS Vector Storage Layout (storage/)
```
storage/
├── auth.db          # SQLite auth database
└── users/
    └── {user_id}/
        └── memory/
            └── {context_id}/
                ├── index.faiss     # FAISS HNSW index file
                └── metadata.pkl    # Pickled list of metadata entries
```

## 3. FAISS Metadata Entry Schema
Each entry in metadata.pkl is a dictionary with:
```python
{
    "chunk_index": int,          # Position in FAISS index
    "text": str,                # Chunked text
    "metadata": {
        "doc_id": str,             # Unique document ID (hash of source and content)
        "source": str,             # Source filename/URL
        "timestamp": str,           # ISO 8601 UTC timestamp
        # Optional extra metadata (type, mode, etc.)
    }
}
```

## 4. Row-Level Security Rules (Enforced)
- **All storage/memory isolation**: Every FAISS operation (add/search/delete uses user_id as directory prefix; user A cannot access user B's files
- **Session validation**: All API endpoints use require valid session_id (core/auth/middleware.py checks session_id)
- **No cross-user queries**: No way to query or modify another user's data at any level
