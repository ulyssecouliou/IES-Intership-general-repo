# Index de `docs/project/`

> Créé le 2026-08-16 (audit complet). Ce dossier contient ~50 documents accumulés ;
> beaucoup sont des instantanés datés. Cet index dit **quoi lire en premier** et
> **ce qui n'est qu'historique**, pour qu'une reprise ne s'y noie pas.

## À lire en premier (vivant, canonique)

| Document | Rôle |
|---|---|
| `HANDOVER_2026-08-28.md` | **Passation finale : état vérifié, commandes, limites et prochaines actions** |
| `FINAL_TRANSMISSION_RECEIPT_2026-08-28.md` | **Reçu final : contrôles exécutés, avertissements conservés et livrables générés** |
| `TRANSMISSION_CHECKLIST_2026-08-28.md` | **Checklist de remise IES : automatisé, propriétaire, VE, SIA et données restreintes** |
| `NEW_MAINTAINER_START_HERE.md` | **Parcours d'accueil : premières 30 minutes, environnement, commandes et responsabilités** |
| `AI_USAGE_AND_GOVERNANCE.md` | **Usage réel de Codex/Claude, absence d'IA au runtime, limites et supervision humaine** |
| `ARCHITECTURE_AND_RUNTIME_GUIDE.md` | **Architecture maintenue, flux client/SIA 4010 et règles d'extension** |
| `DATA_EVIDENCE_AND_LICENSING.md` | **Inventaire des données, preuves, e-mails, confidentialité et blocages de publication** |
| `TESTING_RELEASE_AND_OPERATIONS.md` | **Tests, documentation, paquet ZIP, smoke test VE, release et rollback** |
| `GITHUB_AND_OWNERSHIP_TRANSFER.md` | **Liens, accès, transfert IES, Actions, protection de main et visibilité** |
| `../../CLAUDE.md` | Doctrine non négociable (chargée à chaque session) |
| `../CLAUDE_REFERENCE.md` | Layout réel, workflow, conventions (corrigé 2026-08-16) |
| `../ADR-001-architecture-MSP.md` | Décision d'architecture (mono-processus VE, Tkinter, cas générés par script) |
| `AUDIT_COMPLET_2026-08-16.md` | **Audit complet + plan de remise en état P0→P3** |
| `CODEX_TO_CLAUDE_HANDOFF.md` | État de reprise le plus récent (chaîne Test 1, campagne SIA 4010) |
| `../../PROJECT_PLAN.md` | Plan de projet (⚠ §2 périmé, voir la bannière) |
| `ARCHITECTURE_380-2_vs_4010.md` | Relation entre les deux normes |
| `CLIENT_RUN_GUIDE.md` / `CLIENT_DEMO_RUNBOOK_EN.md` | Exécution côté client |

**Vérité d'architecture (rappel de l'audit) :** la production client vit
**entièrement dans `swiss_sia/`**. `engine/`+`ve_adapter/` = outillage de build
des références & recompute indépendant ; `ui/` = hérité (seuls `design.py`+
`tk_theme.py` servent) ; `core/` = mort.

## Guides thématiques (référence, vivant-ish)

- `SIA_MODEL_BUILDER_GUIDE.md`, `SWISS_REFERENCE_MODEL_ARCHITECTURE.md` — constructeur de modèle de référence.
- `GLAZING_EVIDENCE_GUIDE.md`, `MODEL_REMEDIATION_PLAYBOOK.md`, `SIA3802_CLIENT_TEMPLATE_REMEDIATION_EN.md` — remédiation modèle/vitrage.
- `VE_MODEL_INPUT_REQUIREMENTS_SIA3802_SIA4010.md`, `SIA4010_PHASE_B_VE_EXTRACTION_CONTRACT.md` — contrats d'entrée VE.
- `SIA4010_PDF_PREVALIDATION_STRATEGY.md`, `SIA4010_TESTS_AND_CLASSES_IMPLEMENTATION.md`, `SIA4010_OFFICIAL_PACKAGE_ACQUISITION_CHECKLIST.md` — SIA 4010.
- `MANAGER_REFERENCE_INTEGRATION.md`, `MANAGER_MULTILINGUAL_BRIEF.md`, `RELEASE_ACCEPTANCE_CHECKLIST.md` — livraison/manager.
- `REGISTRE_DEMANDES_EXTERNES.md`, `SIA_CORRESPONDANCE_ZWEIFEL_2026-08-12.md` — dépendances externes SIA (normes manquantes, clarifications).

## Historique / instantanés datés (contexte seulement — peut être périmé)

Ces fichiers sont des runbooks « ce soir », des matrices de complétion et des
statuts d'exécution figés à une date. Les lire pour l'historique, **pas** comme
l'état courant (préférer le handoff + l'audit ci-dessus) :

`MVP_COMPLETION_MATRIX.md`, `MVP_MANAGER_HANDOFF.md`, `MVP_RUSH_RUNBOOK_2026-08-13.md`,
`TONIGHT_SIA4010_EXECUTION_RUNBOOK_FR.md`, `HYBRID_EXECUTION_STATUS_20260811.md`,
`SIA_COMPLIANCE_EXECUTION_TRACKER.md`, `SIA4010_ENGINE_ALIGNMENT_2026-08-11.md`,
`SIA4010_CASE600_MVP_DEMO.md`, `SIA4010_CLASSES_1A_1B_RUNBOOK.md`,
`SIA4010_TEST1_SIX_CASES_EXECUTION_GUIDE.md`, `ZOER_32_C1_REMEDIATION_ACTION_PACK.md`,
`WAITING_FOR_OFFICIAL_EXCEL_ACTION_PLAN.md`, `OPEN_ITEMS_BACKLOG.md`,
`PROMPTS_CLAUDE_FIN_MVP.md`, `PROFESSIONAL_IMPLEMENTATION_PLAN.md`, et les autres
`SIA3802_*`/`SIA4010_*`/`SIA_*` datés.

> Recommandation P2 : déplacer les instantanés datés sous `docs/project/archive/`
> pour ne garder ici que le vivant. Non fait automatiquement (préservation des
> renvois et du worktree en cours) — à décider avec l'équipe.
