from __future__ import annotations

import argparse
import json
from pathlib import Path

from .db import build_database, save_db_json, load_db_json
from .match import match_against_db


def cmd_build_db(args: argparse.Namespace) -> int:
    db = build_database(Path(args.dataset), workers=args.workers)
    save_db_json(db, Path(args.out))
    print(f"OK: DB salvo em {args.out} (items={len(db.get('items', []))})")
    return 0


def cmd_match(args: argparse.Namespace) -> int:
    db = load_db_json(Path(args.db))
    res = match_against_db(db, Path(args.input), topk=args.topk)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="qext", description="JPEG quantization fingerprint toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_db = sub.add_parser("build-db", help="Varre dataset e gera quant_db.json")
    p_db.add_argument("--dataset", required=True, help="Pasta dataset/<software>/*.jpg")
    p_db.add_argument("--out", required=True, help="Arquivo JSON de saida")
    p_db.add_argument("--workers", type=int, default=4, help="Threads para acelerar extracao")
    p_db.set_defaults(func=cmd_build_db)

    p_m = sub.add_parser("match", help="Compara um JPEG contra o DB")
    p_m.add_argument("--db", required=True, help="quant_db.json")
    p_m.add_argument("--input", required=True, help="JPEG alvo")
    p_m.add_argument("--topk", type=int, default=10)
    p_m.set_defaults(func=cmd_match)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))
