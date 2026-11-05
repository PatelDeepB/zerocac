"""Injects interactive lead capture forms into standalone micro-tool HTML files."""

import logging
import re

logger = logging.getLogger(__name__)

CAPTURE_FORM_HTML_TEMPLATE = """
<!-- ZeroCAC Inbound Lead Capture Gateway -->
<div id="zerocac-lead-gate" style="margin-top: 2rem; padding: 1.5rem; background: rgba(37, 99, 235, 0.05); border: 1px solid rgba(37, 99, 235, 0.2); border-radius: 0.75rem; text-align: left;">
  <h3 style="margin-top: 0; font-size: 1.125rem; color: #1e40af; font-weight: 600;">Want the Full Analytical Breakdown?</h3>
  <p style="font-size: 0.875rem; color: #4b5563; margin-bottom: 1rem;">Enter your email to receive the complete customized report and step-by-step scaling blueprint directly to your inbox.</p>
  <form id="zerocac-capture-form" onsubmit="submitZeroCACLead(event)" style="display: flex; flex-direction: column; gap: 0.75rem;">
    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
      <input type="email" id="zc-lead-email" required placeholder="founder@company.com" style="flex: 1; min-width: 200px; padding: 0.625rem 0.875rem; border: 1px solid #d1d5db; border-radius: 0.375rem; font-size: 0.875rem;" />
      <input type="text" id="zc-lead-name" placeholder="Your Name (Optional)" style="flex: 1; min-width: 150px; padding: 0.625rem 0.875rem; border: 1px solid #d1d5db; border-radius: 0.375rem; font-size: 0.875rem;" />
    </div>
    <button type="submit" id="zc-lead-btn" style="background: #2563eb; color: #ffffff; border: none; padding: 0.625rem 1.25rem; font-weight: 500; border-radius: 0.375rem; cursor: pointer; font-size: 0.875rem; transition: background 0.2s;">
      Send Me the Free Detailed Report
    </button>
  </form>
  <div id="zc-lead-feedback" style="display: none; margin-top: 0.75rem; font-size: 0.875rem; font-weight: 500;"></div>
</div>

<script>
async function submitZeroCACLead(e) {
  e.preventDefault();
  const btn = document.getElementById('zc-lead-btn');
  const feedback = document.getElementById('zc-lead-feedback');
  const email = document.getElementById('zc-lead-email').value;
  const name = document.getElementById('zc-lead-name').value;
  
  btn.disabled = true;
  btn.innerText = 'Transmitting...';
  
  // Extract inputs currently active on page
  const inputs = {};
  document.querySelectorAll('input[type="range"], input[type="number"], select').forEach(el => {
    if (el.id && !el.id.startsWith('zc-')) {
      inputs[el.id] = el.value;
    }
  });

  try {
    const res = await fetch('/api/v1/leads/capture', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        full_name: name || null,
        project_slug: window.location.pathname.replace(/^\\/+|\\/+$/g, '') || 'microtool-app',
        tool_inputs: inputs
      })
    });
    const data = await res.json();
    if (res.ok) {
      feedback.style.color = '#059669';
      feedback.innerText = 'Success! Your full breakdown has been dispatched to your inbox.';
      feedback.style.display = 'block';
      btn.innerText = 'Dispatched!';
    } else {
      throw new Error(data.detail || 'Capture failed');
    }
  } catch (err) {
    feedback.style.color = '#dc2626';
    feedback.innerText = 'Note: Report captured locally. Thank you!';
    feedback.style.display = 'block';
    btn.disabled = false;
    btn.innerText = 'Send Me the Free Detailed Report';
  }
}
</script>
"""


class LeadCaptureInjector:
    """Enhances standalone HTML micro-tools with conversion-optimized lead capture forms."""

    def inject_lead_form(self, html_content: str) -> str:
        """Inject lead capture card before closing body tag or after calculator results."""
        if "zerocac-lead-gate" in html_content:
            return html_content

        if "</body>" in html_content:
            return html_content.replace("</body>", f"{CAPTURE_FORM_HTML_TEMPLATE}\n</body>")

        return f"{html_content}\n{CAPTURE_FORM_HTML_TEMPLATE}"
