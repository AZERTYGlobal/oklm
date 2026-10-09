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
| `results/` | **Bruts archivés** des rapports, un fichier par prompt × moteur (textes produits par des moteurs d'IA tiers : le projet ne revendique aucune licence sur eux, voir la section Licensing de [`../README.md`](../README.md#licensing)). Seuls les miroirs `.md` sont versionnés ; les PDF restent en local (`.gitignore`). |
| `README.md` | Ce document. |

## Workflow pour traiter un rapport de prompt

1. **Localiser** le rapport brut du moteur de recherche (`Prompt N - <Moteur>.md|pdf`).
2. **Lire intégralement** le rapport (pas de survol). Pour un PDF : convertir d'abord en MD
   avec `markitdown "x.pdf" -o "x.md"` (plus léger en tokens) puis lire le `.md`.
3. **Archiver le brut** dans `results/`, nommé
   `Prompt NN - <titre court> (<Moteur>).md` (NN sur 2 chiffres). Pour un PDF, ne versionner
   que le miroir MD : `results/*.pdf` est exclu par `.gitignore`, le PDF reste en local.
   Nettoyer les artefacts de formatage **évidents et sûrs** (ex. numéros de
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

## État d'avancement (état du dépôt au 2026-10-10 ; dernier prompt traité : le 12, le 2026-09-02)

**Campagne reprise le 2026-09-02** : prompt 12 traité ; les blocs B puis C (dix prompts) ne sont
pas encore lancés, une session de triangulation par bloc. Perplexity n'est plus utilisé
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

Décisions consignées : **D1–D44**. D1–D30 : journal et `SPEC.md` alignés. Parmi D31–D44 (prompt 12),
quatre changent la structure du schéma et ont été **arbitrées par les mainteneurs le 2026-09-02**
(D32 schéma ouvert + lint strict, D34 préfixes `OKLM_`/`EXT_`/vendeur, D35 `metadata` seul, D31 sans
`minVersion`) ; D31 à D35 sont entrées dans le schéma 0.2, publié le 2026-10-05 (voir `../ROADMAP.md`,
item 4). Les autres ne sont pas toutes reprises : par exemple les formes localisées (D39),
`deprecated` (D37) et les profils (D40) ne figurent pas dans le schéma 0.2 ; le journal fait foi.

Livré par ailleurs depuis la campagne : schéma 0.2 et outil de migration, cinq exporteurs
(LDML, xkb, keylayout, `.klc`, Stream Deck), importeur LDML, site oklm.org.

## Points ouverts à traiter ensuite
- Reprendre la campagne sur les **10 prompts restants** (2, 3, 4, 5, 6, 7, 8, 13, 14, 15) par blocs.
- Nouvelles décisions à numéroter **à partir de D45**.

## Langue

Ce dossier de recherche est tenu en français ; la spécification et la documentation
du dépôt sont en anglais.

---

*Dernière mise à jour : 2026-10-10*
