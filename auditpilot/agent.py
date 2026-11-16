"""
Root audit lead agent and sequential execution pipeline for AuditPilot.
"""

from google.adk.agents import SequentialAgent
from auditpilot.agents.intake import intake_agent

# Lead audit pipeline orchestrating sequential multi-agent execution
audit_lead = SequentialAgent(
    name="audit_lead",
    description="Lead Audit Pipeline Agent for Sahyadri Precision Components Pvt. Ltd.",
    sub_agents=[intake_agent],
)

# Root agent entry point for ADK Web UI and CLI runners
root_agent = audit_lead
