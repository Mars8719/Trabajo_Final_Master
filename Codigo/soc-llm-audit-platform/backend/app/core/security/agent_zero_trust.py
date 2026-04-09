"""
Agent Zero Trust - Minimum privilege enforcement for LLM agents.
OWASP LLM Top 10: LLM06 (Excessive Agency).
"""
import structlog
from dataclasses import dataclass
from typing import Optional

logger = structlog.get_logger()


@dataclass
class AgentPermission:
    agent_id: str
    allowed_actions: list[str]
    denied_actions: list[str]
    max_tokens_per_request: int
    requires_hitl: bool
    risk_level: str


class AgentZeroTrust:
    """Enforces zero-trust principle for LLM agents."""

    DEFAULT_PERMISSIONS = {
        "triage_agent": AgentPermission(
            agent_id="triage_agent",
            allowed_actions=["classify_alert", "score_severity", "recommend_playbook"],
            denied_actions=["execute_playbook", "modify_rules", "access_pii", "delete_records"],
            max_tokens_per_request=4096,
            requires_hitl=False,
            risk_level="low",
        ),
        "playbook_agent": AgentPermission(
            agent_id="playbook_agent",
            allowed_actions=["recommend_playbook", "list_playbooks"],
            denied_actions=["execute_playbook", "modify_infrastructure", "access_pii"],
            max_tokens_per_request=2048,
            requires_hitl=True,
            risk_level="medium",
        ),
        "summary_agent": AgentPermission(
            agent_id="summary_agent",
            allowed_actions=["generate_summary", "read_anonymized_data"],
            denied_actions=["access_pii", "modify_records", "execute_commands"],
            max_tokens_per_request=8192,
            requires_hitl=False,
            risk_level="low",
        ),
    }

    def check_permission(self, agent_id: str, action: str) -> tuple[bool, str]:
        """Check if an agent has permission to perform an action."""
        perm = self.DEFAULT_PERMISSIONS.get(agent_id)
        if not perm:
            logger.warning("Unknown agent attempted action", agent_id=agent_id, action=action)
            return False, f"Unknown agent: {agent_id}"

        if action in perm.denied_actions:
            logger.warning("Agent action denied", agent_id=agent_id, action=action)
            return False, f"Action '{action}' explicitly denied for {agent_id}"

        if action not in perm.allowed_actions:
            logger.warning("Agent action not in allowed list", agent_id=agent_id, action=action)
            return False, f"Action '{action}' not in allowed actions for {agent_id}"

        return True, "Allowed"

    def get_agent_identity(self, agent_id: str) -> Optional[dict]:
        """KYA (Know Your Agent) - Return agent identity information."""
        perm = self.DEFAULT_PERMISSIONS.get(agent_id)
        if not perm:
            return None
        return {
            "agent_id": perm.agent_id,
            "allowed_actions": perm.allowed_actions,
            "risk_level": perm.risk_level,
            "requires_hitl": perm.requires_hitl,
        }


agent_zero_trust = AgentZeroTrust()
