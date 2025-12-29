// Export container registry configuration
// This file can be used for dynamic config generation with environment-specific values

module.exports = {
  containers: [
    {
      name: "nginx-alpine",
      image: "nginx:alpine",
      scanners: ["trivy", "grype", "syft"],
      allow_failure: false,
      fail_on_severity: "high",
    },
    {
      name: "ubuntu-latest",
      image: "ubuntu:latest",
      scanners: ["trivy", "grype"],
      allow_failure: true,
      fail_on_severity: "medium",
    },
    {
      name: "ghcr-runner",
      image: "ghcr.io/actions/actions-runner:latest",
      registry_username_secret: "GHCR_USERNAME",
      registry_password_secret: "GITHUB_TOKEN",
      scanners: ["trivy"],
      allow_failure: false,
      fail_on_severity: "critical",
    }
  ],
};
