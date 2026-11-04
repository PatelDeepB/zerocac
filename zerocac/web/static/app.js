// ZeroCAC Front-End Control Dashboard

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("marketing-form");
  const urlInput = document.getElementById("product-url");
  const providerSelect = document.getElementById("ai-provider-select");
  const submitBtn = document.getElementById("submit-btn");
  const btnText = document.getElementById("btn-text");
  const btnSpinner = document.getElementById("btn-spinner");
  const loadDemoBtn = document.getElementById("load-demo-btn");
  const progressContainer = document.getElementById("progress-container");
  const resultsWorkspace = document.getElementById("results-workspace");
  const toast = document.getElementById("toast");

  // Tab switching
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const targetContent = document.getElementById(targetId);
      if (targetContent) targetContent.classList.add("active");
    });
  });

  // Load demo example
  loadDemoBtn.addEventListener("click", () => {
    urlInput.value = "https://zerocac.org";
    showToast("Loaded ZeroCAC demo target");
  });

  // Form submit handler
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = urlInput.value.trim();
    const provider = providerSelect.value;
    if (!url) return;

    setLoading(true);
    setProgress(1);

    try {
      // Step 1 & 2: Analyze
      setProgress(2);
      const analyzeRes = await fetch("/api/v1/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url, provider: provider }),
      });

      if (!analyzeRes.ok) {
        throw new Error(`Analysis failed with status ${analyzeRes.status}`);
      }

      const profile = await analyzeRes.json();
      renderPositioningTab(profile);

      // Step 3: Generate 4 engines
      setProgress(3);
      const generateRes = await fetch("/api/v1/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile: profile,
          engines: ["sniper", "aeo", "narrative", "directory"],
          provider: provider,
        }),
      });

      if (!generateRes.ok) {
        throw new Error(`Generation failed with status ${generateRes.status}`);
      }

      const campaign = await generateRes.json();
      renderAllEngines(campaign);

      setProgress(4);
      resultsWorkspace.classList.remove("hidden");
      resultsWorkspace.scrollIntoView({ behavior: "smooth" });
      showToast("Organic marketing campaigns staged successfully!");
    } catch (err) {
      console.error(err);
      showToast(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  });

  function setProgress(step) {
    progressContainer.classList.remove("hidden");
    for (let i = 1; i <= 4; i++) {
      const el = document.getElementById(`step-${i}`);
      if (i <= step) {
        el.classList.add("active");
      } else {
        el.classList.remove("active");
      }
    }
  }

  function setLoading(isLoading) {
    if (isLoading) {
      submitBtn.disabled = true;
      btnSpinner.classList.remove("hidden");
      btnText.textContent = "Deploying Autonomous Agent...";
    } else {
      submitBtn.disabled = false;
      btnSpinner.classList.add("hidden");
      btnText.textContent = "Deploy Organic Growth Agent";
    }
  }

  function renderPositioningTab(profile) {
    document.getElementById("profile-name").textContent = profile.product_name;
    document.getElementById("profile-category").textContent = profile.category;
    document.getElementById("profile-oneliner").textContent = profile.one_liner;
    document.getElementById("profile-uvp").textContent = profile.unique_value_proposition;

    // Competitors
    const compBox = document.getElementById("profile-competitors");
    compBox.innerHTML = "";
    profile.competitor_gaps.forEach((gap) => {
      const el = document.createElement("div");
      el.className = "competitor-card";
      el.innerHTML = `
        <div class="competitor-name">Target: ${gap.competitor_name}</div>
        <p style="font-size: 0.85rem; color: var(--text-secondary);">Weakness: ${gap.their_weakness}</p>
        <p style="font-size: 0.85rem; color: var(--accent-primary); margin-top: 0.25rem;">Our Edge: ${gap.our_advantage}</p>
      `;
      compBox.appendChild(el);
    });

    // Personas
    const personasBox = document.getElementById("profile-personas");
    personasBox.innerHTML = "";
    profile.personas.forEach((p) => {
      const el = document.createElement("div");
      el.className = "persona-card";
      el.innerHTML = `
        <div class="persona-title">${p.persona_name}</div>
        <p style="font-size: 0.85rem; margin-bottom: 0.4rem;"><strong>Core Agony:</strong> ${p.core_pain_point}</p>
        <p style="font-size: 0.85rem; margin-bottom: 0.4rem;"><strong>Trigger Event:</strong> ${p.trigger_event}</p>
        <p style="font-size: 0.85rem; color: var(--text-muted);">Watering Holes: ${p.watering_holes.join(", ")}</p>
      `;
      personasBox.appendChild(el);
    });
  }

  function renderAllEngines(campaign) {
    // 1. Sniper
    if (campaign.sniper) {
      const container = document.getElementById("sniper-container");
      container.innerHTML = "";
      campaign.sniper.opportunities.forEach((opp) => {
        const el = document.createElement("div");
        el.className = "opportunity-card";
        el.innerHTML = `
          <div class="opportunity-header">
            <div>
              <strong>${opp.platform} (${opp.community})</strong>
              <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.2rem;">${opp.thread_title}</div>
            </div>
            <span class="intent-badge">${opp.intent_score}% Intent</span>
          </div>
          <div class="response-draft-box">${escapeHtml(opp.draft_response)}</div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 0.75rem; color: var(--text-muted);">Angle: ${opp.organic_mention_angle}</span>
            <button class="btn btn-secondary btn-sm copy-btn" data-copy="${escapeAttr(opp.draft_response)}">Copy Answer</button>
          </div>
        `;
        container.appendChild(el);
      });
    }

    // 2. AEO
    if (campaign.aeo) {
      const container = document.getElementById("aeo-container");
      container.innerHTML = "";
      campaign.aeo.comparison_pages.forEach((page) => {
        const el = document.createElement("div");
        el.className = "card";
        el.style.marginBottom = "1rem";
        el.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <h4>${page.title}</h4>
            <button class="btn btn-secondary btn-sm copy-btn" data-copy="${escapeAttr(page.markdown_content)}">Copy Markdown</button>
          </div>
          <pre class="script-box" style="max-height: 200px; overflow-y: auto;">${escapeHtml(page.markdown_content)}</pre>
        `;
        container.appendChild(el);
      });
    }

    // 3. Viral
    if (campaign.narrative) {
      const threadBox = document.getElementById("viral-thread-container");
      threadBox.innerHTML = "";
      campaign.narrative.x_thread.forEach((tweet) => {
        const el = document.createElement("div");
        el.className = "highlight-box";
        el.style.marginBottom = "0.75rem";
        el.textContent = tweet;
        threadBox.appendChild(el);
      });

      const carouselBox = document.getElementById("viral-carousel-container");
      carouselBox.innerHTML = "";
      campaign.narrative.linkedin_carousel.forEach((slide) => {
        const el = document.createElement("div");
        el.className = "highlight-box accent-box";
        el.style.marginBottom = "0.75rem";
        el.textContent = slide;
        carouselBox.appendChild(el);
      });

      document.getElementById("viral-video-container").textContent = campaign.narrative.video_script_60s;
    }

    // 4. Directory
    if (campaign.directory) {
      const tbody = document.getElementById("directory-tbody");
      tbody.innerHTML = "";
      campaign.directory.listings.forEach((listing) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${listing.directory_name}</strong></td>
          <td><span class="badge badge-success">DA ${listing.domain_authority}</span></td>
          <td style="font-family: var(--font-mono); font-size: 0.8rem;">${listing.tagline}</td>
          <td>
            <a href="${listing.submission_url}" target="_blank" rel="noreferrer" class="btn btn-secondary btn-sm">Submit</a>
          </td>
        `;
        tbody.appendChild(tr);
      });
    }

    // Bind copy buttons
    document.querySelectorAll(".copy-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const text = btn.getAttribute("data-copy");
        navigator.clipboard.writeText(text);
        showToast("Copied to clipboard!");
      });
    });
  }

  function showToast(message) {
    toast.textContent = message;
    toast.classList.remove("hidden");
    setTimeout(() => {
      toast.classList.add("hidden");
    }, 2500);
  }

  function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function escapeAttr(str) {
    return str.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
});
