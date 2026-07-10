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

## État d'avancement (au 2026-06-07)

| Prompt | Sujet | Statut |
|---|---|---|
| 1 | Pipeline & codes de touches | ✅ triangulé (3 moteurs) |
| 9 | Formats d'échange & authoring (LDML) | ✅ triangulé (3 moteurs) |
| 11 | Normes de jure (ISO 9995…) | ✅ triangulé (3 moteurs) |
| **10** | IME & scripts complexes | ⏳ **lot en cours** |
| **16** | Géométrie physique (KLE/info.json/VIA) | ⏳ **lot en cours** |
| 6 | Firmware (QMK/ZMK) | ⬜ à faire — **tranche D10** |
| 12 | Conception du format + conformance | ⬜ à faire |
| 2, 3, 4, 5 | OS desktop (Win/macOS/Linux/autres) | ⬜ à faire (exporteurs) |
| 7, 8, 15 | Mobile / embarqué / web | ⬜ à faire |
| 13, 14 | Gouvernance / besoins industrie | ⬜ à faire |

Décisions consignées : **D1–D14** (voir le journal). Synthèse rapide :
- **D1** ✅ identifiant de touche = **numéro ISO/IEC 9995-1** (`D01`…) canonique + `hid` obligatoire + alias XKB.
- **D2/D3** ✅ modèle ISO `(group, level)` verbatim.
- **D4** ✅ dead keys/compositions séparées du mapping.
- **D5** ✅ géométrie en alias, position en numéro ISO.
- **D7** 🔴 déléguer le cœur texte à **LDML Keyboard 3.0** (cible **UTS #35 Part 7 v48.2**, racine `keyboard3`) — ne pas réinventer transforms/reorder/markers.
- **D8** ✅ couche méta « envelope » (légendes dynamiques, pédagogie, IA scopée, a11y).
- **D9** ✅ architecture en couches (core → LDML / extended / metadata).
- **D10** 🔴 **firmware séparé** (namespace d'extension) — **arbitrage de périmètre à confirmer via le prompt 6**.
- **D11** ✅ frame keys (Fn, numpad…) hors LDML → extension OKLM.
- **D12** ✅ publier les « frontières de redondance ».
- **D13** ✅ déclaration de conformance (ISO 9995 part-based + national).
- **D14** ✅ réutiliser la terminologie ISO 9995.

## Points ouverts à traiter ensuite
- **D10** : décision de périmètre firmware → la fermer avec le **prompt 6**.
- **Migrations `SPEC.md`** : ✅ appliquées le 2026-07-10 (D1, D2/D14, D7, D11, D13, D23) — voir
  [`../schemas/Zones instables v0.1.md`](../schemas/Zones%20instables%20v0.1.md) pour le détail
  et l'état de validation (15/15 tests).

## Langue

Ce dossier de recherche est tenu en français ; la spécification et la documentation
du dépôt sont en anglais.

---

*Dernière mise à jour : 2026-07-10*
