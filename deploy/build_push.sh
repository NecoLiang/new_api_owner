#!/usr/bin/env bash
# Build linux/amd64 image locally (buildx, native Go cross-compile) and push
# to Aliyun ACR. Run from repo root on the developer mac. Must be
# `docker login`ed to the registry first.
#
#   ./deploy/build_push.sh           # -> :latest
#   ./deploy/build_push.sh v2        # -> :v2 and :latest
set -euo pipefail

REGISTRY="${REGISTRY:-crpi-g05sy1sxtgiaw99l.cn-wulanchabu.personal.cr.aliyuncs.com}"
NAMESPACE="${NAMESPACE:-kaizo}"
REPO="${REPO:-kaizo_newapi}"
IMAGE="${REGISTRY}/${NAMESPACE}/${REPO}"

TAG="${1:-latest}"
TAGS=(-t "${IMAGE}:${TAG}")
if [[ "${TAG}" != "latest" ]]; then
    TAGS+=(-t "${IMAGE}:latest")
fi

cd "$(dirname "$0")/.."

echo "==> building ${IMAGE}:${TAG} (linux/amd64)"
docker buildx build \
    --platform=linux/amd64 \
    "${TAGS[@]}" \
    --push \
    .

echo "==> pushed:"
printf '    %s:%s\n' "${IMAGE}" "${TAG}"
if [[ "${TAG}" != "latest" ]]; then
    printf '    %s:latest\n' "${IMAGE}"
fi

echo ""
echo "Next step on server:"
echo "  ssh server8 'cd /root/new-api && docker compose pull && docker compose up -d'"
