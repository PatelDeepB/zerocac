"""Embeddable viral badges, referral share modals, and leaderboard widgets."""

from typing import List
from zerocac.virality.models import LeaderboardEntry, ReferralStats


class ViralWidgetRenderer:
    """Renders scalable vector badges and HTML widgets for product-led distribution."""

    @staticmethod
    def render_svg_counter_badge(product_name: str, ad_savings_usd: float) -> str:
        """Render standalone SVG badge highlighting verified ad dollars displaced."""
        savings_text = f"${ad_savings_usd:,.0f} Saved vs Ads"
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="260" height="28" viewBox="0 0 260 28" role="img" aria-label="{product_name}: {savings_text}">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="a">
    <rect width="260" height="28" rx="4" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#a)">
    <rect width="110" height="28" fill="#18181b"/>
    <rect x="110" width="150" height="28" fill="#10b981"/>
    <rect width="260" height="28" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Inter,-apple-system,BlinkMacSystemFont,sans-serif" font-size="11" font-weight="600">
    <text x="55" y="18" fill="#a1a1aa">{product_name}</text>
    <text x="185" y="18" fill="#000">{savings_text}</text>
  </g>
</svg>"""

    @staticmethod
    def render_leaderboard_html_widget(entries: List[LeaderboardEntry]) -> str:
        """Generate interactive HTML table representing the community referral leaderboard."""
        rows_html = "".join(
            f"""
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.08);">
              <td style="padding: 0.6rem 0.75rem; font-weight: 700; color: #10b981;">#{e.rank}</td>
              <td style="padding: 0.6rem 0.75rem;"><code>{e.user_handle}</code></td>
              <td style="padding: 0.6rem 0.75rem; text-align: center;"><strong>{e.referrals_driven}</strong></td>
              <td style="padding: 0.6rem 0.75rem; color: #34d399;">${e.ad_dollars_saved_usd:,.0f}</td>
              <td style="padding: 0.6rem 0.75rem;"><span style="font-size: 0.75rem; background: rgba(99,102,241,0.2); color: #818cf8; padding: 0.2rem 0.5rem; border-radius: 4px;">{e.badge_title}</span></td>
            </tr>
            """
            for e in entries
        )

        return f"""
        <div style="background: #18181b; color: #fafafa; border: 1px solid #27272a; border-radius: 8px; padding: 1.25rem; font-family: Inter, sans-serif;">
          <h3 style="margin-top: 0; font-size: 1.1rem; color: #10b981;">Leaderboard of Organic CAC Killers</h3>
          <p style="font-size: 0.85rem; color: #a1a1aa; margin-bottom: 1rem;">Top founders scaling distribution without burning capital on Google or Meta ads.</p>
          <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
              <thead>
                <tr style="color: #71717a; text-align: left; border-bottom: 1px solid #3f3f46; font-size: 0.75rem; text-transform: uppercase;">
                  <th style="padding: 0.5rem 0.75rem;">Rank</th>
                  <th style="padding: 0.5rem 0.75rem;">Champion</th>
                  <th style="padding: 0.5rem 0.75rem; text-align: center;">Referrals</th>
                  <th style="padding: 0.5rem 0.75rem;">Ad Dollars Saved</th>
                  <th style="padding: 0.5rem 0.75rem;">Title</th>
                </tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>
          </div>
        </div>
        """
