"""Behavioral nurture engine generating high-converting drip email sequences."""

import logging
from typing import Optional
from zerocac.ai.base import LLMMessage
from zerocac.ai.router import AIRouter
from zerocac.analyzer.models import ProductProfile
from zerocac.leads.models import Lead, NurtureEmail, NurtureSequence

logger = logging.getLogger(__name__)


class NurtureEngine:
    """Orchestrates personalized, input-driven email nurture sequences for inbound leads."""

    def __init__(self, router: Optional[AIRouter] = None) -> None:
        """Initialize engine with AI router."""
        self.router = router or AIRouter()

    def build_default_sequence(self, lead: Lead, profile: ProductProfile) -> NurtureSequence:
        """Generate high-converting 3-stage drip sequence without remote AI call."""
        name_greeting = f"Hi {lead.full_name}" if lead.full_name else "Hi there"
        company_mention = f" for {lead.company}" if lead.company else ""

        # Format inputs nicely
        inputs_summary = "\n".join(
            f"- **{k.replace('_', ' ').title()}:** {v}" for k, v in lead.tool_inputs.items()
        ) or "- Standard baseline assessment"

        # Stage 1: Immediate Value Delivery
        stage_1_md = (
            f"{name_greeting},\n\n"
            f"Here is your customized analysis{company_mention} from the {profile.product_name} evaluator.\n\n"
            f"### Your Calculation Inputs:\n{inputs_summary}\n\n"
            f"### Key Takeaway:\n"
            f"Most teams in your space spend thousands on paid ad networks when the organic wedge can deliver "
            f"the same volume at $0 customer acquisition cost.\n\n"
            f"Best regards,\nThe {profile.product_name} Growth Team"
        )

        stage_1 = NurtureEmail(
            step=1,
            delay_hours=0,
            subject=f"Your {profile.product_name} Diagnostic Breakdown",
            body_markdown=stage_1_md,
            body_html=self._wrap_html(stage_1_md, profile.product_name),
        )

        # Stage 2: Case Study & Proof
        stage_2_md = (
            f"{name_greeting},\n\n"
            f"When evaluating {profile.product_name}, founders usually ask: 'Does organic compounding actually work?'\n\n"
            f"Here is how a recent practitioner team replaced their $12k/month paid ad burn:\n"
            f"1. They deployed automated interactive micro-tools targeting buyer pain points.\n"
            f"2. Princeton GEO comparison pages captured high-intent LLM citations on Perplexity & SearchGPT.\n"
            f"3. In 30 days, their inbound pipeline scaled to 45 qualified opportunities at $0 CAC.\n\n"
            f"Read the full teardown or reply directly to this email to see the raw metrics.\n\n"
            f"Best,\nThe {profile.product_name} Team"
        )

        stage_2 = NurtureEmail(
            step=2,
            delay_hours=48,
            subject=f"How teams eliminate paid ad spend with {profile.product_name}",
            body_markdown=stage_2_md,
            body_html=self._wrap_html(stage_2_md, profile.product_name),
        )

        # Stage 3: Invitation / Direct CTA
        stage_3_md = (
            f"{name_greeting},\n\n"
            f"We are onboarding a curated cohort of founders and growth teams onto {profile.product_name}.\n\n"
            f"Given your metrics, we can unlock your custom organic distribution channels directly.\n"
            f"If you'd like early access, reply 'YES' to this email or book 15 minutes with our team.\n\n"
            f"Warmly,\nThe {profile.product_name} Team"
        )

        stage_3 = NurtureEmail(
            step=3,
            delay_hours=96,
            subject=f"Private Invitation: Join the {profile.product_name} cohort",
            body_markdown=stage_3_md,
            body_html=self._wrap_html(stage_3_md, profile.product_name),
        )

        return NurtureSequence(
            lead_id=lead.lead_id,
            recipient_email=str(lead.email),
            product_name=profile.product_name,
            stages=[stage_1, stage_2, stage_3],
        )

    def _wrap_html(self, markdown_text: str, brand: str) -> str:
        """Wrap markdown into responsive, high-deliverability HTML email template."""
        paragraphs = markdown_text.replace("\n\n", "</p><p>").replace("\n", "<br/>")
        return (
            f'<!DOCTYPE html><html><body style="font-family: -apple-system, BlinkMacSystemFont, '
            f"'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #111827; max-width: 600px; "
            f'margin: 0 auto; padding: 24px;">'
            f'<div style="border-bottom: 2px solid #2563eb; padding-bottom: 12px; margin-bottom: 20px;">'
            f'<strong style="font-size: 18px; color: #1e40af;">{brand}</strong></div>'
            f'<p>{paragraphs}</p>'
            f'<div style="margin-top: 32px; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; '
            f'padding-top: 12px;">Sent automatically by {brand} Growth Agent. '
            f'<a href="#" style="color: #6b7280;">Unsubscribe</a></div></body></html>'
        )
