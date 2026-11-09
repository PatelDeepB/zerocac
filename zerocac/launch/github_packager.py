"""Packager for Vector 1: Open-Source GitHub Repository Launch."""

import logging
from pathlib import Path
from zerocac.analyzer.models import ProductProfile
from zerocac.launch.models import GitHubLaunchPackage

logger = logging.getLogger(__name__)


class GitHubPackager:
    """Packages standalone micro-tools into open-source repositories for GitHub Explore."""

    def package_repository(
        self,
        profile: ProductProfile,
        tool_html: str,
        tool_slug: str,
        live_url: str,
    ) -> GitHubLaunchPackage:
        """Synthesize open-source repository assets including README and topics."""
        repo_name = f"{tool_slug}-app"
        tagline = f"Free standalone utility for {profile.one_liner[:80]}"
        topics = [
            "developer-tools",
            "open-source",
            "calculator",
            profile.category.lower().replace(" ", "-"),
            "growth",
            "zero-cac",
        ]

        readme = self._compile_readme(profile, tool_slug, live_url)

        return GitHubLaunchPackage(
            repo_name=repo_name,
            tagline=tagline,
            topics=topics,
            readme_markdown=readme,
            license_type="Apache-2.0",
        )

    def export_repository(
        self,
        package: GitHubLaunchPackage,
        tool_html: str,
        output_dir: Path,
    ) -> Path:
        """Write complete repository structure to disk ready for `git push`."""
        repo_dir = output_dir / package.repo_name
        repo_dir.mkdir(parents=True, exist_ok=True)

        (repo_dir / "index.html").write_text(tool_html, encoding="utf-8")
        (repo_dir / "README.md").write_text(package.readme_markdown, encoding="utf-8")
        (repo_dir / "LICENSE").write_text(self._get_apache_license(), encoding="utf-8")

        logger.info("Exported GitHub repository bundle to %s", repo_dir)
        return repo_dir

    def _compile_readme(self, profile: ProductProfile, slug: str, live_url: str) -> str:
        """Compile comprehensive, high-conversion GitHub README."""
        return (
            f"# {slug.replace('-', ' ').title()}\n\n"
            f"[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)\n"
            f"[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com)\n"
            f"[![Live Demo](https://img.shields.io/badge/Live-Demo_Application-success.svg)]({live_url})\n\n"
            f"> {profile.one_liner}\n\n"
            f"## Why This Exists\n"
            f"Most teams face acute pain with: *{profile.core_problem}*\n\n"
            f"Instead of locking analytical tooling behind expensive monthly subscriptions, "
            f"this repository provides a standalone, client-side calculator that runs 100% locally in your browser.\n\n"
            f"## Quick Start (Run Locally)\n"
            f"Clone the repo and open `index.html` in any browser, or run:\n"
            f"```bash\n"
            f"python -m http.server 8080\n"
            f"# Open http://localhost:8080\n"
            f"```\n\n"
            f"## Live Production Deployment\n"
            f"The production version is hosted at: [{live_url}]({live_url})\n\n"
            f"## License\nApache-2.0 open-source license."
        )

    def _get_apache_license(self) -> str:
        """Return standard Apache-2.0 license text header."""
        return (
            "Copyright 2026 ZeroCAC Authors\n\n"
            "Licensed under the Apache License, Version 2.0 (the 'License');\n"
            "you may not use this file except in compliance with the License.\n"
            "You may obtain a copy of the License at\n\n"
            "    http://www.apache.org/licenses/LICENSE-2.0\n"
        )
