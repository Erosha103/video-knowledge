"""Консольная база знаний по видео и моушн-графике."""

import argparse
import json
import sys
from pathlib import Path


DEFAULT_DIRECTORY = Path(__file__).resolve().parent / "cards"


def read_card(path):
    """Читает карточку и проверяет обязательные поля."""
    card = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(card, dict):
        raise ValueError("карточка должна быть объектом JSON")
    for field in ("title", "category", "description"):
        value = card.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"поле {field} должно содержать текст")
        card[field] = value.strip()
    tags = card.get("tags")
    if not isinstance(tags, list) or not tags or any(
        not isinstance(tag, str) or not tag.strip() for tag in tags
    ):
        raise ValueError("поле tags должно содержать список непустых тегов")
    card["tags"] = [tag.strip() for tag in tags]
    return card


def matches(card, query):
    text = " ".join(
        [card["title"], card["category"], card["description"], *card["tags"]]
    ).casefold()
    return all(word in text for word in query.casefold().split())


def print_fields(card_id, card):
    print(f"{card_id} | {card['title']} | {card['category']} | {', '.join(card['tags'])}")


def main():
    parser = argparse.ArgumentParser(description="База знаний видеопроизводства")
    parser.add_argument("--cards", type=Path, default=DEFAULT_DIRECTORY, help="папка с карточками JSON")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="показать список карточек")
    search = commands.add_parser("search", help="найти карточки по словам")
    search.add_argument("query", help="одно слово или несколько слов в кавычках")
    show = commands.add_parser("show", help="прочитать карточку")
    show.add_argument("id", help="идентификатор из первого столбца списка")
    args = parser.parse_args()

    if args.command == "search" and not args.query.strip():
        parser.error("поисковый запрос должен содержать хотя бы одно слово")
    try:
        paths = sorted(
            path for path in args.cards.iterdir() if path.is_file() and path.suffix == ".json"
        )
    except OSError as exc:
        print(f"Не удалось открыть папку карточек: {exc}", file=sys.stderr)
        return 1

    has_errors = False
    found = False
    for path in paths:
        if args.command == "show" and path.stem != args.id:
            continue
        try:
            card = read_card(path)
        except (OSError, ValueError) as exc:
            print(f"Ошибка в карточке {path.name}: {exc}", file=sys.stderr)
            has_errors = True
            continue
        if args.command == "search" and not matches(card, args.query):
            continue
        print_fields(path.stem, card)
        if args.command == "show":
            print(card["description"])
        found = True

    if args.command == "show" and not found and not has_errors:
        print(f"Карточка «{args.id}» не найдена.", file=sys.stderr)
        return 1
    if not found and not has_errors:
        print("Карточки не найдены." if args.command == "search" else "База знаний пуста.")
    return int(has_errors)


if __name__ == "__main__":
    sys.exit(main())
