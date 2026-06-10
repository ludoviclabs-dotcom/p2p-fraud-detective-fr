"""Detection Studio — moteur de règles déterministe (Phase 4, ADR-0007).

Modules :
- `dsl` : format de règle YAML (RuleSpec Pydantic) + évaluation déterministe ;
- `testing` : exécution des cas de test embarqués d'une règle ;
- `backtest` : mesure d'impact sur dataset labellisé (faux positifs, volume) ;
- `store` : versions de règles avec lifecycle draft → tested → active,
  promotion 4-eyes (auteur ≠ approbateur) et journalisation audit log.

Le LLM (llm/rule_studio.py) ne fait que DRAFTER : tout ce qui engage
(compilation, tests, backtest, activation) est exécuté par ce code.
"""
