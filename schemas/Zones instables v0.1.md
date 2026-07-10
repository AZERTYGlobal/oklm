# Zones instables — schéma OKLM v0.1

> Note de conception accompagnant `oklm-manifest.schema.json` et
> `oklm-conversion-report.schema.json` (draft 0.1, 2026-07-10).
>
> Le schéma v0.1 incorpore les décisions confirmées du journal
> [`research/Décisions de conception — deep research.md`](../research/Décisions%20de%20conception%20—%20deep%20research.md)
> (D1-D30, prompts 1, 9, 10, 11, 16 triangulés). Sur les zones couvertes par des
> prompts **non traités**, il reste volontairement silencieux ou minimal plutôt que
> d'inventer. Cette note liste ce qui pourra bouger, et pourquoi.

## Ce que le schéma v0.1 fige (décisions confirmées)

- **Identité de touche** : numéro ISO/IEC 9995-1 canonique (`D01`, `C00`…), `hid`
  obligatoire (page 0x07, hexadécimal), alias `xkb` et `code` W3C optionnels (D1, D24).
- **Modèle `(group, level)` ISO verbatim** : `levels` (1-8) par touche pour le
  groupe 1, `groups` optionnel pour les groupes 2+ ; sélecteurs nommés par fonction
  (`Level2Shift`, `Level3Shift`…), jamais par touche physique (D2, D3, D14).
- **Dead keys séparées du mapping**, isomorphes aux markers + transforms simples
  LDML Keyboard 3.0 : `\m{id}` + base → sortie (D4, D7). Vérifié contre UTS #35
  Part 7 v48.2 le 2026-07-10 (racine `keyboard3`, `conformsTo` = entier ≥ 45,
  markers `\m{id}`, transforms `simple`/`backspace`).
- **Géométrie en alias** (`iso-full`, `ansi-60`…), position canonique = numéro ISO (D5).
- **Architecture en couches** : cœur alignable LDML → `metadata` (enveloppe D8,
  strippée à l'export) → `extensions` namespacées (D9, D11).
- **Frame keys hors cœur** : namespace d'extension réservé `frame-keys` (D11, D29).
- **Déclaration de conformance** : liste explicite de références normatives avec
  portée ; l'alignement LDML se déclare à part, sur la cible d'export (D13).
- **Terminologie ISO 9995** : `level`, `group`, key number — plus de `layers` ni
  de `shift states` (D14) ; le champ `layers` est rejeté par le schéma.

## Zones instables (prompts non traités)

### 1. Prompt 12 — Conception du format + conformance (**seule vraie dépendance structurelle**)

Le prompt 12 est le seul dont le résultat peut modifier la **structure** du schéma,
pas seulement l'enrichir. Pourront bouger :

- les conventions de nommage et l'ordre canonique des champs ;
- la frontière exacte notation compacte / notation longue des sorties ;
- la forme du bloc `conformance` (aujourd'hui volontairement minimal :
  `reference` + `scope` + `notes`) et une éventuelle politique de versionnage
  du schéma lui-même (`schemaVersion` est un `const "0.1"` en attendant) ;
- la politique d'enregistrement des namespaces d'`extensions`.

### 2. Prompt 6 — Firmware (fermeture de D10 🔴)

D10 (mapping physique firmware dans un namespace d'extension séparé) reste un
**arbitrage de périmètre non fermé**. Le schéma réserve le namespace
`extensions.firmware` sans en spécifier le contenu. Rien dans le cœur ne dépend
de cette décision ; la fermeture de D10 via le prompt 6 remplira (ou supprimera)
ce namespace sans casser les manifestes existants.

### 3. Prompts 2-5, 7-8, 15 — Exporteurs (OS desktop, mobile, embarqué, web)

- `exports[].options` est un objet **libre** : chaque exporteur recevra son propre
  sous-schéma d'options une fois son prompt traité.
- Le schéma de rapport de conversion ne couvre que les deux directions
  obligatoires (`oklm-to-ldml`, `ldml-to-oklm`) ; les rapports des autres cibles
  d'export seront ajoutés avec les exporteurs.
- La liste des valeurs de `target` est ouverte (pattern, pas d'enum) pour la même
  raison.

### 4. Acquis des prompts 10 et 16 volontairement non schématisés en v0.1

Ces prompts sont déjà triangulés, mais leurs « points à confirmer avant migration »
ne sont pas levés :

- **Bloc IME** (D15-D18) : aucune propriété `imeRequirements`/`platformBindings`
  en v0.1 — la forme JSON exacte (nommage, cardinalités, catégories, relation
  BCP 47 `k0`/`i0`) est explicitement à confirmer dans le journal.
- **Transforms généraux, reorders, normalisation** (D19-D21) : le v0.1 ne couvre
  que les dead keys (transforms simples). Le contrat de normalisation D21 est
  🔴 (tension SPEC bloquante consignée) : non tranché ici, conformément au journal.
- **Géométrie dessinable** (D23-D30) : pas de `x/y/w/h`, rotation, variantes ni
  `elementType` dans le cœur — le nommage des blocs (`geometry.elements`,
  `variantGroups`, `electricalBindings`…) est listé « à confirmer » ; namespace
  `extensions.geometry` réservé en attendant.

## Migrations `SPEC.md` — appliquées le 2026-07-10

Le `research/README.md` listait des migrations « en attente, avec validation ».
Le schéma v0.1 les implémentait déjà côté schéma ; les 6 migrations ci-dessous
ont été **appliquées à `SPEC.md` le 2026-07-10** (avec synchronisation de
`README.md` et `CONVERSIONS.md` sur la terminologie group/level et le renvoi
au schéma de rapport de conversion) :

1. Ids d'exemple `"C01"` → numéros ISO 9995-1 réels + `hid` obligatoire +
   `xkb`/`code` optionnels sur l'objet Key (D1, D24).
2. Terminologie `layers: base/shift/altgr/shiftAltgr/caps` → modèle ISO
   `(group, level)` + sélecteurs fonctionnels (D2, D3, D14).
3. `deadKeys`/`compositions` reformulés comme isomorphes aux markers/transforms
   LDML, avec mention de la politique d'annulation par plate-forme (D4, D7).
4. Mention de la convention touches hors page HID 0x07 → extension `frame-keys`
   (D11).
5. Sections Key : retirer `row`/`column`/`width` du cœur (géométrie dessinable
   différée, D23) et renvoyer l'exemple minimal vers
   `examples/azerty-global-minimal.oklm.json`.
6. Ajouter la section « Conformance declaration » (D13) et le renvoi au schéma
   de rapport de conversion désormais existant.

`SPEC.md` précise désormais explicitement : en cas de divergence prose/schéma,
le schéma fait foi pour le draft 0.1.

## État de validation (2026-07-10)

Validation exécutée avec `jsonschema` 4.26.0 (Python, Draft 2020-12) :
méta-validation des 2 schémas, exemple `azerty-global-minimal.oklm.json` valide,
unicité des ids et résolution des références `deadKey` vérifiées hors schéma,
5 cas invalides de manifeste et 3 cas invalides de rapport correctement rejetés,
2 instances de rapport (export et import) valides. Script rejouable :
[`validators/validate_v0_1.py`](../validators/validate_v0_1.py) (15/15 tests OK
au 2026-07-10).

---

*Dernière mise à jour : 2026-07-10*
