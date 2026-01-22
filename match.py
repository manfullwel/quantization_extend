from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .extract import extract_qtables, qhash_from_tables
from .db import load_db_json
from .utils import sha256_file


@dataclass
class MatchHit:
    software: str
    quality: Optional[int]
    filename: str
    sha256: str
    score: float


def match_against_db(db: Dict[str, Any], input_path: Path, topk: int = 10) -> Dict[str, Any]:
    """Match por igualdade de qhash (Y e/ou C).

    score:
      - 1.0 match perfeito Y+C
      - 0.7 match so Y
      - 0.6 match so C
    """
    input_path = Path(input_path)
    qtables = extract_qtables(input_path)
    qhash = qhash_from_tables(qtables)

    hits: List[MatchHit] = []

    for it in db.get("items", []):
        it_q = it.get("qhash", {})
        y_ok = ("Y" in qhash and it_q.get("Y") == qhash.get("Y"))
        c_ok = ("C" in qhash and it_q.get("C") == qhash.get("C"))

        if not (y_ok or c_ok):
            continue

        if y_ok and c_ok:
            score = 1.0
        elif y_ok:
            score = 0.7
        else:
            score = 0.6

        hits.append(
            MatchHit(
                software=it.get("software", "?"),
                quality=it.get("quality"),
                filename=it.get("filename", "?"),
                sha256=it.get("sha256", "?"),
                score=score,
            )
        )

    hits.sort(key=lambda x: (-x.score, x.software, (x.quality or 10**9)))
    hits = hits[:topk]

    return {
        "input": {
            "path": str(input_path.resolve()),
            "sha256": sha256_file(input_path),
            "qhash": qhash,
        },
        "hits": [h.__dict__ for h in hits],
        "notes": [
            "Match baseado em igualdade de tabela de quantizacao (fingerprint forte, mas nao prova absoluta).",
            "Para laudo: documente encoder family, subsampling/progressive, e cadeias de custodia.",
        ],
    }


def match_db_file(db_json_path: Path, input_path: Path, topk: int = 10) -> Dict[str, Any]:
    db = load_db_json(db_json_path)
    return match_against_db(db, input_path=input_path, topk=topk)
