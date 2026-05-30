"""Phase 1 backend services for the Gaia/IAG platform.

The modules in this package are intentionally deterministic and side-effect
light. They provide the stable analysis contract that the React frontend and
future API layer can call without depending on Streamlit session state.
"""

from core.phase1.service import Phase1Analyzer

__all__ = ["Phase1Analyzer"]
