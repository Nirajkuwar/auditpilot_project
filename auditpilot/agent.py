"""
Root audit lead agent and sequential/parallel execution pipeline for AuditPilot.
"""

from google.adk.agents import ParallelAgent, SequentialAgent
from auditpilot.agents.anomaly import anomaly_agent
from auditpilot.agents.intake import intake_agent
from auditpilot.agents.policy import policy_agent
from auditpilot.agents.ratio import ratio_agent
from auditpilot.agents.risk import risk_agent
from auditpilot.agents.skeptic import skeptic_loop
from auditpilot.agents.vendor import vendor_agent
from auditpilot.callbacks import pipeline_guard

# Parallel specialist group analyzing anomalies, vendor integrity, ratios, and policy compliance concurrently
specialists = ParallelAgent(
    name="specialists",
    description="Parallel specialist team analyzing pattern anomalies, vendor integrity, financial ratios, and policy compliance.",
    sub_agents=[anomaly_agent, vendor_agent, ratio_agent, policy_agent],
    before_agent_callback=pipeline_guard,
)

# Lead audit pipeline orchestrating sequential multi-agent execution:
# 1. intake_agent (validates dataset structure, halted by pipeline_guard if FAILED)
# 2. specialists (executes anomaly_agent, vendor_agent, ratio_agent, and policy_agent in parallel)
# 3. risk_agent (deduplicates, deterministically scores, and ranks all audit findings)
# 4. skeptic_loop (adversarial verification loop validating existence, corroborating evidence, filtering false positives)
audit_lead = SequentialAgent(
    name="audit_lead",
    description="Lead Audit Pipeline Agent for Sahyadri Precision Components Pvt. Ltd.",
    sub_agents=[intake_agent, specialists, risk_agent, skeptic_loop],
)

# Root agent entry point for ADK Web UI and CLI runners
root_agent = audit_lead
