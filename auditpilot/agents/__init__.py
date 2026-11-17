"""
AuditPilot multi-agent definitions.
"""

from auditpilot.agents.anomaly import anomaly_agent
from auditpilot.agents.intake import intake_agent
from auditpilot.agents.policy import policy_agent
from auditpilot.agents.ratio import ratio_agent
from auditpilot.agents.risk import risk_agent
from auditpilot.agents.vendor import vendor_agent

__all__ = [
    "intake_agent",
    "anomaly_agent",
    "vendor_agent",
    "ratio_agent",
    "policy_agent",
    "risk_agent",
]
