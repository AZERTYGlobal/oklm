# OKLM — Décisions de conception issues des deep research

> Synthèse vivante des arbitrages de conception extraits des résultats de deep research.
> Chaque décision reste **provisoire** tant que le prompt source n'a pas été recoupé sur un
> second moteur. Ne rien figer dans `SPEC.md` avant de passer une décision au statut
> « confirmée ».

## Légende des statuts

- 🟡 **Provisoire** : issu d'un seul moteur, à recouper.
- 🟢 **Confirmée** : recoupée sur ≥ 2 moteurs (ou source primaire vérifiée), intégrable à `SPEC.md`.
- 🔴 **À arbitrer** : tension avec l'état actuel de `SPEC.md`, décision humaine requise.

## Provenance des résultats

| Prompt | Moteur(s) | Date | Statut | Résultat brut |
|---|---|---|---|---|
| 1 — Pipeline & codes de touches | Perplexity + ChatGPT + Gemini | 2026-06-07 | 🟢 recoupé (triangulation 3 moteurs) | [Perplexity](results/Prompt%2001%20-%20Input%20pipeline%20%26%20key%20codes%20%28Perplexity%29.md) · [ChatGPT](results/Prompt%2001%20-%20Input%20pipeline%20%26%20key%20codes%20%28ChatGPT%29.md) · [Gemini](results/Prompt%2001%20-%20Input%20pipeline%20%26%20key%20codes%20%28Gemini%29.md) |
| 9 — Formats d'échange & authoring | Perplexity + ChatGPT + Gemini | 2026-06-07 | 🟢 recoupé (triangulation 3 moteurs) | [Perplexity](results/Prompt%2009%20-%20Interchange%20formats%20%26%20authoring%20tools%20%28Perplexity%29.md) · [ChatGPT](results/Prompt%2009%20-%20Interchange%20formats%20%26%20authoring%20tools%20%28ChatGPT%29.md) · [Gemini](results/Prompt%2009%20-%20Interchange%20formats%20%26%20authoring%20tools%20%28Gemini%29.md) |
| 10 — IME & saisie des scripts complexes | Perplexity + ChatGPT + Gemini | 2026-06-07 | 🟢 recoupé (triangulation 3 moteurs) | [Perplexity](results/Prompt%2010%20-%20IME%20and%20complex-script%20input%20%28Perplexity%29.md) · [ChatGPT](results/Prompt%2010%20-%20IME%20and%20complex-script%20input%20%28ChatGPT%29.md) · [Gemini](results/Prompt%2010%20-%20IME%20and%20complex-script%20input%20%28Gemini%29.md) |
| 11 — Normes de jure (ISO 9995…) | Perplexity + ChatGPT + Gemini | 2026-06-07 | 🟢 recoupé (triangulation 3 moteurs) | [Perplexity](results/Prompt%2011%20-%20De%20jure%20keyboard%20standards%20%28Perplexity%29.md) · [ChatGPT](results/Prompt%2011%20-%20De%20jure%20keyboard%20standards%20%28ChatGPT%29.md) · [Gemini](results/Prompt%2011%20-%20De%20jure%20keyboard%20standards%20%28Gemini%29.md) |
| 16 — Géométrie physique des claviers | Perplexity + ChatGPT + Gemini | 2026-06-07 | 🟢 recoupé (triangulation 3 moteurs) | [Perplexity](results/Prompt%2016%20-%20Physical%20keyboard%20geometry%20description%20formats%20%28Perplexity%29.md) · [ChatGPT](results/Prompt%2016%20-%20Physical%20keyboard%20geometry%20description%20formats%20%28ChatGPT%29.md) · [Gemini](results/Prompt%2016%20-%20Physical%20keyboard%20geometry%20description%20formats%20%28Gemini%29.md) |

---

## Prompt 1 — Pipeline d'entrée & codes de touches

> Sources : Perplexity + ChatGPT + Gemini, 2026-06-07. Statut global : 🟢 **confirmé par
> triangulation** (3 moteurs convergents sur le fond). Les décisions ci-dessous sont
> intégrables à `SPEC.md`. **D1 tranché le 2026-06-07** (cf. ci-dessous). Reste **D2** à acter
> côté `SPEC.md` (alignement de la terminologie des niveaux sur ISO 9995).

### Décisions retenues (provisoires)

- **D1 — Identifiant physique de touche.** ✅ **TRANCHÉ (2026-06-07, affiné par Prompt 11)**
  **Clé canonique = numéro de touche ISO/IEC 9995-1** (grille de référence) — ex. `D01` (Q),
  `C00` (Caps), `B00` (touche ISO à gauche de Z), `E01` (1), `C12` (Ç ABNT) — **avec un champ
  `hid` (USB HID Usage ID, page 0x07) OBLIGATOIRE** comme ancre machine non ambiguë, un **alias
  XKB** (`AD01`…) optionnel pour l'export Linux, et la **géométrie** en alias (cf. D5).
  Raison : la grille ISO 9995-1 est le **standard de jure** de désignation de position, utilisé
  par toutes les normes nationales (NF Z71-300, DIN 2137…) ; lisible, versionnable, aligné sur
  les déclarations de conformité. Le `hid` obligatoire préserve l'export et désambiguïse
  l'international (ABNT Ro 0x87 ≠ touche ISO B00). **Les 3 moteurs des prompts 1 ET 11
  convergent** sur « numéro ISO canonique + HID ancre ».
  → ⚠️ **Évolution vs 1ʳᵉ formulation** : on avait d'abord retenu le **nom XKB** (`AD01`) ; le
  prompt 11 montre que la grille **ISO 9995-1** (`D01`) est plus normative et que XKB en
  **diffère** (préfixe de section, colonnes 00 vs 01). → notation canonique = **ISO**, XKB = alias.
  → **Implication `SPEC.md`** (à appliquer) : migrer les ids `"C01"` → numéros ISO 9995-1
  (`"D01"`, `"C00"`…), ajouter `hid` **obligatoire**, `xkb` et `geometry` optionnels sur l'objet
  `Key`. Convention d'extension pour les touches **hors page 0x07** (Fn invisible OS, touches
  média/consumer page 0x0C).

- **D2 — Modèle de niveaux (shift levels).** 🟢🔴 (confirmé par les 3 moteurs)
  Adopter le modèle **ISO/IEC 9995 / XKB** : Level 1 (base), Level 2 (Shift), Level 3
  (AltGr / Level3 Select), Level 4 (Shift + Level 3), Level 5/6 optionnels. Nommer les
  modificateurs par **fonction** (`Level2Shift`, `Level3Shift`, `Level5Shift`, `CapsLock`,
  `NumLock`), pas par la touche physique qui les active.
  → **Tension avec `SPEC.md`** : les `layers` actuels sont nommés `base/shift/altgr/shiftAltgr/caps`.
  À arbitrer : aligner sur la terminologie ISO 9995 (recommandé pour la conformité) ou garder
  des noms « familiers ».

- **D3 — Groupes ≠ niveaux.** 🟢
  Modéliser les **groupes** XKB (keymaps alternatives complètes, ex. multi-scripts)
  séparément des niveaux (variantes shiftées d'un même keymap). Ne pas confondre les deux axes.

- **D4 — Dead keys & composition séparées du mapping.** 🟢 (cohérent avec SPEC)
  Une touche morte produit un **jeton de touche morte** à un niveau donné, pas un caractère.
  La table de composition est une liste ordonnée séparée `(jeton, caractère base) → sortie`.
  Distinguer trois mécanismes : dead keys définies dans le layout, séquences Compose externes,
  ligatures (une touche → plusieurs codepoints, façon `pLigature` Windows).
  → **Recoupement** : prévoir une *politique d'annulation* annotable (X11 « avale » le keysym
  qui annule la séquence, Windows rejoue ≈ la sortie de la touche morte — comportements **non
  identiques**), et, pour l'interop forte (bureau distant, testeurs, jeux), une option de
  résolution de la composition en *user-space* plutôt que de dépendre de l'OS.
  → Valide l'orientation `deadKeys` de `SPEC.md`.

- **D5 — Métadonnées de géométrie obligatoires.** 🟢
  Le champ `geometry` (ANSI / ISO / JIS / ABNT / custom) est indispensable : il indique au
  consommateur quelles touches supplémentaires existent (`<LSGT>` en ISO, touches japonaises
  en JIS, touches ABNT C1/C2). Omettre la géométrie = bindings silencieusement manquants.

- **D6 — Cross-référence OS optionnelle.** 🟢
  Prévoir un bloc `os_mappings` optionnel par touche (Windows scancode + VK, macOS CGKeyCode,
  Linux evdev) pour faciliter exporters et débogage, sans en faire la source de vérité.

### Checklist de validation du schéma (les 10 « traps » du rapport)

À vérifier que le schéma OKLM gère explicitement chacun de ces pièges :

- [ ] **AltGr vs Ctrl+Alt** : déclarer si Level 3 s'active par Right Alt seul ou par Ctrl+Right Alt (conflit raccourcis Windows `KLLF_ALTGR`).
- [ ] **Pas d'AltGr natif sur macOS** : mapper explicitement Option (`kVK_Option`) → Level 3 à l'export macOS.
- [ ] **Offset X11 +8** : tracer la conversion evdev ↔ X11 keycode de façon cohérente.
- [ ] **Plafond 255 sur X11** : capper / détecter les keycodes evdev > 247 (Wayland/libxkbcommon relâche la limite).
- [ ] **Sémantique Caps Lock** : `alphabetic` vs `shift_lock` (AZERTY) vs `locale_specific` (turc İ/ı). Défaut = `alphabetic`, override par layout.
- [ ] **Pas de correspondance numérique inter-OS** : ne jamais supposer d'égalité entre VK / CGKeyCode / evdev.
- [ ] **Scancodes inaccessibles sur macOS** : ne pas dépendre du scancode côté macOS (seuls CGKeyCode + sortie caractère sont exposés).
- [ ] **JIS & ABNT** : extensions de géométrie spécifiques (touches japonaises, ABNT C1/C2).
- [ ] **Contournement IME** : le modèle couvre le mapping *pré-IME* uniquement ; l'intégration IME est orthogonale (cf. prompt 10).
- [ ] **État dead-key per-thread (Windows)** : `ToUnicodeEx()` modifie l'état clavier ; prévu pour les exporters/testeurs.
- [ ] **Swap ISO macOS (Grave ↔ Section)** : sur clavier ISO, macOS échange `kVK_ANSI_Grave` (0x32) et `kVK_ISO_Section` (0x0A) ; l'exporteur macOS doit dé-permuter selon la géométrie. *(apport recoupement Gemini + ChatGPT)*
- [ ] **ABNT « Ro » ≠ ISO `<LSGT>`** : la touche `/?` ABNT2 est HID 0x87 (International1, evdev `KEY_RO`), à **ne pas** normaliser vers `<LSGT>` / `VK_OEM_102` (0x64) sous peine de casser la saisie. *(apport recoupement Gemini)*
- [ ] **JIS — 5 touches dédiées** : Muhenkan, Henkan, Hiragana/Katakana, Ro, Yen ont des HID usages globalement uniques (0x87–0x8B + LANG) ; ne pas les confondre avec des OEM génériques.

### Bonus directement réutilisable

Le rapport propose en § 8.5 une **structure de format portable** (metadata + keys[levels] +
composition + os_mappings) qui recoupe largement les objets de `SPEC.md`. À utiliser comme
point de comparaison lors de la prochaine itération de la spec.

### Résolutions issues du recoupement (triangulation 3 moteurs)

- ✅ **« ISO/IEC 9995-1:2026 »** : **non confirmé**. Ni ChatGPT ni Gemini ne mentionnent
  d'édition 2026 (ils citent « ISO/IEC 9995 » sans millésime, ou la version 2009). Traiter le
  « :2026 » de Perplexity comme **probable hallucination** ; retenir l'édition **2009** sauf
  preuve d'une édition plus récente sur iso.org.
- ⚠️ **Version des HID Usage Tables** : les 3 moteurs divergent — Perplexity « 1.21 »,
  ChatGPT « 1.4 (2023-01-26) », Gemini cite l'URL `hut1_5.pdf` (→ 1.5). Le « 1.21 » est
  **obsolète** ; version courante = **≥ 1.4 (probablement 1.5)**. À verrouiller sur usb.org
  avant citation dans la spec (contenu de la page 0x07 stable → non bloquant).
- ✅ **Tableau croisé de codes** : valeurs **concordantes** sur les 3 moteurs (Q, A, Space,
  Enter, Caps, `<LSGT>`…). Aucune contradiction relevée.
- ✅ **D2 / D3 / D4 / D5 / D6** : confirmées par les 3 moteurs.
- ✅ **D1** : **tranché le 2026-06-07** — clé = nom de position lisible (XKB/ISO 9995) + `hid`
  obligatoire (cf. bloc D1).
- 🔴 **D2** : reste à acter côté `SPEC.md` (aligner la terminologie des niveaux sur ISO 9995).

---

## Prompt 9 — Formats d'échange & outils d'authoring

> Sources : Perplexity + ChatGPT + Gemini, 2026-06-07. Statut : 🟢 **confirmé par triangulation
> (3 moteurs)**. Orientation stratégique forte et convergente :
> **OKLM = enveloppe d'authoring qui délègue le cœur de transformation de texte à LDML
> Keyboard 3.0 et ajoute une couche de métadonnées que LDML ne couvre pas.**

### Décisions retenues

- **D7 — Déléguer le cœur interchange à LDML 3.0 (isomorphisme).** 🟢🔴
  Le cœur texte d'OKLM (base mapping, niveaux, dead keys, transforms contextuels, reorder
  Indic/Brahmic, markers, UnicodeSet, display statique, locale, tests, flicks tactiles) doit
  **se compiler en LDML Keyboard 3.0 valide** (mapping 1:1). **Ne JAMAIS réinventer** le
  langage de transforms, les poids de reorder (attribut `order`), les markers, ni la notation
  UnicodeSet (`\u{...}`, `uset`). Réinventer = standard parallèle = redondance (les 2 moteurs
  l'affirment fortement).
  → **Tension `SPEC.md`** : `deadKeys` / `compositions` actuels → les modéliser de façon
  isomorphe à LDML `<transforms>` / markers plutôt qu'un modèle propre.

- **D8 — Valeur ajoutée OKLM = couche méta « envelope ».** 🟢 (confirmé 3 moteurs)
  Zones réellement sous-couvertes, à ajouter comme métadonnées **strippées à l'export LDML**
  mais préservées pour les consommateurs non-OS :
  - **Légendes dynamiques** (LDML `<display>` est statique) — display conditionnel par mode/état.
  - **Pédagogie** : `fingerAssignment`, `homeRowAnchor`, `lesson`/`curriculumLevel`,
    `difficulty`, `mnemonic`.
  - **IA scopée** : métriques d'effort par touche + n-gram (Perplexity) **et** `semanticIntent`
    (`math_operator`, `ai_prompt_trigger` — Gemini). **PAS** de prédiction/autocorrect (IME, hors scope).
  - **Accessibilité** : LDML 3.0 déclare l'accessibilité « not yet included » (ChatGPT) → espace
    légitime pour des annotations a11y dans OKLM.
  - **Fan-out multi-cibles** depuis une source JSON unique, validée par JSON Schema. ⚠️ Nuance
    (ChatGPT) : « source unique qui fan-out » est déjà occupé (kalamine/kbdgen/KLFC/Keyman) ; la
    justification OKLM = fan-out **vers LDML + la longue traîne** (OS, mobile, remappers, firmware).
  → Garde-fou : pédagogie / IA / a11y = **extensions séparables**, jamais cœur (anti scope-creep).

- **D9 — Architecture en couches.** 🟢
  `core/` (→ LDML 3.0 → consommateurs OS/mobile) + `extended/` (→ kalamine, kbdgen, Keyman,
  XKB/KLC/keylayout) + `metadata/` (légendes dynamiques, pédagogie, IA, a11y — **non exportée**).
  → **Raffinement (ChatGPT)** : séparer strictement 4 niveaux — (1) famille logique de touches,
  (2) projection sémantique LDML, (3) *lowering hints* par cible (Windows/macOS/XKB/Keyman),
  (4) exports non-layout (Karabiner, AHK). Rend explicite ce qui est sémantique vs présentation
  vs simple commodité d'export.

- **D10 — Mapping physique (firmware) séparé du mapping linguistique.** 🟢🔴 *(arbitrage de périmètre)*
  Le mapping firmware (QMK/ZMK/TMK : matrice physique → HID) est **orthogonal** au mapping
  layout (HID → Unicode).
  → **Divergence des moteurs** : Perplexity = prudent (namespace d'extension `physicalMapping`
  distinct, risque de confusion d'audience) ; Gemini = ambitieux (« source de vérité unifiée »
  soft+hard). **Synthèse retenue** : inclure le firmware **mais dans un namespace d'extension
  clairement séparé**, jamais au même niveau que la couche texte. Décision de périmètre projet à
  confirmer (recoupe le prompt 6 firmware).

- **D11 — Frame keys hors scope LDML → extension OKLM.** 🟢
  LDML 3.0 ne couvre que les touches émettrices de caractères (non-frame) ; Fn, Numpad, cursor,
  IME-swap sont hors scope. OKLM les couvre via extension (recoupe **D1** : touches hors page
  0x07 — Fn, média/consumer page 0x0C).

- **D12 — Publier explicitement les « frontières de redondance ».** 🟢 (reco ChatGPT)
  Documenter ce qu'OKLM **n'est pas** : pas un remplaçant des transforms/reorders/markers LDML ;
  pas une re-spécification des formats OS natifs. OKLM **est** une couche d'authoring + métadonnées
  qui compile vers LDML et d'autres backends ; sa valeur = maintenabilité, métadonnées riches,
  orchestration multi-cibles — pas une redéfinition de la sémantique de frappe.

### Statut LDML 3.0 à connaître
- « Keyboard 3.0 » introduit en **CLDR v45** (réécriture complète, **incompatible CLDR v43-** ;
  ancien `ldmlKeyboard.dtd` gelé). Au **7 juin 2026, ligne stable = CLDR 48.2 / UTS #35 Part 7
  v48.2** (ChatGPT) — le `conformsTo="techpreview"` correspond aux phases de dev, pas à la version
  stable. → **OKLM cible UTS #35 Part 7 v48.x** et suit l'évolution CLDR.
- **Élément/modèle racine = `keyboard3`** (tranché : ChatGPT + Gemini concordants ; Perplexity
  disait `<keyboard>`, imprécis/legacy). L'ancien élément `<keyboard>` est la ligne gelée.

### Résolutions issues du recoupement (triangulation 3 moteurs)
- ✅ **Élément racine** = `keyboard3` (ChatGPT + Gemini concordants ; Perplexity imprécis).
- ✅ **Version cible** = **UTS #35 Part 7 v48.2** (CLDR 48.2 stable au 2026-06-07) ; « techpreview »
  = phases de dev, dépassé.
- 🔴 **D10** (inclure le firmware dans OKLM via namespace séparé) = reste un arbitrage de
  périmètre projet (les 3 moteurs valident l'idée, divergent sur l'ampleur).

### Artefacts d'archive
- Le `.md` Perplexity du prompt 9 a un artefact d'export : certaines balises XML ont perdu leur
  `<l` (`<layers>` → `ayers>`, `<layer>` → `ayer>`, `<locales>` → `ocales>`). Cosmétique,
  contenu intact.
- Le miroir Gemini est une conversion auto markitdown (tableaux éclatés) — lecture seule.

---

## Prompt 11 — Normes de jure (ISO/IEC 9995 & nationales)

> Sources : Perplexity + ChatGPT + Gemini, 2026-06-07. Statut : 🟢 **confirmé par triangulation
> (3 moteurs très convergents)**. Apport central : **le vocabulaire normatif ISO/IEC 9995 à
> adopter verbatim**, et la résolution de la notation de **D1** (→ numéro de touche ISO 9995-1
> canonique, voir le bloc D1 mis à jour).

### Décisions retenues

- **D2 confirmé/enrichi — modèle à 2 axes `(group, level)` verbatim.** 🟢
  Niveaux 1-4 (L2 = Shift, L3 = AltGr/Level-3-Select, L4 = Shift+AltGr ; L4 réservé aux
  caractères rares) **+ Groupes** (axe supérieur, multi-script ; Group 1 défaut ; latch ou
  lock). Abandonner « layers / shift-states / fn ».

- **D5 enrichi — géométrie en alias, position en numéro ISO.** 🟢
  La **géométrie** (forme physique) est déclarée par alias — ANSI/ISO/JIS/ABNT, ou key
  arrangement A/E/J/B (ISO 9995-2:2026), ou 101/102/104/106 (W3C) — mais la **position
  canonique reste le numéro ISO 9995-1** (cf. D1). OKLM peut accepter plusieurs notations d'alias.

- **D13 — Déclaration de conformance.** 🟢
  Permettre une **liste explicite** de références normatives (un claim « ISO 9995 compliant »
  global est invalide). Ex. : « Conforms to ISO/IEC 9995-1:2026 + 9995-2:2026 (Clause 7.2,
  48 touches) ; dead keys per 9995-11:2026 ; légendes per 9995-7:2009/Amd.1:2012 ; national :
  AFNOR NF Z71-300:2019 (AZERTY) ». Conformance **partielle** permise (60 % → sections
  absentes). Alignement LDML = déclaration **séparée** (pas une conformance ISO).

- **D14 — Réutiliser la terminologie ISO 9995 (ne pas réinventer).** 🟢
  `level` (≠ « shift state »), `group` (≠ « mode/layer »), `key number` / `key reference grid`
  (≠ « scan code » / « key code »), `section` / `zone`, `dead key`, `qualifier` /
  `level-select` / `group-select key`, `graphic key` / `function key`. Recoupe D7/D12.

- **Légendes (renforce D8)** : référencer **ISO/IEC 9995-7** (symboles de fonctions, plusieurs
  encodés Unicode : Alt `U+2387`, Ctrl `U+2388`, Compose `U+2384`…), **9995-10** (caractères
  ambigus), et les **3 schémas de placement** de 9995-1:2026 (columnar / group-1-priorized /
  level-4-including).

### À connaître
- **ISO/IEC 9995 révisé 2025-2026** : parts 1, 2, 3, 9, 11 = **2026** ; parts 4, 10 = 2025 ;
  parts 5, 7, 8 sur éditions antérieures ; part 6 retirée. → citer les éditions 2026.
- **9995-3:2026** = nouvelle « Latin International » (remplace l'ancien « common secondary group »).
- **Annexe A de 9995-2 (placement des lettres latines) = informative** → Dvorak / BÉPO /
  Turkish-F peuvent réclamer la conformité 9995-2.
- **AFNOR NF Z71-300:2019** (AZERTY optimisé + BÉPO, forme ISO) implémenté nativement
  Windows 11 24H2 — pertinent pour le positionnement AZERTY Global.
- **DIN 2137-01:2023-08** (E1/E2) introduit un « Extra Selector » ≈ Level 5 / compose — précédent utile.

### Divergences mineures (non bloquantes)
- **GOST** : Perplexity & Gemini « GOST 6431-90 » (JCUKEN) ; ChatGPT « GOST 14289-88 »
  (claviers informatiques) + 29124-91 (exigences générales). Les deux existent ; à verrouiller
  si besoin Russie.
- **Notation d'alias géométrie** : pas de consensus (A/E/J/B vs 101/102/104/106 vs
  ANSI/ISO/JIS/ABNT) — OKLM en supporte plusieurs ; canonique = numéro ISO.

### Artefacts d'archive
- Comme le prompt 9 : balises `<layer>` apparaissent `ayer>` dans le Perplexity (export). Miroir
  Gemini = conversion auto markitdown. Cosmétique.

---

## Prompt 10 — IME & saisie des scripts complexes

> Sources : Perplexity + ChatGPT + Gemini, 2026-06-07. Statut : 🟢 **confirmé par triangulation
> (3 moteurs)**, avec vérification source primaire ciblée sur **UTS #35 Part 7 v48.2** et
> **UAX #15**. Apport central : fermeture de la frontière ouverte par D7/D11.
> **OKLM représente le layout et le déterministe LDML ; OKLM référence les IME complets ; OKLM
> ne modélise pas le rendu.**

### Décisions retenues

- **D15 — Frontière tripartite obligatoire : Layout / Transforms-Reorders / IME complet.** 🟢
  OKLM doit publier une règle de classement simple :
  1. **LAYOUT** = mapping fixe `key + group/level -> caractère, chaîne courte, touche morte ou
     état de touche morte`, sans analyse linguistique.
  2. **TRANSFORMS / REORDERS** = réécritures locales, déterministes, sans dictionnaire :
     dead keys, translittération déterministe, reorder Indic/Thai, markers, normalisation.
  3. **FULL IME** = pré-édition, conversion, candidats, dictionnaires, ranking, historique
     utilisateur, reconversion, prédiction.
  Citations rapports : Perplexity : « Deterministic, dictionary-free » ; ChatGPT :
  « deterministic, local, dictionary-free » ; Gemini : « dictionary, or probabilistic candidate
  ranking ». Vérification source primaire : UTS #35 définit le clavier comme un format
  d'échange qui produit du texte brut et définit séparément l'IME comme composant avec logique
  contextuelle et UI de candidats.
  → **Affinage D7** : OKLM ne réinvente pas les transforms/reorders/markers LDML.
  → **Affinage D11** : les touches/modes IME restent metadata ou extension, pas cœur LDML.

- **D16 — Les IME complets sont référencés, jamais embarqués.** 🟢
  OKLM doit permettre une metadata déclarative de dépendance IME, mais ne doit pas inclure de
  dictionnaires, tables de candidats, modèles statistiques, règles de ranking, UI de candidats ni
  protocole runtime TSF/IMK/IBus/Fcitx/Android. Le bloc recommandé doit couvrir au minimum :
  `type` sémantique (`phonetic-chinese`, `shape-chinese`, `kana-kanji`, `phonetic-indic`...),
  `platformBindings` (TSF/text service, macOS input source ou bundle, IBus/Fcitx engine,
  Android package/service), `fallback`, et éventuel `transformSet` exécuté avant la délégation.
  Citations rapports : Perplexity : « The layout file is not an IME descriptor » ; ChatGPT :
  « provide declarative references » ; Gemini : « avoid embedding dictionary files ».
  → **Tension `SPEC.md`** : aucun champ `imeRequirements` / `inputMethods` / `platformBindings`
  n'existe encore ; les `commands` actuels ne doivent pas devenir un fourre-tout IME.

- **D17 — Hangul est algorithmique : natif transform/FSM, pas IME complet.** 🟢
  La composition Hangul ordinaire (jamo -> syllabe précomposée) est déterministe et sans
  dictionnaire ; elle doit donc être représentable dans OKLM comme transform set, marker/FSM ou
  transform algorithmique LDML-compatible. **Hanja conversion** et toute sélection lexicale
  rebasculent en IME complet référencé.
  Citations rapports : Perplexity : « no dictionary is required » ; ChatGPT : « not
  dictionary-driven » ; Gemini : « mathematically deterministic ».
  → **Point à confirmer** : vérifier l'encodage LDML le plus maintenable pour Hangul complet
  (tables explicites, markers, ou référence d'algorithme standard) avant migration `SPEC.md`.

- **D18 — CJK et kana-kanji : conversion candidate/dictionnaire hors cœur OKLM.** 🟢
  Les méthodes chinoises Pinyin, Zhuyin/Bopomofo, Wubi, Cangjie et Stroke, ainsi que le
  kana->kanji japonais, exigent lookup lexical, homophonie, segmentation, ranking ou candidat UI :
  OKLM les **référence** seulement. En revanche, `romaji -> kana` et le direct kana sont
  déterministes : ils peuvent vivre dans les transforms ou le layout.
  Citations rapports : Perplexity : « cannot be reduced to a transform-only model » ; ChatGPT :
  « candidate lookup and conversion are central » ; Gemini : « require dictionary-backed,
  stateful IMEs ».

- **D19 — Indic/Brahmic et Asie du Sud-Est : script grammar déterministe dans LDML.** 🟢
  InScript, virama/halant, matras, pré-voyelles, reorder Brahmic, Thai WTT, Khmer Coeng,
  Myanmar/Lao reorder/stacking appartiennent au bucket transforms/reorders/markers quand ils
  sont déterministes et sans candidats. Les variantes phonétiques qui ajoutent suggestions,
  ranking ou dictionnaire deviennent des IME légers référencés.
  Citations rapports : Perplexity : « Input sequence validation ... without requiring a
  dictionary » ; ChatGPT : « deterministic script-order handling » ; Gemini : « syntactic
  sequence validation ».
  → **Point à confirmer** : inventaire exact des règles Khmer/Myanmar/Lao à traiter par script,
  car les rapports ne fournissent pas un jeu de règles complet.

- **D20 — Arabic/Hebrew : input logique natif ; shaping, bidi et glyphes hors OKLM.** 🟢
  OKLM doit modéliser le mapping vers les lettres et marques combinantes (harakat, niqqud,
  etc.) en ordre logique. Il ne doit pas modéliser les formes contextuelles arabes, ligatures,
  substitutions OpenType, miroir bidi ou ordre visuel : ce sont des responsabilités du moteur de
  rendu et de l'algorithme bidi.
  Citations rapports : Perplexity : « rendering/font concern » ; ChatGPT : « shaping and bidi
  are rendering » ; Gemini : « exclusive responsibility of the downstream Rendering and Shaping
  Engine ».

- **D21 — La normalisation devient un contrat explicite du cœur transforms.** 🟢🔴
  Les transforms/reorders/markers OKLM doivent déclarer leur contrat de normalisation et de
  backspace : correspondance en NFD, sortie normalement en NFC ou forme demandée par la
  plateforme, markers non émis en texte final, et comportements de retour arrière pour séquences
  composées. UAX #15 est la référence Unicode ; LDML Part 7 décrit où la normalisation intervient.
  Citations rapports : Perplexity : « NFD matching -> NFC output » ; ChatGPT : « normalisation is
  an engine requirement » ; Gemini : « strict Unicode Normalization ».
  → **Tension `SPEC.md` bloquante** : `SPEC.md` ne contient pas encore `normalization`,
  `transforms`, `reorders`, `markers` ni `backspaceTransforms`.

- **D22 — Prédiction, autocorrect, handwriting, voice : hors cœur ; translittération scindée.** 🟢
  La prédiction, l'autocorrect, l'écriture manuscrite et la voix sont des couches adjacentes,
  non-layout. La translittération est à diviser : table déterministe (`romaji -> kana`,
  Latin -> script Indic sans candidat) = transforms ; translittération avec suggestions,
  dictionnaire, ranking ou apprentissage = IME référencé.
  Citations rapports : Perplexity : « outside the core » ; ChatGPT : « separate optional
  layers » ; Gemini : « strictly excluded from the structural layout format ».

### Résolutions issues du recoupement (triangulation 3 moteurs)

- ✅ **Frontière principale stable** : les 3 moteurs convergent sur le critère
  *déterministe/local/sans dictionnaire* pour LDML, et *dictionnaire/candidats/ranking* pour IME.
- ✅ **Source primaire LDML** : la cible reste **UTS #35 Part 7 v48.2**, élément `keyboard3`,
  avec `transforms`, `reorder`, markers, normalisation, `<special>` extensible, et exclusion des
  frame keys (Fn, numpad, IME swap, cursor).
- ✅ **UAX #15** : la normalisation est un contrat d'implémentation, pas une table ad hoc de
  layout author.
- ✅ **IME runtime hors scope** : TSF, IMK, IBus/Fcitx, Android `InputMethodService` sont des
  frameworks d'exécution à référencer, pas à sérialiser dans OKLM.
- ⚠️ **Apple iOS** : ChatGPT nuance correctement : IMK = macOS ; iOS passe par custom keyboard /
  text-input APIs, pas IMK public. À garder prudent.
- ⚠️ **Gemini** : le rapport affirme trop largement que la translittération Latin -> script
  étranger « rely on vast phonetic dictionaries ». Recoupement Perplexity + ChatGPT :
  translittération déterministe = transforms ; suggestions/ranking = IME.

### Tensions avec `SPEC.md`

- `SPEC.md` expose `layers`, `deadKeys` et `outputs`, mais pas encore les concepts LDML
  nécessaires : `transforms`, `reorders`, `markers`, `normalization`, `backspaceTransforms`,
  imports de transform sets.
- `SPEC.md` ne prévoit pas de metadata de dépendance IME (`imeRequirements`, `platformBindings`,
  `fallback`, `transformSetBeforeIme`).
- `SPEC.md` parle de `commands` et d'AI assistant metadata ; il faut empêcher la confusion entre
  commandes companion-app et IME runtime.
- Le champ `layers` reste en terminologie familière (`base/shift/altgr/...`) alors que D2/D14
  demandent l'alignement ISO `(group, level)`.

### Points à confirmer avant migration `SPEC.md`

- Forme JSON exacte du bloc IME : nommage, cardinalités, catégories contrôlées, identifiants
  plateforme, relation éventuelle aux extensions BCP 47 `k0` / `i0`.
- Encodage LDML maintenable de Hangul : transform set complet, markers, ou primitive déclarative
  d'algorithme Unicode.
- Inventaire par script des règles Khmer/Myanmar/Lao réellement nécessaires au v0.1.
- Politique `conformsTo` / `tr35Version` : UTS #35 Part 7 est en v48.2, mais les exemples LDML
  Keyboard 3.0 utilisent encore des valeurs de conformité historiques comme `45`.
- Namespace `<special>` pour les metadata OKLM exportées vers LDML et comportement attendu des
  processeurs qui les ignorent.

### Artefacts d'archive

- Source Gemini PDF localisée sous le nom `Prompt 10 -  Gemini.pdf` (double espace après le tiret) ;
  miroir créé en `Prompt 10 - Gemini.md`, puis archivé sous le nom normalisé.
- Le miroir Gemini issu de `markitdown` casse plusieurs tableaux et perd des variables dans la
  formule Hangul ; contenu exploitable, mais à ne pas citer comme typographie de référence.
- Le rapport ChatGPT conserve des artefacts de citation internes (`îˆ€cite...`) ; brut conservé.
- Le rapport Perplexity contient quelques artefacts d'export déjà observés ailleurs (`<layers>` ->
  `ayers>`, `<candidates>` -> `andidates>`), cosmétiques.

---

## Prompt 16 — Géométrie physique des claviers

> Sources : Perplexity + ChatGPT + Gemini, 2026-06-07. Statut : 🟢 **confirmé par triangulation
> (3 moteurs)**, avec vérification source primaire ciblée sur **KLE/kle-serial**, **QMK
> `info.json` + schema**, **VIA/Vial**, **W3C UI Events `code`** et **XKB geometry**. Apport
> central : OKLM doit avoir une couche géométrie autonome, explicite, exportable, séparée à la
> fois du mapping texte et de la matrice firmware.

### Décisions retenues

- **D23 — Géométrie canonique stateless en coordonnées absolues.** 🟢
  La couche géométrie OKLM doit être une liste explicite d'éléments physiques, sans curseur de
  ligne implicite à la KLE : `x`, `y`, `w`, `h` en unités clavier `u`, origine top-left, valeurs
  absolues, avec ordre de sérialisation non significatif. Les rangées (`row`, `column`) peuvent
  rester des alias humains ou ISO, mais ne doivent pas suffire à dessiner un clavier.
  Citations rapports : ChatGPT : « stateless and absolute » ; Perplexity : « every key
  dictionary is stateless » ; Gemini : « strictly stateless, explicit coordinate system ».
  → **Tension `SPEC.md`** : le modèle actuel expose surtout `row`, `column`, `width` et un alias
  global `geometry`, pas une géométrie dessinable complète.

- **D24 — Identité canonique ISO, références croisées machine en metadata.** 🟢🔴
  D1/D5 sont maintenues : l'identifiant primaire d'une touche reste le **numéro ISO/IEC 9995-1**
  quand il existe, avec références croisées structurées vers XKB (`AD01`...), UI Events
  (`KeyQ`, `IntlBackslash`, `NumpadComma`...), USB HID usage et alias QMK/VIA. Les touches hors
  grille ou physiquement présentes mais non visibles par l'OS utilisent un namespace d'extension
  stable (`vendor:...`, `board:...`, `frame:...`), jamais un libellé imprimé.
  Citations rapports : Perplexity : « ISO 9995-1 grid IDs as stable key identifiers » ; ChatGPT :
  « attach structured cross-references » ; Gemini diverge : « adopt W3C KeyboardEvent.code
  strings as primary ». **Résolution** : `code` est excellent comme référence Web, mais il est
  incomplet pour les éléments firmware/boîtier et moins normatif qu'ISO pour OKLM.

- **D25 — Géométrie, matrice électrique, mapping texte et légendes restent séparés.** 🟢
  OKLM ne doit pas laisser la matrice QMK/VIA devenir l'identité physique ni mélanger caractère,
  switch et position. La matrice doit vivre dans un bloc séparé de type `electricalBindings` ou
  `firmwareBindings`, qui relie `physicalKeyId` à `(row, col)` QMK/VIA quand nécessaire. Les
  caractères restent dans la couche layout/LDML ; les légendes dans metadata d'affichage.
  Citations rapports : ChatGPT : « geometry, firmware matrix, legends and character mapping are
  separate axes » ; Perplexity : « matrix coordinates are not physical identity » ; Gemini :
  « separate `geometry`, `matrix`, and `logicalMapping` sections ».
  → **Affinage D10/D11** : le firmware est exportable, mais dans une extension latérale.

- **D26 — Rotation et formes : rectangles par défaut, formes riches optionnelles.** 🟢🔴
  Le cœur doit couvrir `rotation.angle` + pivot absolu (`rx`, `ry` ou équivalent), rectangles
  `w/h`, et formes composées ou polygonales facultatives pour ISO Enter, stepped keys, keycaps
  atypiques, châssis et CAD. Export : KLE peut recevoir deux rectangles (`x2/y2/w2/h2`) ; XKB/CAD
  peuvent recevoir des polygones/outlines ; QMK `info.json` actuel doit être traité comme
  rectangle + rotation, avec dégradation contrôlée pour les formes non rectangulaires.
  Citations rapports : ChatGPT : « optional composite/polygonal shapes » ; Gemini : « vector
  polygon path methodology from XKB » ; Perplexity mentionne `ks` côté QMK. **Résolution source
  primaire** : la documentation et le schema QMK vérifiés listent `x/y/w/h`, `matrix`, `label`,
  `r/rx/ry`, `encoder`, mais pas de champ polygonal `ks` ; ne pas l'utiliser sans revérification.

- **D27 — Variantes physiques first-class.** 🟢
  Les options ANSI/ISO/JIS/ABNT, split backspace, split spacebar, stepped Caps Lock ou bottom rows
  doivent être modélisées comme groupes de variantes mutuellement exclusives, avec éléments
  physiques activables/désactivables et région couverte. Exports : VIA/Vial en labels/options,
  QMK en `LAYOUT_*` multiples, KLE en vues ou fichiers séparés, UI en sélecteurs de variantes.
  Citations rapports : Perplexity : « variants as first-class objects » ; ChatGPT : « mutually
  exclusive physical alternatives » ; Gemini : « LayoutVariant construct ».
  → **Tension `SPEC.md`** : l'alias `geometry: ansi-60` ne suffit pas pour décrire des variantes
  simultanément supportées par un même PCB.

- **D28 — Légendes, profils, homing et couleurs sont du rendu/fabrication, pas l'identité.** 🟢
  OKLM peut conserver ces informations pour visualisation, keycap sets, documentation ou exports
  KLE/VIA, mais elles ne doivent pas définir la touche physique ni la sortie Unicode. Les slots de
  légende KLE (jusqu'à 12), couleurs, tailles, `profile`, `nub`, `stepped` et `decal` restent des
  metadata.
  Citations rapports : ChatGPT : « legends are rendering metadata » ; Perplexity : « legend
  placement is not a key identifier » ; Gemini : « visual legends are annotations ».

- **D29 — Les éléments non-caractères et OS-invisibles appartiennent à la géométrie.** 🟢
  La géométrie OKLM doit placer les touches de fonction, navigation, pavé numérique, média,
  touches IME/langue, Fn, boutons firmware, encoders, LEDs/indicateurs et autres éléments visibles.
  Recommandation : `elementType` (`key`, `encoder`, `indicator`, `caseFeature`, `displayOnly`...)
  + `hostVisible`/`eventing` pour distinguer touche HID, consumer page, firmware-only et pur
  dessin. Les touches Fn et mode internes ne doivent pas disparaître parce qu'elles ne sortent pas
  de `KeyboardEvent.code`.
  Citations rapports : Perplexity : « physically-present-but-OS-invisible keys » ; ChatGPT :
  « Fn keys still need physical placement » ; Gemini : « every physical control deserves a
  physical element record ».
  → **Affinage D11** : les frame keys hors LDML sont bien couvertes par OKLM, côté géométrie.

- **D30 — XKB geometry, Ergogen/CAD et KLE sont des formats d'échange, pas le canon OKLM.** 🟢
  OKLM garde son canon en unités `u` lisibles à la main, avec une échelle optionnelle `u_mm` pour
  les exports millimétriques. XKB geometry est riche pour formes, sections, doodads et polygones,
  mais legacy et orienté rendu X11 ; KLE est très utile mais stateful en source ; QMK/VIA/Vial sont
  indispensables pour firmware/configurateurs mais centrés sur matrice et visualisation. OKLM doit
  importer/exporter ces formats sans hériter de leurs contraintes internes.
  Citations rapports : ChatGPT : « do not make KLE the canonical source » ; Perplexity : « KLE is
  de-facto but lossy/quirky » ; Gemini : « XKB geometry should inform, not dominate ».

### Résolutions issues du recoupement (triangulation 3 moteurs)

- ✅ **Convergence forte** : les 3 moteurs recommandent une géométrie absolue, explicite,
  maintenable, séparée du mapping texte et de la matrice firmware.
- ✅ **KLE** : excellent format d'interop hobbyist et visualisation, mais source compacte/stateful
  avec effets de rangée, propriétés persistantes, légendes surchargées et variantes non natives.
- ✅ **QMK** : `info.json` relie position visuelle et matrice ; utile pour firmware/export, pas assez
  riche pour devenir le canon géométrique.
- ✅ **VIA/Vial** : reprennent KLE et encodent la matrice/options dans les légendes ; OKLM doit
  exporter ce modèle, pas le reprendre tel quel.
- ✅ **XKB geometry** : bon précédent pour formes, sections et doodads ; format legacy à traiter en
  import/export.
- ⚠️ **Divergence Gemini** : `KeyboardEvent.code` proposé comme ID primaire. Résolu contre Gemini :
  OKLM conserve ISO comme canon, `code` comme référence croisée.
- ⚠️ **Divergence Perplexity** : champ QMK polygonal `ks`. Résolu par source primaire QMK : absent
  de la documentation et du schema actuels vérifiés.

### Tensions avec `SPEC.md`

- `SPEC.md` n'a pas encore de `geometry.keys[]` dessinable avec `x/y/w/h`, rotation, pivot,
  forme, variantes et éléments non-touches.
- `Key.id` et les exemples actuels doivent être alignés avec D1/D5/D24 : ISO canonique +
  références croisées, pas ID implicite de rangée interne ou libellé.
- `labels` et `outputs` cohabitent dans la définition de touche ; la migration devra isoler
  géométrie, légende visuelle et sortie texte.
- Aucune structure ne couvre encore les bindings firmware/matrice ni les éléments `encoder`,
  `indicator`, `Fn`, `caseFeature` ou `displayOnly`.
- Les variantes ANSI/ISO/JIS/ABNT et options PCB ne sont pas représentables autrement que par un
  alias global.

### Points à confirmer avant migration `SPEC.md`

- Nommage final des blocs : `geometry.elements`, `geometry.keys`, `variantGroups`,
  `references`, `electricalBindings`, `eventing` ou équivalents.
- Détails exacts des numéros ISO/IEC 9995-1:2026 pour touches ABNT/JIS/Korean mode derrière texte
  normatif payant ; conserver les mappings issus des prompts 1/11 jusqu'à validation.
- Politique de dégradation export pour QMK/VIA/Vial quand OKLM contient polygones, châssis,
  encoders hors matrice ou variantes imbriquées.
- Correspondance complète ISO ↔ XKB ↔ UI Events `code` ↔ HID pour pavé numérique, IME keys,
  touches média/consumer page et touches firmware-only.
- Niveau de détail CAD souhaité dans v0.1 : simple visualisation 2D ou export fabrication plus
  précis (switch cutout, stab, plate outline, keycap profile).

### Artefacts d'archive

- Le miroir Gemini issu de `markitdown` casse plusieurs tableaux ; contenu exploitable, mais le
  PDF original a été archivé à côté.
- Les rapports ChatGPT et Perplexity contiennent des artefacts de citation internes déjà observés
  (`cite...`, balises XML parfois mangées) ; les bruts ont été conservés fidèlement.
- La mention Perplexity de `ks` côté QMK est conservée dans le brut mais annotée ici comme non
  confirmée par les sources primaires vérifiées.

---

*Dernière mise à jour : 2026-06-07*
