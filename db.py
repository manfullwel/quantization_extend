from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from tqdm import tqdm

from .extract import extract_jpeg_meta, extract_qtables, qhash_from_tables
from .utils import sha256_file


QUALITY_RE = re.compile(r"(\d+)")


def infer_quality_from_filename(name: str) -> Optional[int]:
    """Extrai o primeiro numero do nome do arquivo como quality.

    Ex:
      "90.jpg" -> 90
      "quality_95.jpg" -> 95
    """
    m = QUALITY_RE.search(name)
    if not m:
        return None
    try:
        q = int(m.group(1))
        if 0 <= q <= 1000:
            return q
    except Exception:
        return None
    return None


def _process_one(sw: str, p: Path) -> Dict[str, Any]:
    """Processa uma imagem e devolve um registro pronto para DB."""
    quality = infer_quality_from_filename(p.name)
    qtables = extract_qtables(p)
    qhash = qhash_from_tables(qtables)
    meta = extract_jpeg_meta(p)

    return {
        "software": sw,
        "filename": p.name,
        "path": str(p.resolve()),
        "sha256": sha256_file(p),
        "quality": quality,
        "qtables": qtables,
        "qhash": qhash,
        "jpeg_meta": asdict(meta),
    }


def build_database(dataset_dir: Path, workers: int = 1) -> Dict[str, Any]:
    """Varre dataset_dir/<software>/*.jpg e monta um DB auditavel.

    Parametros:
      - workers: numero de threads para processar JPEGs (I/O + parse). Use 4-16 para lotes grandes.
    """
    dataset_dir = Path(dataset_dir)
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset nao encontrado: {dataset_dir}")

    db: Dict[str, Any] = {
        "schema": "qext.quantdb.v1",
        "dataset_root": str(dataset_dir.resolve()),
        "items": [],
    }

    software_dirs = [p for p in dataset_dir.iterdir() if p.is_dir()]
    for sw_dir in software_dirs:
        sw = sw_dir.name
        jpgs = sorted([p for p in sw_dir.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg"}])

        if workers <= 1:
            for p in tqdm(jpgs, desc=f"[{sw}]", unit="img"):
                db["items"].append(_process_one(sw, p))
        else:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futs = [ex.submit(_process_one, sw, p) for p in jpgs]
                for fut in tqdm(as_completed(futs), total=len(futs), desc=f"[{sw}]", unit="img"):
                    db["items"].append(fut.result())

    return db


def save_db_json(db: Dict[str, Any], out_path: Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")


def load_db_json(path: Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
