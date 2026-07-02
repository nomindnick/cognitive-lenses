"""Lens registry: the configurable lens set. Add/drop lenses in
config/default.json; add new lens classes here."""
from __future__ import annotations

from .lens_delphi import DelphiLens
from .lens_dialectic import DialecticLens
from .lens_premortem import PremortemLens
from .lens_steelman import SteelmanLens
from .lens_structural import StructuralLens
from .lens_tetlock import TetlockLens

REGISTRY = {
    cls.name: cls
    for cls in (DelphiLens, TetlockLens, DialecticLens, PremortemLens,
                SteelmanLens, StructuralLens)
}


def build_lenses(cfg: dict) -> dict:
    """Instantiate the configured lens set: {name: Lens}."""
    out = {}
    for name, params in (cfg.get("lenses") or {}).items():
        if name not in REGISTRY:
            raise KeyError(f"unknown lens {name!r}; known: {sorted(REGISTRY)}")
        out[name] = REGISTRY[name](params or {})
    return out
