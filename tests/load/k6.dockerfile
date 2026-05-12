# Image k6 reproductible pour les tests de charge.
#
# Build : docker build -f tests/load/k6.dockerfile -t p2pfd-k6 tests/load/
# Run   : docker run --rm --network=host p2pfd-k6 run /scripts/api_smoke.js \
#           -e API_BASE_URL=http://localhost:8000 -e API_SECRET=$API_SECRET
FROM grafana/k6:0.55.0

COPY api_smoke.js /scripts/api_smoke.js

# Pas d'ENTRYPOINT override — l'image grafana/k6 utilise déjà `k6` comme entrypoint.
CMD ["run", "/scripts/api_smoke.js"]
