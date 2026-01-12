#!/usr/bin/env bash
#
# Mirror the hardening Dagger module to GHE container registries
#
# Run this script from a machine that has access to both:
# - ghcr.io (source)
# - Your GHE container registries (destinations)
#
# Usage:
#   ./mirror-to-ghe.sh 2.10.0
#   ./mirror-to-ghe.sh latest

set -euo pipefail

VERSION="${1:-latest}"
SOURCE_IMAGE="ghcr.io/huntridge-labs/hardening:${VERSION}"

# List of GHE registries to mirror to
# Edit this list for your organization
GHE_REGISTRIES=(
  "ghe1.company.com/huntridge-labs/hardening"
  "ghe2.company.com/huntridge-labs/hardening"
  # Add more as needed
)

echo "=== Mirroring Hardening Module ==="
echo "Source: $SOURCE_IMAGE"
echo "Version: $VERSION"
echo ""

# Pull from source
echo "Pulling from ghcr.io..."
docker pull "$SOURCE_IMAGE"

# Push to each GHE registry
for registry in "${GHE_REGISTRIES[@]}"; do
  TARGET_IMAGE="${registry}:${VERSION}"
  echo ""
  echo "Pushing to: $TARGET_IMAGE"

  # Tag for this registry
  docker tag "$SOURCE_IMAGE" "$TARGET_IMAGE"

  # Push (assumes you're already logged in)
  if docker push "$TARGET_IMAGE"; then
    echo "✓ Successfully pushed to $TARGET_IMAGE"
  else
    echo "✗ Failed to push to $TARGET_IMAGE"
    echo "  Make sure you're logged in: docker login ${registry%%/*}"
  fi
done

echo ""
echo "=== Mirror Complete ==="
echo ""
echo "To use on GHE, set HARDENING_IMAGE in your workflow:"
for registry in "${GHE_REGISTRIES[@]}"; do
  echo "  HARDENING_IMAGE: ${registry}:${VERSION}"
done
