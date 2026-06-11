"""LLM utilities — socle IA de confiance (ADR-0007) + génération narrative.

Modules :
- `structured` : génération structurée garantie (schéma Pydantic + redaction
  PII fail-closed + validation de provenance) ;
- `schemas` : schémas Pydantic des sorties IA (source de vérité unique) ;
- `provenance` : source pack + validation en code des citations ;
- `ai_ledger` : journalisation des appels IA dans l'audit log signé ;
- `audit_explainer` : feature pilote — traduction du verdict de vérification
  cryptographique en langage audit ;
- `narrative_generator` : narration ISA 240 par fournisseur (historique).
"""
