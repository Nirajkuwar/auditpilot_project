"""
AuditPilot package initialization.
Loads environment configuration and provides top-level exports.
"""

from pathlib import Path
from dotenv import load_dotenv

# Automatically load environment variables (.env from workspace root or package directory)
_root_env = Path(__file__).resolve().parent.parent / ".env"
_pkg_env = Path(__file__).resolve().parent / ".env"

if _root_env.exists():
    load_dotenv(_root_env)
elif _pkg_env.exists():
    load_dotenv(_pkg_env)

from .agent import audit_lead, root_agent

__all__ = ["audit_lead", "root_agent"]
