from __future__ import annotations

from sqlalchemy.sql import Select, text


def apply_fulltext_search(query: Select, search_text: str) -> Select:
    # Предполагается, что миграция создала GIN-индекс
    # Используем plainto_tsquery для преобразования вводимых слов
    return query.filter(
        text(
            "to_tsvector('russian', title || ' ' || content) @@ plainto_tsquery('russian', :search)"
        )
    ).params(search=search_text)
