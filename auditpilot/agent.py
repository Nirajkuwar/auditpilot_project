"""
Root audit lead agent and sequential/parallel execution pipeline for AuditPilot.
"""

from google.adk.agents import ParallelAgent, SequentialAgent
from auditpilot.agents.anomaly import anomaly_agent
from auditpilot.agents.intake import intake_agent
from auditpilot.agents.policy import policy_agent
from auditpilot.agents.ratio import ratio_agent
from auditpilot.agents.report import report_agent
from auditpilot.agents.risk import risk_agent
from auditpilot.agents.skeptic import skeptic_agent, skeptic_loop
from auditpilot.agents.vendor import vendor_agent
from auditpilot.callbacks import after_tool_audit_logger, before_model_guardrail, pipeline_guard

# Attach security guardrails (bank account masking) and provenance audit logging callbacks
ALL_AUDIT_LLM_AGENTS = [
    intake_agent,
    anomaly_agent,
    vendor_agent,
    ratio_agent,
    policy_agent,
    risk_agent,
    skeptic_agent,
    report_agent,
]

for agent in ALL_AUDIT_LLM_AGENTS:
    agent.before_model_callback = before_model_guardrail
    agent.after_tool_callback = after_tool_audit_logger

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
# 5. report_agent (synthesizes audit memorandum in docs/audit_memo.md and manages partner sign-off)
audit_lead = SequentialAgent(
    name="audit_lead",
    description="Lead Audit Pipeline Agent for Sahyadri Precision Components Pvt. Ltd.",
    sub_agents=[intake_agent, specialists, risk_agent, skeptic_loop, report_agent],
)

# Root agent entry point for ADK Web UI and CLI runners
root_agent = audit_lead
