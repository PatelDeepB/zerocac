"""Autonomous Edge Deployment and Indexation module for ZeroCAC."""

from zerocac.deployers.cloudflare import CloudflarePagesDeployer
from zerocac.deployers.indexer import IndexNowClient, SitemapPinger
from zerocac.deployers.manager import EdgeDeploymentManager
from zerocac.deployers.models import (
    DeploymentArtifact,
    DeploymentProvider,
    DeploymentResult,
    IndexNowPayload,
)

__all__ = [
    "CloudflarePagesDeployer",
    "IndexNowClient",
    "SitemapPinger",
    "EdgeDeploymentManager",
    "DeploymentArtifact",
    "DeploymentProvider",
    "DeploymentResult",
    "IndexNowPayload",
]
