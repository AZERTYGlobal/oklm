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
     (dernier utilisé : **D14**) ;
   - lister les **points à confirmer** et les **tensions avec `SPEC.md`**.

### Légende des statuts de décision
- 🟡 **Provisoire** : 1 seul moteur, recoupement à venir.
- 🟢 **Confirmée** : triangulation (≥ 2-3 moteurs) ou source primaire vérifiée → intégrable à `SPEC.md`.
- 🔴 **À arbitrer** : tension avec `SPEC.md` ou décision de périmètre projet (humain requis).

## État d'avancement (au 2026-07-11)

**Campagne en pause, à reprendre** (décision Antoine 2026-07-11).

| Prompt | Sujet | Statut |
|---|---|---|
| 1 | Pipeline & codes de touches | ✅ triangulé (≥ 2-3 moteurs) |
| 9 | Formats d'échange & authoring (LDML) | ✅ triangulé (≥ 2-3 moteurs) |
| 10 | IME & scripts complexes | ✅ triangulé (≥ 2-3 moteurs) |
| 11 | Normes de jure (ISO 9995…) | ✅ triangulé (≥ 2-3 moteurs) |
| 16 | Géométrie physique (KLE/info.json/VIA) | ✅ triangulé (≥ 2-3 moteurs) |
| 2, 3, 4, 5, 6, 7, 8, 12, 13, 14, 15 | Reste de la carte (11 prompts) | ⬜ restants |

Décisions consignées : **D1–D30** (journal et `SPEC.md` alignés — voir le journal pour le détail
prompt par prompt).

Livré par ailleurs pendant la campagne : draft OKLM 0.1, exporteurs v1 (LDML/xkb/keylayout),
schéma de rapport 0.2, site oklm.org.

## Points ouverts à traiter ensuite
- Reprendre la campagne sur les **11 prompts restants** (2, 3, 4, 5, 6, 7, 8, 12, 13, 14, 15).
- Nouvelles décisions à numéroter **à partir de D31**.

## Langue

Ce dossier de recherche est tenu en français ; la spécification et la documentation
du dépôt sont en anglais.

---

*Dernière mise à jour : 2026-07-11*
