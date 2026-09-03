# OKLM — Campagne de deep research (dossier `research/`)

> But : alimenter la conception du modèle OKLM (voir `../SPEC.md`, `../README.md`)
> avec une compréhension exhaustive de l'écosystème clavier, via des
> deep research recoupées sur plusieurs moteurs (Perplexity, ChatGPT, Gemini).
>
> **Document de reprise** : à lire en premier par toute IA/personne qui continue le travail.

## Fichiers du dossier

| Fichier | Rôle |
|---|---|
| `Deep Research Prompts.md` | Les **16 prompts** (source). Carte + ordre suggéré en tête. |
| `Décisions de conception — deep research.md` | **Journal des décisions** (D1…), source vivante pour `SPEC.md`. |
| `results/` | **Bruts archivés** des rapports, un fichier par prompt × moteur. |
| `README.md` | Ce document. |

## Workflow pour traiter un rapport de prompt

1. **Localiser** le rapport brut du moteur de recherche (`Prompt N - <Moteur>.md|pdf`).
2. **Lire intégralement** le rapport (pas de survol). Pour un PDF : convertir d'abord en MD
   avec `markitdown "x.pdf" -o "x.md"` (plus léger en tokens) puis lire le `.md`.
3. **Archiver le brut** dans `results/`, nommé
   `Prompt NN - <titre court> (<Moteur>).md` (NN sur 2 chiffres). Pour un PDF, copier le PDF
   **et** le miroir MD. Nettoyer les artefacts de formatage **évidents et sûrs** (ex. numéros de
   diagramme rendus en `[^1]`), sinon laisser le brut fidèle et **signaler** l'artefact.
4. **Trianguler** dès qu'on a ≥ 2 moteurs : comparer convergences / divergences / apports,
   trancher les divergences factuelles par majorité ou source primaire.
5. **Consigner** dans `Décisions de conception — deep research.md` :
   - ajouter/mettre à jour la ligne de **provenance** (table en tête) ;
   - ajouter une **section `## Prompt N`** avec les décisions, en numérotant `Dxx` **à la suite**
     (dernier utilisé : **D44**) ;
   - lister les **points à confirmer** et les **tensions avec `SPEC.md`**.

### Légende des statuts de décision
- 🟡 **Provisoire** : 1 seul moteur, recoupement à venir.
- 🟢 **Confirmée** : triangulation (≥ 2-3 moteurs) ou source primaire vérifiée → intégrable à `SPEC.md`.
- 🔴 **À arbitrer** : tension avec `SPEC.md` ou décision de périmètre projet (humain requis).

## État d'avancement (au 2026-09-02)

**Campagne reprise le 2026-09-02** (roadmap OKLM, décision 7) : prompt 12 traité ; blocs B puis C
à partir d'octobre 2026, une session de triangulation par bloc. Perplexity n'est plus utilisé
(pas d'abonnement) : les trois moteurs sont ChatGPT, Claude et Gemini.

| Prompt | Sujet | Statut |
|---|---|---|
| 1 | Pipeline & codes de touches | ✅ triangulé (≥ 2-3 moteurs) |
| 9 | Formats d'échange & authoring (LDML) | ✅ triangulé (≥ 2-3 moteurs) |
| 10 | IME & scripts complexes | ✅ triangulé (≥ 2-3 moteurs) |
| 11 | Normes de jure (ISO 9995…) | ✅ triangulé (≥ 2-3 moteurs) |
| 16 | Géométrie physique (KLE/info.json/VIA) | ✅ triangulé (≥ 2-3 moteurs) |
| 12 | Conception du format + conformance | ✅ triangulé (3 moteurs, 2026-09-02) — D31–D44, 4 points 🔴 |
| 2, 3, 4, 5, 6, 7, 8, 13, 14, 15 | Reste de la carte (10 prompts) | ⬜ restants (octobre 2026, blocs B puis C) |

Décisions consignées : **D1–D44**. D1–D30 : journal et `SPEC.md` alignés. **D31–D44 (prompt 12) ne
sont pas migrées** : quatre d'entre elles changent la structure du schéma et ont été **arbitrées par
Antoine le 2026-09-02** (D32 schéma ouvert + lint strict, D34 préfixes `OKLM_`/`EXT_`/vendeur,
D35 `metadata` seul, D31 sans `minVersion`) ; elles entrent en v0.2 (chantier C5 de la roadmap).

Livré par ailleurs pendant la campagne : draft OKLM 0.1, exporteurs v1 (LDML/xkb/keylayout),
schéma de rapport 0.2, site oklm.org.

## Points ouverts à traiter ensuite
- Reprendre la campagne sur les **10 prompts restants** (2, 3, 4, 5, 6, 7, 8, 13, 14, 15) par blocs.
- Nouvelles décisions à numéroter **à partir de D45**.

## Langue

Ce dossier de recherche est tenu en français ; la spécification et la documentation
du dépôt sont en anglais.

---

*Dernière mise à jour : 2026-09-02*
