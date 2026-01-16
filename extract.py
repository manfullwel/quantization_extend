from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from PIL import Image

from .utils import sha256_text, flatten_8x8


@dataclass(frozen=True)
class JPEGMeta:
    progressive: Optional[bool] = None
    subsampling: Optional[str] = None  # "444" | "422" | "420" | None
    width: Optional[int] = None
    height: Optional[int] = None


def _read_be_u16(b: bytes, off: int) -> int:
    return (b[off] << 8) | b[off + 1]


def extract_jpeg_meta(jpeg_path: Path) -> JPEGMeta:
    """Extrai metadados relevantes lendo marcadores JPEG (SOF0/SOF2).

    Nao depende de bibliotecas externas.
    """
    data = jpeg_path.read_bytes()
    if len(data) < 4 or data[0:2] != b"\xFF\xD8":
        return JPEGMeta()

    i = 2
    progressive = None
    width = height = None
    subsampling = None

    while i + 4 <= len(data):
        # procurar 0xFF marker prefix
        if data[i] != 0xFF:
            i += 1
            continue

        # pular FFs de padding
        while i < len(data) and data[i] == 0xFF:
            i += 1
        if i >= len(data):
            break

        marker = data[i]
        i += 1

        # SOI/EOI sem length
        if marker in (0xD8, 0xD9):
            continue

        if i + 2 > len(data):
            break
        seg_len = _read_be_u16(data, i)
        i += 2
        if seg_len < 2 or i + (seg_len - 2) > len(data):
            break

        seg = data[i : i + (seg_len - 2)]
        i += seg_len - 2

        # SOF0 baseline, SOF2 progressive
        if marker in (0xC0, 0xC2) and len(seg) >= 6:
            progressive = marker == 0xC2
            # seg layout: P(1), Y(2), X(2), Nf(1), then components
            height = _read_be_u16(seg, 1)
            width = _read_be_u16(seg, 3)
            nf = seg[5]

            # components: id(1), sampling(1), qtid(1)
            # sampling: high nibble = H, low nibble = V
            comps = []
            base = 6
            for _ in range(nf):
                if base + 3 > len(seg):
                    break
                cid = seg[base]
                samp = seg[base + 1]
                h_s = (samp >> 4) & 0x0F
                v_s = samp & 0x0F
                comps.append((cid, h_s, v_s))
                base += 3

            # heuristic subsampling from Y vs chroma sampling factors
            # Y is usually component id 1
            y = next((c for c in comps if c[0] == 1), None)
            cb = next((c for c in comps if c[0] == 2), None)
            if y and cb:
                y_h, y_v = y[1], y[2]
                cb_h, cb_v = cb[1], cb[2]
                if (y_h, y_v) == (1, 1) and (cb_h, cb_v) == (1, 1):
                    subsampling = "444"
                elif (y_h, y_v) == (2, 1) and (cb_h, cb_v) == (1, 1):
                    subsampling = "422"
                elif (y_h, y_v) == (2, 2) and (cb_h, cb_v) == (1, 1):
                    subsampling = "420"

            # ja achamos o SOF, pode sair
            break

    return JPEGMeta(progressive=progressive, subsampling=subsampling, width=width, height=height)


def extract_qtables(jpeg_path: Path) -> Dict[str, Any]:
    """Extrai tabelas de quantizacao via Pillow.

    Retorna estrutura:
      {
        "Y": [[8x8]],
        "Cb": [[8x8]] (se existir),
        "Cr": [[8x8]] (normalmente igual a Cb)
      }

    Observacao: Pillow expose qtables por indice (0=luma, 1=chroma).
    """
    img = Image.open(jpeg_path)
    qtables = getattr(img, "quantization", None)
    if not qtables:
        return {}

    out: Dict[str, Any] = {}
    if 0 in qtables:
        out["Y"] = np.array(qtables[0], dtype=np.int32).reshape((8, 8)).tolist()
    if 1 in qtables:
        chroma = np.array(qtables[1], dtype=np.int32).reshape((8, 8)).tolist()
        out["Cb"] = chroma
        out["Cr"] = chroma
    return out


def qhash_from_tables(qtables: Dict[str, Any]) -> Dict[str, str]:
    """Gera fingerprint deterministico das tabelas.

    Usa SHA-256 do vetor 64 (string CSV) para Y e C.
    """
    h: Dict[str, str] = {}
    if "Y" in qtables:
        y_flat = flatten_8x8(qtables["Y"])
        h["Y"] = sha256_text(",".join(map(str, y_flat)))
    if "Cb" in qtables:
        c_flat = flatten_8x8(qtables["Cb"])
        h["C"] = sha256_text(",".join(map(str, c_flat)))
    return h
