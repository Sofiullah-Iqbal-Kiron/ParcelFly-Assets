"""Parcel Fly brand kit generator.

Everything in the kit is generated from three sources of truth:
  - pfbrand.brand     colours, contact details, taglines, sub-brands
  - pfbrand.symbol    the measured geometry of the Parcel Fly symbol
  - source/master/    the outlined wordmark artwork (Nasalization, fixed artwork)
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]          # brand-assets/
SOURCE = ROOT / "source"
FONTS = SOURCE / "fonts"
MASTER = SOURCE / "master"
