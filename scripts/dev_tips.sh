#!/usr/bin/env bash
# Shell welcome message for Bijmantra developers
if [ -z "${BIJMANTRA_DEV_TIPS_SHOWN:-}" ]; then
  export BIJMANTRA_DEV_TIPS_SHOWN=1
  echo "💡 Bijmantra Dev Tips:"
  echo "   - make dev            # start infrastructure"
  echo "   - make dev-backend    # run API with hot reload"
  echo "   - make dx-check       # run DX automation checks"
  echo "   - make test-backend   # run backend test suite"
fi
