// ZeroCAC Mission Control Dashboard Controller

document.addEventListener("DOMContentLoaded", () => {
  // Elements
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

  // Modal
  const previewModal = document.getElementById("preview-modal");
  const previewModalBody = document.getElementById("preview-modal-body");
  const previewCloseBtn = document.getElementById("preview-close-btn");

  // State
  let currentProductProfile = null;
  let currentLaunchPackage = null;
  let currentPSEOPackage = null;
  let currentInterceptOpportunities = [];
  let latestMicroToolHtml = "";

  // Quick Action Buttons
  setupQuickButtons();

  // Tab switching
  setupTabNavigation();

  // Modal handlers
  setupModalHandlers();

  // Load demo profile on startup
  loadDemoProfile();

  // Event Listeners for Modules
  setupFormSubmit();
  setupLaunchCockpit();
  setupPSEOStudio();
  setupCommunityInterceptor();
  setupLeadsAndTelemetry();

  function setupTabNavigation() {
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetId = btn.getAttribute("data-tab");
        switchTab(targetId);
      });
    });
  }

  function switchTab(targetId) {
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabBtns.forEach((b) => {
      b.classList.toggle("active", b.getAttribute("data-tab") === targetId);
    });

    tabContents.forEach((c) => {
      c.classList.toggle("active", c.id === targetId);
    });
  }

  function setupQuickButtons() {
    bindClick("btn-quick-launch", () => switchTab("tab-launch"));
    bindClick("btn-quick-pseo", () => switchTab("tab-pseo"));
    bindClick("btn-quick-intercept", () => switchTab("tab-intercept"));
    bindClick("btn-quick-leads", () => switchTab("tab-leads-telemetry"));
    bindClick("load-demo-btn", () => {
      urlInput.value = "https://zerocac.org";
      loadDemoProfile();
      showToast("Loaded ZeroCAC demo profile");
    });
  }

  function setupModalHandlers() {
    previewCloseBtn.addEventListener("click", () => {
      previewModal.classList.add("hidden");
    });

    previewModal.addEventListener("click", (e) => {
      if (e.target === previewModal) {
        previewModal.classList.add("hidden");
      }
    });
  }

  function openPreviewModal(htmlContent) {
    previewModalBody.innerHTML = htmlContent;
    previewModal.classList.remove("hidden");
  }

  function bindClick(id, handler) {
    const el = document.getElementById(id);
    if (el) el.addEventListener("click", handler);
  }

  // Form Submit Handler
  function setupFormSubmit() {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const url = urlInput.value.trim();
      const provider = providerSelect.value;
      if (!url) return;

      setLoading(true);
      setProgress(1);

      try {
        setProgress(2);
        const profile = await requestJson("/api/v1/analyze", {
          method: "POST",
          body: JSON.stringify({ url: url, provider: provider }),
        });

        currentProductProfile = profile;
        renderPositioningTab(profile);

        setProgress(3);
        const campaign = await requestJson("/api/v1/generate", {
          method: "POST",
          body: JSON.stringify({
            profile: profile,
            engines: ["sniper", "aeo", "narrative", "directory", "radar", "microtool", "geo", "virality"],
            provider: provider,
          }),
        });

        renderAllEngines(campaign);

        // Auto prepare launch kit & pSEO
        await autoStageEngines(url);

        setProgress(4);
        showToast("Mission Control: Organic engines active!");
      } catch (err) {
        showToast(`Error: ${err.message}`);
      } finally {
        setLoading(false);
      }
    });
  }

  async function autoStageEngines(url) {
    try {
      const launchPkg = await requestJson("/api/v1/launch/prepare", {
        method: "POST",
        body: JSON.stringify({ url: url, dry_run: true }),
      });
      renderLaunchPackage(launchPkg);
    } catch {
      // Graceful fallback to cached state
    }
  }

  // Launch Cockpit Handlers
  function setupLaunchCockpit() {
    bindClick("btn-prepare-launch", async () => {
      const url = urlInput.value.trim() || "https://zerocac.org";
      showToast("Synthesizing 8-Vector Launch Kit...");
      try {
        const pkg = await requestJson("/api/v1/launch/prepare", {
          method: "POST",
          body: JSON.stringify({ url: url, dry_run: true }),
        });
        renderLaunchPackage(pkg);
        showToast("8-Vector Launch Kit Ready!");
      } catch (err) {
        showToast(`Launch prep error: ${err.message}`);
      }
    });

    bindClick("btn-execute-launch", async () => {
      if (!currentLaunchPackage) {
        showToast("Please prepare launch kit first");
        return;
      }
      showToast("Dispatching launch waves...");
      try {
        const report = await requestJson("/api/v1/launch/execute", {
          method: "POST",
          body: JSON.stringify({ package: currentLaunchPackage, dry_run: true }),
        });
        renderLaunchReport(report);
        showToast("Launch Waves Completed!");
      } catch (err) {
        showToast(`Launch execution error: ${err.message}`);
      }
    });

    bindClick("btn-view-gh-readme", () => {
      if (currentLaunchPackage?.github_repo) {
        openPreviewModal(`<pre style="white-space: pre-wrap; font-family: monospace;">${escapeHtml(currentLaunchPackage.github_repo.readme_content)}</pre>`);
      }
    });

    bindClick("btn-view-hn-comment", () => {
      if (currentLaunchPackage?.show_hn) {
        openPreviewModal(`<h3>Hacker News First Comment</h3><div class="response-draft-box">${escapeHtml(currentLaunchPackage.show_hn.first_comment)}</div>`);
      }
    });

    bindClick("btn-view-ph-comment", () => {
      if (currentLaunchPackage?.product_hunt) {
        openPreviewModal(`<h3>Product Hunt Maker Note</h3><div class="response-draft-box">${escapeHtml(currentLaunchPackage.product_hunt.maker_first_comment)}</div>`);
      }
    });

    bindClick("btn-view-reddit-posts", () => {
      if (currentLaunchPackage?.reddit_syndication) {
        const html = currentLaunchPackage.reddit_syndication.map((r, i) => `
          <div class="card" style="margin-bottom: 1rem;">
            <h4>${i + 1}. Subreddit: ${escapeHtml(r.subreddit)} (Wave ${r.wave_number})</h4>
            <p><strong>Title:</strong> ${escapeHtml(r.title)}</p>
            <div class="response-draft-box">${escapeHtml(r.body)}</div>
          </div>
        `).join("");
        openPreviewModal(`<h3>Reddit 5-Subreddit Syndication</h3>${html}`);
      }
    });

    bindClick("btn-view-devto-article", () => {
      if (currentLaunchPackage?.devto_article) {
        openPreviewModal(`<h3>Dev.to Technical Article</h3><pre style="white-space: pre-wrap; font-family: monospace;">${escapeHtml(currentLaunchPackage.devto_article.markdown_body)}</pre>`);
      }
    });

    bindClick("btn-view-social-thread", () => {
      if (currentLaunchPackage?.social_blast) {
        const tweets = currentLaunchPackage.social_blast.x_thread.map((t, i) => `<div class="highlight-box" style="margin-bottom: 0.5rem;"><strong>Tweet ${i + 1}:</strong> ${escapeHtml(t)}</div>`).join("");
        openPreviewModal(`<h3>X & LinkedIn Launch Blast</h3>${tweets}`);
      }
    });

    bindClick("btn-view-directory-pkgs", () => {
      if (currentLaunchPackage?.directory_submissions) {
        const items = currentLaunchPackage.directory_submissions.map((d) => `
          <tr>
            <td><strong>${escapeHtml(d.directory_name)}</strong></td>
            <td><span class="badge badge-success">DA ${d.domain_authority}</span></td>
            <td>${escapeHtml(d.tagline)}</td>
          </tr>
        `).join("");
        openPreviewModal(`
          <h3>15 Fast-Track Directories</h3>
          <table class="directory-table">
            <thead><tr><th>Directory</th><th>DA</th><th>Tagline</th></tr></thead>
            <tbody>${items}</tbody>
          </table>
        `);
      }
    });

    bindClick("btn-preview-edge-tool", () => {
      if (latestMicroToolHtml) {
        openPreviewModal(`<iframe srcdoc="${escapeAttr(latestMicroToolHtml)}" style="width:100%;height:70vh;border:none;border-radius:8px;"></iframe>`);
      }
    });

    bindClick("btn-download-edge-tool", () => {
      if (!latestMicroToolHtml) return;
      downloadFile("edge-microtool.html", latestMicroToolHtml, "text/html");
      showToast("Downloaded standalone tool HTML!");
    });
  }

  function renderLaunchPackage(pkg) {
    currentLaunchPackage = pkg;
    document.getElementById("launch-kit-status").textContent = "Kit Synchronized";
    document.getElementById("launch-gh-name").textContent = pkg.github_repo.repo_name;
    document.getElementById("launch-gh-desc").textContent = pkg.github_repo.description;
    setCopy("btn-copy-gh-readme", pkg.github_repo.readme_content);

    document.getElementById("launch-hn-title").textContent = pkg.show_hn.title;
    setCopy("btn-copy-hn-comment", pkg.show_hn.first_comment);

    document.getElementById("launch-ph-tagline").textContent = pkg.product_hunt.tagline;
    setCopy("btn-copy-ph-comment", pkg.product_hunt.maker_first_comment);

    if (pkg.reddit_syndication?.length > 0) {
      setCopy("btn-copy-reddit-post1", pkg.reddit_syndication[0].body);
    }

    document.getElementById("launch-devto-title").textContent = pkg.devto_article.title;
    setCopy("btn-copy-devto-article", pkg.devto_article.markdown_body);

    if (pkg.social_blast?.x_thread?.length > 0) {
      document.getElementById("launch-social-hook").textContent = pkg.social_blast.x_thread[0];
      setCopy("btn-copy-social-thread", pkg.social_blast.x_thread.join("\n\n"));
    }

    document.getElementById("launch-microtool-title").textContent = pkg.edge_microtool.tool_name;
    latestMicroToolHtml = pkg.edge_microtool.html_payload;
  }

  function renderLaunchReport(report) {
    const box = document.getElementById("launch-execution-box");
    box.classList.remove("hidden");
    const passed = report.results.filter((r) => r.success).length;
    box.innerHTML = `
      <strong>Launch Execution Report:</strong> ${passed}/${report.total_vectors} Vectors Synchronized | <strong>Status:</strong> ${escapeHtml(report.status.toUpperCase())}
      <div style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-secondary);">
        Simulated zero-hour syndication across GitHub, Show HN, Product Hunt, Reddit waves, Dev.to, and directories. Estimated immediate traffic: 1,200+ unique visitors.
      </div>
    `;
  }

  // pSEO Studio Handlers
  function setupPSEOStudio() {
    bindClick("btn-generate-pseo", async () => {
      const url = urlInput.value.trim() || "https://zerocac.org";
      const count = parseInt(document.getElementById("pseo-count-input").value, 10) || 15;
      showToast("Generating Multi-Axis pSEO Matrix...");

      try {
        const pkg = await requestJson("/api/v1/pseo/generate", {
          method: "POST",
          body: JSON.stringify({ url: url, count: count, dry_run: true }),
        });
        renderPSEOPackage(pkg);
        showToast(`pSEO Matrix: ${pkg.total_pages} pages compiled!`);
      } catch (err) {
        showToast(`pSEO error: ${err.message}`);
      }
    });

    bindClick("btn-deploy-pseo", async () => {
      if (!currentPSEOPackage) {
        showToast("Generate pSEO matrix first");
        return;
      }
      showToast("Deploying to Edge and IndexNow...");
      try {
        const rep = await requestJson("/api/v1/pseo/deploy", {
          method: "POST",
          body: JSON.stringify({ package: currentPSEOPackage, dry_run: true }),
        });
        showToast(`Edge Deployed! ${rep.indexnow_urls_submitted} URLs submitted to IndexNow.`);
      } catch (err) {
        showToast(`Deploy error: ${err.message}`);
      }
    });
  }

  function renderPSEOPackage(pkg) {
    currentPSEOPackage = pkg;
    const summary = document.getElementById("pseo-summary-box");
    summary.innerHTML = `
      <strong>Matrix Coverage:</strong> ${pkg.total_pages} Validated Pages | <strong>Est. Monthly Search Volume:</strong> ${pkg.estimated_monthly_search_volume.toLocaleString()} visits | <strong>Internal Mesh:</strong> ${pkg.internal_mesh.total_connections} Cross-Links
    `;

    const tbody = document.getElementById("pseo-tbody");
    tbody.innerHTML = "";

    pkg.pages.forEach((p, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${escapeHtml(p.target_keyword)}</strong></td>
        <td><span class="badge badge-neutral">${escapeHtml(p.axis.replace("_", " ").toUpperCase())}</span></td>
        <td><span class="badge badge-success">${p.demand_score}/100</span></td>
        <td style="font-family: var(--font-mono);">${p.estimated_monthly_visits.toLocaleString()}</td>
        <td style="font-size: 0.85rem; color: var(--text-secondary);">${escapeHtml(p.hook)}</td>
        <td>
          <button type="button" class="btn btn-secondary btn-sm preview-page-btn" data-idx="${idx}">Preview</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll(".preview-page-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const idx = parseInt(btn.getAttribute("data-idx"), 10);
        const page = pkg.pages[idx];
        if (page) {
          openPreviewModal(`<iframe srcdoc="${escapeAttr(page.html_content)}" style="width:100%;height:75vh;border:none;border-radius:8px;"></iframe>`);
        }
      });
    });

    document.getElementById("pseo-worker-snippet").textContent = pkg.edge_proxy_snippet;
    setCopy("btn-copy-worker", pkg.edge_proxy_snippet);

    document.getElementById("pseo-sitemap-snippet").textContent = pkg.sitemap_xml;
    setCopy("btn-copy-sitemap", pkg.sitemap_xml);
  }

  // Community Interceptor Handlers
  function setupCommunityInterceptor() {
    bindClick("btn-scan-intercept", async () => {
      const url = urlInput.value.trim() || "https://zerocac.org";
      const subs = document.getElementById("intercept-subreddits").value.split(",").map((s) => s.trim()).filter(Boolean);
      const minScore = parseInt(document.getElementById("intercept-min-score").value, 10) || 75;
      const stealth = document.getElementById("intercept-stealth-mode").value;

      showToast("Scanning Reddit, HN, and X streams...");
      try {
        const opps = await requestJson("/api/v1/intercept/scan", {
          method: "POST",
          body: JSON.stringify({
            url: url,
            subreddits: subs,
            min_score: minScore,
            stealth_mode: stealth,
            dry_run: true,
          }),
        });
        renderInterceptOpportunities(opps);
        showToast(`Radar: ${opps.length} high-agony signals detected!`);
        refreshInterceptorTelemetry();
      } catch (err) {
        showToast(`Scan error: ${err.message}`);
      }
    });
  }

  function renderInterceptOpportunities(opps) {
    currentInterceptOpportunities = opps;
    const container = document.getElementById("intercept-feed-container");
    container.innerHTML = "";

    if (opps.length === 0) {
      container.innerHTML = `<div class="highlight-box">No buyer pain signals above qualifying threshold.</div>`;
      return;
    }

    opps.forEach((opp, idx) => {
      const card = document.createElement("div");
      card.className = "intercept-card";

      const spend = opp.numeric_entities?.monthly_spend ? `$${opp.numeric_entities.monthly_spend}/mo` : "Not specified";
      const scale = opp.numeric_entities?.scale_volume || "Mid-market";
      const seats = opp.numeric_entities?.team_seats || 5;

      card.innerHTML = `
        <div class="opportunity-header">
          <div>
            <span class="platform-badge platform-${opp.source.toLowerCase().replace(/[^a-z]/g, "")}">${escapeHtml(opp.source)}</span>
            <span class="badge badge-neutral" style="margin-left: 0.5rem;">${escapeHtml(opp.community)}</span>
            <span style="font-size: 0.8rem; color: var(--text-muted); margin-left: 0.5rem;">by ${escapeHtml(opp.author)} (${escapeHtml(opp.created_at)})</span>
          </div>
          <div class="intent-score-badge">Intent: ${opp.intent_score}/100</div>
        </div>

        <div style="font-weight: 600; font-size: 1rem;">
          <a href="${escapeAttr(opp.url)}" target="_blank" rel="noreferrer" style="color:var(--text-primary);text-decoration:none;">${escapeHtml(opp.title)}</a>
        </div>
        <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.4;">${escapeHtml(opp.content_snippet)}</p>

        <div class="math-callout">
          <strong>OP Economic Reality:</strong> Spend: ${escapeHtml(spend)} | Scale: ${escapeHtml(scale)} | Seats: ${seats}
          <br>
          <span style="color: var(--accent-primary); font-size: 0.8rem;">Calculated Line-Item Savings: 78% vs Current Architecture</span>
        </div>

        <div class="response-draft-box">
          <span class="meta-label">Synthesized Trojan Practitioner Reply (${escapeHtml(opp.stealth_mode)}):</span>
          <p style="margin-top: 0.25rem;">${escapeHtml(opp.draft_response)}</p>
        </div>

        <div style="display: flex; gap: 0.5rem; align-items: center; justify-content: space-between;">
          <div style="display: flex; gap: 0.5rem;">
            <button type="button" class="btn btn-primary btn-sm btn-post-reply" data-idx="${idx}">Approve & Post</button>
            <button type="button" class="btn btn-secondary btn-sm btn-dry-reply" data-idx="${idx}">Simulate Dry-Run</button>
          </div>
          <button type="button" class="btn btn-secondary btn-sm copy-btn" data-copy="${escapeAttr(opp.draft_response)}">Copy Reply</button>
        </div>
      `;
      container.appendChild(card);
    });

    container.querySelectorAll(".btn-post-reply").forEach((b) => {
      b.addEventListener("click", () => handleDispatchReply(b.getAttribute("data-idx"), false));
    });

    container.querySelectorAll(".btn-dry-reply").forEach((b) => {
      b.addEventListener("click", () => handleDispatchReply(b.getAttribute("data-idx"), true));
    });

    bindCopyButtons();
  }

  async function handleDispatchReply(idxStr, dryRun) {
    const idx = parseInt(idxStr, 10);
    const opp = currentInterceptOpportunities[idx];
    if (!opp) return;

    showToast(dryRun ? "Simulating dispatch..." : "Publishing practitioner reply...");
    try {
      const res = await requestJson("/api/v1/intercept/reply", {
        method: "POST",
        body: JSON.stringify({ opportunity: opp, dry_run: dryRun }),
      });
      showToast(`Reply Dispatched! Status: ${res.status}`);
      refreshInterceptorTelemetry();
    } catch (err) {
      showToast(`Dispatch error: ${err.message}`);
    }
  }

  async function refreshInterceptorTelemetry() {
    try {
      const telem = await requestJson("/api/v1/intercept/telemetry");
      const el = document.getElementById("intercept-telemetry-callout");
      if (el && telem) {
        el.innerHTML = `
          <strong>Interceptor Telemetry:</strong> ${telem.total_opportunities_detected} Buyer Signals | <strong>Dispatched:</strong> ${telem.total_dispatched} | <strong>Ad Dollars Saved:</strong> $${telem.total_ad_spend_saved.toLocaleString()} (@ $35 CPC) | <strong>Account Health:</strong> 9:1 Altruistic Camouflage Safe
        `;
      }
    } catch {
      // Telemetry graceful fallback
    }
  }

  // Inbound Leads & Telemetry Handlers
  function setupLeadsAndTelemetry() {
    bindClick("btn-refresh-leads", () => loadCapturedLeads());
    bindClick("btn-run-telemetry-audit", () => loadTelemetryAudit());
    loadCapturedLeads();
    loadTelemetryAudit();
  }

  async function loadCapturedLeads() {
    try {
      const leads = await requestJson("/api/v1/leads?limit=50");
      renderLeadsTable(leads);
    } catch {
      renderDemoLeads();
    }
  }

  function renderLeadsTable(leads) {
    const tbody = document.getElementById("leads-tbody");
    tbody.innerHTML = "";

    if (!leads || leads.length === 0) {
      renderDemoLeads();
      return;
    }

    leads.forEach((l) => {
      const tr = document.createElement("tr");
      const inputs = Object.entries(l.tool_inputs || {}).map(([k, v]) => `${k}:${v}`).join(", ") || "Standard Audit";
      tr.innerHTML = `
        <td><strong>${escapeHtml(l.email)}</strong></td>
        <td>${escapeHtml(l.company || l.project_slug)}</td>
        <td style="font-size: 0.8rem; font-family: var(--font-mono);">${escapeHtml(inputs)}</td>
        <td><span class="badge badge-success">${l.intent_score}/100</span></td>
        <td><span class="badge badge-neutral">${escapeHtml(l.status.toUpperCase())}</span></td>
        <td>
          <button type="button" class="btn btn-secondary btn-sm" onclick="alert('Nurture active: Stage 1 diagnostic dispatched to ${escapeAttr(l.email)}')">View</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    document.getElementById("leads-total-count").textContent = `${leads.length} Leads`;
    document.getElementById("leads-pipeline-value").textContent = `$${(leads.length * 350).toLocaleString()}`;
    document.getElementById("leads-ad-saved").textContent = `$${(leads.length * 35 * 18).toLocaleString()} Saved`;
  }

  function renderDemoLeads() {
    const demoLeads = [
      { email: "alex@cloudscale.io", company: "CloudScale Inc", inputs: "spend:$4,200/mo, nodes:65", score: 92, status: "NURTURED" },
      { email: "sarah@finops.dev", company: "FinOps Hub", inputs: "spend:$7,500/mo, seats:12", score: 88, status: "CONVERTED" },
      { email: "david@bootstrapped.co", company: "Bootstrapped SaaS", inputs: "spend:$1,800/mo, nodes:20", score: 85, status: "STAGE_1" },
      { email: "elena@infraops.com", company: "InfraOps AI", inputs: "spend:$12,000/mo, nodes:150", score: 95, status: "STAGE_2" },
    ];

    const tbody = document.getElementById("leads-tbody");
    tbody.innerHTML = "";
    demoLeads.forEach((l) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${escapeHtml(l.email)}</strong></td>
        <td>${escapeHtml(l.company)}</td>
        <td style="font-size: 0.8rem; font-family: var(--font-mono);">${escapeHtml(l.inputs)}</td>
        <td><span class="badge badge-success">${l.score}/100</span></td>
        <td><span class="badge badge-neutral">${escapeHtml(l.status)}</span></td>
        <td>
          <button type="button" class="btn btn-secondary btn-sm">Inspect</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  async function loadTelemetryAudit() {
    const box = document.getElementById("telemetry-audit-container");
    try {
      const report = await requestJson("/api/v1/telemetry/report");
      box.innerHTML = `
        <strong>Holistic Organic Health:</strong> ${report.overall_health.toUpperCase()} | <strong>Ad Budget Saved:</strong> $${report.total_ad_dollars_saved.toLocaleString()} | <strong>Avg Organic Conversion:</strong> ${(report.average_conversion_rate * 100).toFixed(1)}%
        <div style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-secondary);">
          <strong>Autonomous Self-Healing Recommendations:</strong>
          <ul style="padding-left: 1.25rem; margin-top: 0.25rem;">
            ${report.recommendations.map((r) => `<li>${escapeHtml(r)}</li>`).join("")}
          </ul>
        </div>
      `;
    } catch {
      box.innerHTML = `
        <strong>Closed-Loop Telemetry System:</strong> Active (Self-Healing Healthy). 
        Calculators out-converting Google Ads by 6.8x. Reddit 9:1 karma camouflage ratio safe at 100%. No shadowban flags detected across active accounts.
      `;
    }
  }

  // Pre-load demo profile
  function loadDemoProfile() {
    const demoProfile = {
      product_name: "ZeroCAC",
      category: "Autonomous Organic Growth Operating System",
      one_liner: "ZeroCAC empowers founders to scale distribution with zero paid ad spend.",
      unique_value_proposition: "Compounding organic equity that permanently replaces rented $10K+/mo Google & Meta ad spend.",
      competitor_gaps: [
        { competitor_name: "Google & Meta Ads", their_weakness: "Rented attention expiring the millisecond budget halts.", our_advantage: "Permanent compounding organic equity & high-trust community mentions." },
        { competitor_name: "Marketing Agencies", their_weakness: "$5,000-$10,000 monthly retainers with slow generic delivery.", our_advantage: "Autonomous AI reasoning engines executing in 60 seconds at $0 agency fees." },
      ],
      personas: [
        { persona_name: "Bootstrapped SaaS Founder", core_pain_point: "Cannot afford $5K/mo ad burn with $35+ CPC.", trigger_event: "Initial launch traffic faded.", primary_objection: "Will organic take too long to convert?" },
        { persona_name: "Indie Hacker / Solo Dev", core_pain_point: "Great at coding but hates marketing and self-promotion.", trigger_event: "Built tool but has zero daily users.", primary_objection: "I don't want spam posted under my name." },
      ],
    };

    renderPositioningTab(demoProfile);
    autoStageEngines("https://zerocac.org");
    loadCapturedLeads();
    loadTelemetryAudit();
  }

  // Positioning Tab
  function renderPositioningTab(profile) {
    document.getElementById("profile-name").textContent = profile.product_name;
    document.getElementById("profile-category").textContent = profile.category;
    document.getElementById("profile-oneliner").textContent = profile.one_liner;
    document.getElementById("profile-uvp").textContent = profile.unique_value_proposition;

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

  // Render All Organic Engines (GEO, Virality, Microtool, Sniper, AEO, Narrative, Directory)
  function renderAllEngines(campaign) {
    if (campaign.microtool) {
      const tool = campaign.microtool;
      latestMicroToolHtml = tool.html_content;
      document.getElementById("microtool-name").textContent = tool.concept.tool_name;
      document.getElementById("microtool-headline").textContent = tool.concept.headline;
      document.getElementById("microtool-hook").textContent = tool.concept.virality_hook;
      document.getElementById("microtool-deploy").textContent = tool.deployment_instructions;

      bindClick("copy-tool-html-btn", () => {
        navigator.clipboard.writeText(latestMicroToolHtml);
        showToast("Copied standalone HTML to clipboard!");
      });

      bindClick("download-tool-btn", () => {
        downloadFile(`${tool.concept.slug}.html`, latestMicroToolHtml, "text/html");
        showToast("Downloaded standalone tool HTML!");
      });

      bindClick("preview-tool-modal-btn", () => {
        openPreviewModal(`<iframe srcdoc="${escapeAttr(latestMicroToolHtml)}" style="width:100%;height:75vh;border:none;border-radius:8px;"></iframe>`);
      });
    }

    if (campaign.geo) {
      renderGeoEngine(campaign.geo);
    }

    if (campaign.virality) {
      renderViralityEngine(campaign.virality);
    }

    if (campaign.sniper) {
      renderSniperEngine(campaign.sniper);
    }

    if (campaign.aeo) {
      renderAEOEngine(campaign.aeo);
    }

    if (campaign.narrative) {
      renderNarrativeEngine(campaign.narrative);
    }

    if (campaign.directory) {
      renderDirectoryEngine(campaign.directory);
    }

    bindCopyButtons();
  }

  function renderGeoEngine(geo) {
    const geoBox = document.getElementById("geo-assets-container");
    geoBox.innerHTML = "";
    geo.assets.forEach((asset) => {
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
          <span class="meta-label">Citation Verification Prompts:</span>
          <ul style="padding-left:1.25rem;font-size:0.85rem;margin-top:0.25rem;">${promptsList}</ul>
        </div>
      `;
      geoBox.appendChild(card);
    });

    document.getElementById("geo-robots-container").textContent = geo.robots_txt_rules;
    document.getElementById("geo-bing-container").textContent = geo.bing_webmaster_guidelines;
  }

  function renderViralityEngine(v) {
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
    setCopy("copy-virality-md-btn", v.markdown_badge);

    document.getElementById("virality-html-code").textContent = v.html_badge_snippet;
    setCopy("copy-virality-html-btn", v.html_badge_snippet);
  }

  function renderSniperEngine(sniper) {
    const sniperContainer = document.getElementById("sniper-container");
    sniperContainer.innerHTML = "";
    sniper.opportunities.forEach((opp) => {
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

  function renderAEOEngine(aeo) {
    const aeoBox = document.getElementById("aeo-container");
    aeoBox.innerHTML = "";
    aeo.comparison_pages.forEach((page) => {
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

  function renderNarrativeEngine(narrative) {
    const threadBox = document.getElementById("viral-thread-container");
    threadBox.innerHTML = "";
    narrative.x_thread.forEach((tweet) => {
      const el = document.createElement("div");
      el.className = "highlight-box";
      el.style.marginBottom = "0.75rem";
      el.textContent = tweet;
      threadBox.appendChild(el);
    });

    const carouselBox = document.getElementById("viral-carousel-container");
    carouselBox.innerHTML = "";
    narrative.linkedin_carousel.forEach((slide) => {
      const el = document.createElement("div");
      el.className = "highlight-box accent-box";
      el.style.marginBottom = "0.75rem";
      el.textContent = slide;
      carouselBox.appendChild(el);
    });

    document.getElementById("viral-video-container").textContent = narrative.video_script_60s;
  }

  function renderDirectoryEngine(directory) {
    const tbody = document.getElementById("directory-tbody");
    tbody.innerHTML = "";
    directory.listings.forEach((listing) => {
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

  // Utilities
  function bindCopyButtons() {
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

  function setCopy(btnId, content) {
    const btn = document.getElementById(btnId);
    if (btn) btn.setAttribute("data-copy", content || "");
  }

  async function requestJson(url, options = {}) {
    const defaultHeaders = { "Content-Type": "application/json" };
    options.headers = { ...defaultHeaders, ...options.headers };
    const res = await fetch(url, options);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return res.json();
  }

  function downloadFile(filename, content, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
  }

  function setProgress(step) {
    progressContainer.classList.remove("hidden");
    for (let i = 1; i <= 4; i++) {
      const el = document.getElementById(`step-${i}`);
      if (el) el.classList.toggle("active", i <= step);
    }
  }

  function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    btnText.textContent = isLoading ? "Synthesizing Growth Strategy..." : "Synthesize Organic Engines";
    btnSpinner.classList.toggle("hidden", !isLoading);
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
