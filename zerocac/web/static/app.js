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

  let latestMicroToolHtml = "";

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

      // Step 3: Generate all organic & high-velocity engines
      setProgress(3);
      const generateRes = await fetch("/api/v1/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile: profile,
          engines: ["sniper", "aeo", "narrative", "directory", "radar", "microtool", "geo", "virality"],
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
      showToast("High-velocity organic engines deployed!");
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
      btnText.textContent = "Synthesizing Growth Strategy...";
      btnSpinner.classList.remove("hidden");
    } else {
      submitBtn.disabled = false;
      btnText.textContent = "Deploy Organic Engines";
      btnSpinner.classList.add("hidden");
    }
  }

  function renderPositioningTab(profile) {
    document.getElementById("profile-name").textContent = profile.product_name;
    document.getElementById("profile-category").textContent = profile.category;
    document.getElementById("profile-oneliner").textContent = profile.one_liner;
    document.getElementById("profile-uvp").textContent = profile.unique_value_proposition;

    // Competitors
    const compContainer = document.getElementById("profile-competitors");
    compContainer.innerHTML = "";
    profile.competitor_gaps.forEach((gap) => {
      const card = document.createElement("div");
      card.className = "competitor-item";
      card.innerHTML = `
        <div class="competitor-name">vs ${escapeHtml(gap.competitor_name)}</div>
        <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;">
          <strong style="color: var(--accent-warning);">Incumbent Flaw:</strong> ${escapeHtml(gap.their_weakness)}
        </div>
        <div style="font-size: 0.85rem; color: var(--accent-primary); margin-top: 0.25rem;">
          <strong>Our Advantage:</strong> ${escapeHtml(gap.our_advantage)}
        </div>
      `;
      compContainer.appendChild(card);
    });

    // Personas
    const personaContainer = document.getElementById("profile-personas");
    personaContainer.innerHTML = "";
    profile.personas.forEach((persona) => {
      const card = document.createElement("div");
      card.className = "persona-card";
      card.innerHTML = `
        <div class="persona-role">${escapeHtml(persona.persona_name)}</div>
        <div class="meta-item" style="margin-top: 0.5rem;">
          <span class="meta-label">Core Pain Point:</span>
          <span style="font-size: 0.85rem; color: var(--text-primary);">${escapeHtml(persona.core_pain_point)}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Trigger Event:</span>
          <span style="font-size: 0.85rem; color: var(--text-secondary);">${escapeHtml(persona.trigger_event)}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Primary Objection:</span>
          <span style="font-size: 0.85rem; color: var(--text-muted);">${escapeHtml(persona.primary_objection)}</span>
        </div>
      `;
      personaContainer.appendChild(card);
    });
  }

  function renderAllEngines(campaign) {
    // 1. Live Intent Radar
    if (campaign.radar) {
      document.getElementById("radar-action-box").textContent = campaign.radar.action_plan;
      const radarContainer = document.getElementById("radar-signals-container");
      radarContainer.innerHTML = "";
      campaign.radar.high_intent_signals.forEach((sig) => {
        const item = document.createElement("div");
        item.className = "opportunity-item";
        item.innerHTML = `
          <div class="opportunity-header">
            <div>
              <span class="platform-badge platform-${sig.source.toLowerCase().replace(/[^a-z]/g, "")}">${escapeHtml(sig.source)}</span>
              <span style="font-size: 0.85rem; color: var(--text-muted); margin-left: 0.5rem;">by ${escapeHtml(sig.author)} (${escapeHtml(sig.created_at)})</span>
            </div>
            <div class="intent-score">Score: ${sig.intent_score}/100</div>
          </div>
          <div style="font-weight: 600; margin-top: 0.5rem; font-size: 0.95rem;">
            <a href="${escapeAttr(sig.url)}" target="_blank" rel="noreferrer" style="color:var(--text-primary);text-decoration:none;">${escapeHtml(sig.title)}</a>
          </div>
          <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;">${escapeHtml(sig.content_snippet)}</p>
          <div class="draft-response-box">
            <span class="meta-label">Recommended Authentic Solution:</span>
            <p style="margin-top: 0.25rem;">${escapeHtml(sig.recommended_reply)}</p>
            <div style="margin-top: 0.5rem;">
              <button type="button" class="btn btn-secondary btn-sm copy-btn" data-copy="${escapeAttr(sig.recommended_reply)}">Copy Reply</button>
            </div>
          </div>
        `;
        radarContainer.appendChild(item);
      });
    }

    // 2. Interactive Micro-Tool
    if (campaign.microtool) {
      const tool = campaign.microtool;
      latestMicroToolHtml = tool.html_content;
      document.getElementById("microtool-name").textContent = tool.concept.tool_name;
      document.getElementById("microtool-headline").textContent = tool.concept.headline;
      document.getElementById("microtool-hook").textContent = tool.concept.virality_hook;
      document.getElementById("microtool-deploy").textContent = tool.deployment_instructions;

      document.getElementById("copy-tool-html-btn").onclick = () => {
        navigator.clipboard.writeText(latestMicroToolHtml);
        showToast("Copied standalone HTML to clipboard!");
      };

      document.getElementById("download-tool-btn").onclick = () => {
        const blob = new Blob([latestMicroToolHtml], { type: "text/html" });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `${tool.concept.slug}.html`;
        a.click();
        showToast("Downloaded index.html!");
      };
    }

    // 3. Princeton GEO
    if (campaign.geo) {
      const geoBox = document.getElementById("geo-assets-container");
      geoBox.innerHTML = "";
      campaign.geo.assets.forEach((asset, idx) => {
        const card = document.createElement("div");
        card.className = "card";
        card.style.marginBottom = "1rem";
        const statsList = asset.statistical_evidence.map((s) => `<li>${escapeHtml(s)}</li>`).join("");
        const promptsList = asset.citation_verification_prompts.map((p) => `<li><code>${escapeHtml(p)}</code></li>`).join("");
        card.innerHTML = `
          <h4 style="color:var(--accent-secondary);font-size:0.95rem;">Target Query: ${escapeHtml(asset.target_query)}</h4>
          <div class="highlight-box accent-box" style="margin-top:0.75rem;">
            <span class="meta-label">Answer-First Definition (${asset.word_count} words):</span>
            <p style="margin-top:0.25rem;line-height:1.5;">${escapeHtml(asset.answer_first_definition)}</p>
          </div>
          <div style="margin-top:0.75rem;">
            <span class="meta-label">Statistical Evidence:</span>
            <ul style="padding-left:1.25rem;font-size:0.85rem;color:var(--text-secondary);margin-top:0.25rem;">${statsList}</ul>
          </div>
          <div style="margin-top:0.75rem;">
            <span class="meta-label">Citation Verification Prompts (for Perplexity / SearchGPT):</span>
            <ul style="padding-left:1.25rem;font-size:0.85rem;margin-top:0.25rem;">${promptsList}</ul>
          </div>
        `;
        geoBox.appendChild(card);
      });

      document.getElementById("geo-robots-container").textContent = campaign.geo.robots_txt_rules;
      document.getElementById("geo-bing-container").textContent = campaign.geo.bing_webmaster_guidelines;
    }

    // 4. Virality Loops
    if (campaign.virality) {
      const v = campaign.virality;
      const mechBox = document.getElementById("virality-mechanics");
      mechBox.innerHTML = "";
      v.viral_loop_mechanics.forEach((step) => {
        const d = document.createElement("div");
        d.className = "highlight-box";
        d.style.marginBottom = "0.5rem";
        d.textContent = step;
        mechBox.appendChild(d);
      });

      document.getElementById("virality-svg-preview").innerHTML = v.svg_badge;
      document.getElementById("virality-markdown-code").textContent = v.markdown_badge;
      document.getElementById("copy-virality-md-btn").setAttribute("data-copy", v.markdown_badge);

      document.getElementById("virality-html-code").textContent = v.html_badge_snippet;
      document.getElementById("copy-virality-html-btn").setAttribute("data-copy", v.html_badge_snippet);
    }

    // 5. Intent Sniper
    if (campaign.sniper) {
      const sniperContainer = document.getElementById("sniper-container");
      sniperContainer.innerHTML = "";
      campaign.sniper.opportunities.forEach((opp) => {
        const item = document.createElement("div");
        item.className = "opportunity-item";
        item.innerHTML = `
          <div class="opportunity-header">
            <div>
              <span class="platform-badge platform-${opp.platform.toLowerCase().replace(/[^a-z]/g, "")}">${escapeHtml(opp.platform)}</span>
              <span style="font-size: 0.85rem; color: var(--text-muted); margin-left: 0.5rem;">${escapeHtml(opp.community)}</span>
            </div>
            <div class="intent-score">Intent: ${opp.intent_score}/100</div>
          </div>
          <div style="font-weight: 600; margin-top: 0.5rem; font-size: 0.95rem;">"${escapeHtml(opp.thread_title)}"</div>
          <div class="draft-response-box">
            <span class="meta-label">Authentic Solution:</span>
            <p style="margin-top: 0.25rem;">${escapeHtml(opp.draft_response)}</p>
            <div style="margin-top: 0.5rem;">
              <button type="button" class="btn btn-secondary btn-sm copy-btn" data-copy="${escapeAttr(opp.draft_response)}">Copy Response</button>
            </div>
          </div>
        `;
        sniperContainer.appendChild(item);
      });
    }

    // 6. AEO Pages
    if (campaign.aeo) {
      const aeoBox = document.getElementById("aeo-container");
      aeoBox.innerHTML = "";
      campaign.aeo.comparison_pages.forEach((page) => {
        const item = document.createElement("div");
        item.className = "card";
        item.style.marginBottom = "1rem";
        item.innerHTML = `
          <div class="card-header-flex">
            <div>
              <h4 style="color: var(--accent-primary); font-size: 1rem;">vs ${escapeHtml(page.target_competitor)}</h4>
              <p style="font-size: 0.85rem; color: var(--text-muted);">Slug: <code>${escapeHtml(page.slug)}</code></p>
            </div>
            <button type="button" class="btn btn-secondary btn-sm copy-btn" data-copy="${escapeAttr(page.markdown_content)}">Copy Markdown</button>
          </div>
          <pre class="script-box" style="margin-top: 0.75rem;">${escapeHtml(page.markdown_content.substring(0, 450))}...</pre>
        `;
        aeoBox.appendChild(item);
      });
    }

    // 7. Viral Content
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

    // 8. Directory
    if (campaign.directory) {
      const tbody = document.getElementById("directory-tbody");
      tbody.innerHTML = "";
      campaign.directory.listings.forEach((listing) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${escapeHtml(listing.directory_name)}</strong></td>
          <td><span class="badge badge-success">DA ${listing.domain_authority}</span></td>
          <td style="font-family: var(--font-mono); font-size: 0.8rem;">${escapeHtml(listing.tagline)}</td>
          <td>
            <a href="${escapeAttr(listing.submission_url)}" target="_blank" rel="noreferrer" class="btn btn-secondary btn-sm">Submit</a>
          </td>
        `;
        tbody.appendChild(tr);
      });
    }

    // Bind all copy buttons
    document.querySelectorAll(".copy-btn").forEach((btn) => {
      btn.onclick = () => {
        const text = btn.getAttribute("data-copy");
        if (text) {
          navigator.clipboard.writeText(text);
          showToast("Copied to clipboard!");
        }
      };
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
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function escapeAttr(str) {
    if (!str) return "";
    return String(str).replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
});
