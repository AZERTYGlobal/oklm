Survey and Analysis of Keyboard
Physical Geometry Data Models for
Open Layout Schema Design
Introduction and Architectural Context
The abstraction of human-computer interface devices inherently demands a strict, structural
demarcation between the physical architecture of the hardware and the logical behavior it
executes. In the context of keyboard design and systems engineering, the development of an
open layout schema necessitates decoupling the physical geometry layer from the character
mapping layer. The physical geometry domain encompasses the absolute and relative
coordinates of key positions, the structural dimensions of keycaps, the rotational orientations of
ergonomic clusters, the underlying electrical switch matrix, and the permutations of physical
form factors. Conversely, the logical layer—which falls outside the primary scope of this
geometry analysis—dictates the alphanumeric values, modifiers, or control codes transmitted to
the operating system upon actuation.
Historically, operating systems and firmware have frequently conflated these layers, treating
hardware scan codes as implicit indicators of localized character maps. However, modern
systems architecture requires a geometry model that treats the keyboard as a pure physical
canvas. A unified, open layout model must establish a standardized methodology for defining
physical keys in a manner that is both hand-maintainable for engineers and mathematically
precise for automated tooling. This model must possess the elasticity to account for a vast array
of geometric configurations. These range from highly standardized staggered layouts (such as
the ANSI, ISO, and JIS specifications) to highly specialized ortholinear, column-staggered, and
split-angle ergonomic designs utilized by hardware enthusiasts.
To engineer this foundational schema, it is imperative to exhaustively survey and deconstruct
the existing de-facto hobbyist formats, firmware configuration protocols, and international
engineering standards that currently attempt to map the physical realm. This analysis critically
evaluates the Keyboard Layout Editor (KLE) JSON format, the Quantum Mechanical Keyboard
(QMK) info.json structure, VIA and Vial dynamic interface definitions, the ISO/IEC 9995-1
reference grid, and the X Keyboard Extension (XKB) geometry component. Furthermore, this
report addresses the critical systemic challenge of identifying identical physical keys across
disparate, incompatible systems. By mapping physical locations to hardware-agnostic
identifiers—specifically the W3C UI Events code values and USB Human Interface Device (HID)
usage IDs—the model can achieve universal interoperability. By evaluating the coordinate
models, matrix encoding strategies, variant handling capabilities, and inherent limitations of
these disparate formats, this report formulates a comprehensive recommendation for the
architectural foundations of a new, universally adaptable open keyboard layout model.
Exhaustive Survey of Existing Geometry Description

Formats
Keyboard Layout Editor (KLE) JSON: The De-Facto Hobbyist Standard
The Keyboard Layout Editor (KLE), accessible via the web application
keyboard-layout-editor.com, has established itself over the past decade as the foundational
visual design tool and the primary interchange format for custom keyboard physical
geometries.1 Its output is a highly compact, specialized serialization format utilizing JSON. More
accurately, it is typically serialized as JSON5, given that the raw data output frequently lacks
quotation marks around property names to maximize visual compactness.1 KLE's primary
architectural objective is the visual rendering of keycaps on a two-dimensional Cartesian plane
for rapid prototyping.
The Stateful Coordinate Model and Parsing Challenges
The most defining, and systemically the most problematic, characteristic of the KLE serialization
format is its heavily stateful coordinate model. A KLE layout is structurally defined as an array of
rows, where each row is an array containing either strings (representing key legends) or objects
(representing property modifiers).1 Rather than explicitly declaring absolute and
coordinates for every key entity, KLE utilizes an internal rendering state machine.5
When the parser encounters a string, it renders a key using the currently held state variables for
width, height, color, and position. After the key is drawn, the state machine implicitly increments
the internal pointer by the calculated width of the key.1 When a row array terminates, the
parser resets the pointer to zero and increments the pointer by one standard key unit
(1u).1 To introduce horizontal or vertical gaps—such as the interstitial space separating a main
alphanumeric cluster from a navigation cluster or numeric keypad—KLE accepts an object
containing coordinate modifiers immediately preceding the key string.1 For example, the object
{x: 0.25, y: 0.5} instructs the parser to shift the rendering pointer relative to its current state
before drawing the subsequent key.
While this stateful, relative architecture ensures a remarkably concise file size that is relatively
easy for humans to type manually, it creates immense friction for programmatic integration. Any
consuming application, CAD generator, or firmware compiler must implement a fully functional
state machine parser simply to determine the absolute physical bounding box of a single key.4
Furthermore, because the format evolved iteratively without strict initial schema validation,
community parsers (such as kle-serial) are frequently required to handle deprecated edge cases
and lenient syntax anomalies.4
Key Sizes, Rotational Mathematics, and Stepped Geometry
KLE defines standard key dimensions using width (w) and height (h) properties, which
universally default to 1u (typically standardized in physical manufacturing as a 19.05 mm pitch).5
However, the representation of non-rectangular or stepped keys—such as the ISO Enter key or

an off-center stepped Caps Lock—exposes significant geometric quirks within the format.
To render a stepped key, KLE utilizes secondary dimension properties: x2, y2, w2, and h2.7
These parameters define a secondary rectangle overlaid upon the primary key bounding box.
For a complex shape like an ISO Enter key, this results in an overlapping combination of two
distinct rectangles to simulate the "L-shape", rather than utilizing a geometrically pure vector
polygon definition. This approach forces downstream CAD tooling, such as plate generators like
swillkb, to algorithmically merge these overlapping rectangles into a single continuous cut-out
path, introducing potential errors in physical switch plate tolerances.9
Rotational geometry presents an even more complex challenge in KLE. Rotation is achieved via
the r, rx, and ry properties.7 The rx and ry variables establish the absolute coordinates of the
transform origin, while r dictates the rotational angle in degrees.7 Once a rotation parameter is
parsed, it alters the orientation of the rendering pointer's Cartesian plane. Consequently, all
subsequent keys in that array, and all subsequent rows, are drawn relative to this newly rotated
axis until the rotation is explicitly reset to zero. This behavior severely complicates the
algorithmic conversion of KLE data into pure, absolute top-down coordinates, particularly for
heavily splayed ergonomic split keyboards where columns branch off at differing vectors.
Legend Placement and Formatting Limitations
KLE visualizes keycap legends by mapping an array of strings to specific physical quadrants on
the keycap surface. A single key definition can accept an array of up to 12 text labels.4 These
indices map sequentially to specific spatial alignments: top-left (0), top-center (1), top-right (2),
middle-left (3), middle-center (4), middle-right (5), bottom-left (6), bottom-center (7), bottom-right
(8), front-left (9), front-center (10), and front-right (11).2 Font sizes and colors can be individually
dictated for each of these 12 positions, allowing for highly complex visual representations of
sub-legends.1
Despite its ubiquity in the hobbyist space, KLE presents fundamental limitations for a rigorous
systems schema. It is inherently stateless in its representation of the electrical matrix; it purely
describes visual geometry. It has no mechanism for natively defining variant physical layouts
(such as an optional split spacebar) without simply drawing the keys overlapping one another in
the visual editor.
QMK info.json: Firmware-Level Layout Representation
The Quantum Mechanical Keyboard (QMK) firmware architecture initially relied heavily on
deeply nested C preprocessor macros to translate a linear array of electrical switch states into a
two-dimensional physical layout, and subsequently into a logical keymap. With the recent
advent of the Data-Driven Configuration paradigm, QMK shifted toward maintaining a strict,
schema-validated JSON file (info.json) to describe keyboard hardware metadata, establishing a
far more rigid standard for physical layout geometries.5
The Stateless, Absolute Coordinate System
In direct and deliberate contrast to KLE's state machine, the QMK info.json format utilizes a
completely stateless representation.5 Under the layouts dictionary, specific layout macros (e.g.,

LAYOUT_ansi, LAYOUT_iso) encapsulate an array named layout.5 Each element within this
array is a distinct, self-contained JSON object representing a single key.5
Every key explicitly declares its absolute x and y position in Key Units (u), relative to the top-left
corner of the physical keyboard bounding box.5 Width (w) and height (h) are also explicitly
defined, defaulting to 1u if omitted.5 By entirely discarding the relative state machine of KLE,
QMK's format allows parsers, such as the QMK Configurator web interface or localized
compilation scripts, to read key definitions in any arbitrary order.12 This vastly simplifies the
rendering logic, layout modification, and automated verification against the JSON schema
constraints.5
To resolve KLE's overlapping rectangle problem for complex shapes, the QMK schema
simplifies the representation. The ISO Enter key, for instance, is standardized in QMK as
possessing a 1.25u width and a 2u height (1.25u×2uh).5 Renderers are expected to internally
recognize this specific dimensional signature and draw the distinct "L-shape" automatically,
circumventing the need for raw polygon data or secondary coordinate offsets.5
Encoding the Electrical Matrix
The most critical systems-level distinction of the QMK info.json geometry representation is its
explicit, mandatory coupling of physical space to the underlying electrical switch matrix.5 Each
key object within the layout array must contain a matrix property, defined as an array of two
integers: [row, column].5 This object directly bridges the physical geometric location of a keycap
to the electrical routing on the printed circuit board (PCB).12
When engineering a PCB with missing switches, non-standard routing, or physical gaps (such
as the spaces between function key clusters), the legacy C macro equivalents historically used
placeholder values like KC_NO to denote void matrix intersections, ensuring the memory array
aligned properly.12 In the JSON schema, keys that do not physically exist are simply omitted
from the array entirely.12 The overall electrical row and column dimensions (MATRIX_ROWS
and MATRIX_COLS) remain fixed in the configuration headers, but the info.json layout array
only describes physically extant switches.12 Thus, the QMK geometry layer acts as a direct,
explicit translator between a strictly rectangular electrical grid and a highly irregular, physically
staggered surface.
VIA and Vial Definitions: Dynamic Layout and Variant Handling
VIA and its open-source fork, Vial, operate as dynamic configuration interfaces. They allow
end-users to alter keymaps, lighting, and macros in real-time via USB protocols without the
need to recompile or reflash the device firmware.14 To achieve this dynamic mapping, the host
software requires an exhaustive description of the keyboard's physical geometry, the routing
matrix, and, crucially, any optional layout permutations the PCB supports (such as splitting a
backspace key, or toggling between an ANSI and an ISO Enter form factor).1
KLE JSON Encapsulation and Data Overloading
Rather than inventing an entirely new geometry schema from scratch, or solely utilizing the

QMK info.json (which VIA predates in its widespread adoption), VIA and Vial keyboard
definitions cleverly reuse the raw KLE JSON format.1 This KLE array is embedded directly into
the VIA/Vial configuration files under the keymap property.1 Because the KLE format purely
defines visual geometry and lacks native matrix encoding, VIA and Vial establish a standard that
overloads the 12-position legend string array to encode crucial hardware metadata directly into
the key descriptions.1
To encode the switch matrix, the top-left legend (index 0) of every key in the embedded KLE
array is populated with its electrical coordinates in a row,col string format.13 When the host
software parses the geometry, it strips this coordinate string from the visual label, uses it to
dynamically build the matrix mapping, and renders the key without the coordinate text.13 This
tightly couples the visual representation in KLE to the physical matrix of the PCB, allowing
developers to trace schematics and visually apply coordinates directly in the layout editor.13
Form Factor Permutations and Variant Key Handling
Keyboards frequently support multiple physical arrangements on a single manufactured PCB.
For instance, a bottom row might support a single 6.25u spacebar (the ANSI standard) or a 7u
spacebar with a different arrangement of smaller surrounding modifier keys.18 VIA and Vial
manage these form factor variants through the concept of "Layout Options," encoded via the
bottom-right legend (index 8) of the KLE keys.1
The format for defining variant keys is option,choice (e.g., 0,1).1 The first integer defines the
layout option group (e.g., Option 0 might represent the "Bottom Row"). The second integer
defines the specific physical arrangement choice within that group. The host software defines
human-readable labels for these options in a separate labels array (e.g., ``).1 If a label is a
simple string, it acts as a boolean toggle (Choice 0 vs Choice 1).1 If it is an array of strings, it
generates a multi-select dropdown menu in the UI.1
A strict geometric constraint is enforced for this system to function: alternate layout choices
must possess an identical, combined bounding box to the default layout choice.1 If the default
Left Shift is a continuous 2.25u key, the split variant keys (e.g., a 1.25u shift and an adjacent 1u
key) must precisely equal 2.25u when their widths are summed, aligning perfectly within the
original coordinate space.13 To represent physical blockers or empty space—such as the
missing corner keys on a Happy Hacking Keyboard (HHKB) layout—VIA utilizes KLE "decal"
keys.1 These are non-functional, purely visual representations that fill the geometric void to
maintain the bounding box constraints.1 This overlay technique ensures that dynamic UI
renderers can easily swap out physical geometries without altering the absolute coordinates or
structural flow of the surrounding invariant keys.
Standardized Physical References: The ISO/IEC 9995-1 Grid
While hobbyist firmware relies on floating Cartesian coordinates and arbitrary Key Units (u),
international manufacturing standards approach keyboard geometry through highly regimented
alphanumeric grids. ISO/IEC 9995-1 specifies the general principles governing the physical
placement, spacing, and zoning of keys for all numeric, alphanumeric, and composite

information technology equipment keyboards.19
The Standard Reference Grid, Zoning, and Row Lettering
ISO/IEC 9995-1 partitions the physical keyboard into structured sections: the alphanumeric
section, editing section, numeric section, and function section.21 These sections are further
subdivided into specific functional zones. Unlike the continuous floating-point Cartesian system
of KLE, the ISO standard employs an intersection grid of rows and columns to pinpoint exact
key locations relative to one another.19
Rows are identified alphabetically, progressing from the bottom to the top. Row A represents the
bottom-most alphanumeric row containing the spacebar.21 Progressing upwards, Row B
contains the bottom alphabetical row (typically Z-X-C-V), Row C is the home row (A-S-D-F),
Row D is the top alphabetical row (Q-W-E-R), and Row E is the uppermost alphanumeric row
containing the decimal digits.21 Row K is physically separated and specifically reserved as the
reference row for the function section (comprising the F1-F12 keys).19 If a keyboard possesses
rows below the reference Row A (such as extended macro keys, custom thumb clusters on
ergonomic boards, or integrated trackpad buttons), they utilize a descending alphabetical
sequence: Z, Y, X, and so forth.19
Columns are identified by two-digit numbers.19 Column 01 is strictly designated as the primary
reference column on the left edge of the main alphanumeric block (typically aligning with the Tab
and Q keys).19 Columns extend to the right sequentially (02, 03, 04, up to 15), and extend to the
left of the reference boundary using descending values (00, 99, 98).19
Geometric Identification via ISO Key Names
The synthesis of the row letter and the column number produces a standardized,
hardware-agnostic key identification string.26 For example, the key physically located at the
intersection of Row E (the number row) and Column 01 is universally designated as <AE01>.26
The key at the intersection of Row C and Column 01 (Caps Lock) is <AC01>.
This alphanumeric grid reference provides a permanent, culturally and linguistically agnostic
method of referring to a physical location. Regardless of whether a French AZERTY layout
prints an 'A' or an American QWERTY layout prints a 'Q' at position <AD01>, the physical
geometric identifier remains completely stable across all linguistic localizations.26
Resolving ANSI, ISO, JIS, and ABNT Form Factors
The ISO/IEC 9995-1 standard provides the architectural language to pinpoint the exact physical
differences between major global form factors (ANSI, ISO, JIS, and ABNT). These differences
are strictly physical—representing the presence, absence, or dimensional shifting of keys—not
merely logical character map changes.
● ANSI (American National Standards Institute): The standard 104-key layout features a
wide 2.25u Left Shift key that occupies the physical space of both <B00> and <B01>. The
Enter key is a continuous 2.25u horizontal bar occupying <C13>. The key immediately
above it is a 1.5u key at <D13>.
● ISO (International Organization for Standardization): The standard 105-key layout

introduces critical physical alterations. The Left Shift is shortened to 1.25u, creating a
physical void at <B00> which is filled by an entirely new physical key (often containing the
backslash or angle brackets). The Enter key is a massive, stepped "L-shape" spanning
both rows C and D (<C13> and <D13>), forcing the key originally at <D13> to move down
and left into the <C12> position.5
● JIS (Japanese Industrial Standards): The 109-key JIS layout physically fractures the
Row A spacebar block. Instead of a single massive spacebar, JIS utilizes a much shorter
spacebar, introducing new physical keys directly adjacent to it (the Muhenkan and Henkan
keys). Furthermore, it introduces a physical key at <C12> (often holding the Ro character)
and another key adjacent to the backspace at <E13> (the Yen character), heavily
compressing the Backspace and Right Shift dimensions to accommodate these extra
switches.27
● ABNT (Associação Brasileira de Normas Técnicas): The Brazilian ABNT2 physical
format generally follows the ISO Enter structure but introduces an additional physical key
on Row A or Row B, typically situated between the alphanumeric block and the numeric
keypad, requiring an entirely distinct matrix column compared to US layouts.27
While the rigid ISO/IEC 9995-1 grid excels at defining these standard staggered anomalies, it
encounters severe topological limitations when mapping highly ergonomic, non-standard
geometries. It assumes a fundamentally row-staggered or ortholinear alignment. When applied
to column-staggered ergonomic designs (such as an Alice layout) or aggressive split-angle
keyboards, the orthogonal grid assumption collapses, forcing engineers to make arbitrary
assignments of keys to columns that do not logically or physically align in three-dimensional
space.
Other Relevant Sources: XKB Geometry, Tooling Exports, and
Keycaps
Beyond firmware JSONs and international specifications, the X Keyboard Extension (XKB) for
X11 operating system displays, as well as ergonomic CAD generators, utilize highly specialized
geometry descriptor formats that an open model must accommodate.
The XKB Geometry Component
In the Linux and Unix X11 ecosystem, the XKB configuration consists of several discrete
modules: keycodes, types, compat, symbols, and geometry.30 The xkb_geometry component is
explicitly responsible for providing a complete description of the physical keyboard layout,
engineered to be sufficient for rendering an accurate graphical representation directly on a
display.32
Unlike KLE or QMK, XKB geometry does not utilize arbitrary Key Units (u). Instead, its
coordinate model is strictly rooted in precise, real-world physical measurements, specifying
dimensions in tenths of a millimeter (mm/10).33 A keyboard definition declares a global
width_mm and height_mm at the root of the file.33 The geometry is hierarchically structured: a
keyboard contains sections (e.g., Alpha, Editing, Keypad).34 Sections contain rows, and rows

contain the individual keys.35
Crucially, XKB utilizes shapes and outlines to define the exact vector polygon of a key surface
and its bounding box.33 A shape may consist of an arbitrary number of plot points, allowing for
the precise mathematical definition of an L-shaped ISO Enter key or an irregularly molded
spacebar without resorting to KLE's methodology of overlaid rectangles.35 XKB also includes
definitions for doodads—physical artifacts like indicator LEDs, manufacturer logos, and
structural plastic bezels—to complete the physical rendering.33
While incredibly precise, the XKB geometry format is notoriously verbose, heavily
over-engineered for modern usage, and largely considered legacy. In contemporary Wayland
display servers utilizing libxkbcommon, the geometry component is frequently ignored or
minimally parsed due to the excessive computational overhead required to maintain it.26
Ergonomic Generative Tooling and Plate CAD
For extreme custom, column-staggered, and split geometries, modern keyboard engineers rely
on generative CAD tools like Ergogen. Ergogen's parametric YAML format defines points (the
and centers of keys) through programmatic generation rather than absolute hardcoded
coordinates.37 It uses units such as u (19.05 mm for Cherry MX switch pitch), cx (18 mm width
for Kailh Choc low-profile switches), and cy (17 mm height for Kailh Choc).6
By defining a matrix of columns and rows, and applying variables like stagger, splay (rotation),
and spread, Ergogen generates complex angled geometries algorithmically.38 These points are
then used to generate physical switch plates, PCB routing files for KiCad, and 3D printable
cases.39 The reliance on absolute physical units (mm) or strict pitch units (u) in tools like
Ergogen and swillkb 9 underscores the necessity of a geometry schema that accurately
translates virtual coordinates into manufacturable physical plate tolerances.
Keycap Profiles, Stabilizers, and Bounding Geometry
While the underlying electrical switch matrix defines the mechanical center of a key, the
geometry of the visible keycap directly impacts layout bounding boxes and legend placement
constraints.40 Keycap profiles are broadly categorized into uniform profiles (e.g., DSA, XDA,
KAM) and sculpted profiles (e.g., Cherry, OEM, SA, MT3).40 Sculpted profiles feature varying
inclinations, angles, and heights depending entirely on the ISO 9995-1 row they inhabit,
inherently restricting them from being moved between rows without disrupting the ergonomic
curvature.40
The physical shape of the keycap surface dictates the feasible boundaries for legend
placement. For instance, the uniform XDA profile possesses a wider, flatter top surface area,
allowing for broader, edge-aligned legend positioning.40 In contrast, the aggressive spherical
indentation of SA profiles restricts central legend positioning and prevents complex sub-legend
arrays from printing cleanly on the physical edges.43
Furthermore, larger physical form factors (such as the 2u, 6.25u, and 7u spacebars or large
Shift keys) require PCB-mounted stabilizers spanning multiple unit intervals to prevent the
keycap from wobbling or binding during off-center presses.18 An open geometry model must

factor the bounding box of the physical keycap width independently from the switch's central
point coordinates to accurately accommodate the routing holes required for these stabilizer
wires on the physical PCB.18
Representation of Non-Character Keys
A fundamental requirement of a comprehensive physical geometry model is the ability to
accurately map keys that do not transmit traditional printable alphanumeric characters. This
broad category includes the Numeric Keypad (Numpad), editing and navigation clusters,
multimedia controls, and OS-invisible state toggles like the Fn key.
In the ISO/IEC 9995-1 standard, the Numpad is clearly delineated as its own distinct numeric
section (ZN0) and function zone (ZN1), physically separate from the alpha block.22 Similarly,
XKB geometry isolates the Keypad and Editing clusters into distinct geometric sections in the
code, maintaining internal row and column consistency independent of the main alphanumeric
layout.34 KLE and QMK, however, process these keys identically to standard alphanumeric
keys, relying entirely on their floating Cartesian and coordinates relative to the global
origin to dictate their position.
The representation of the Fn (Function) key poses a unique systemic complication. On standard
portable laptop architectures and compact mechanical keyboards, the Fn key acts as a
hardware-level layer toggle.23 It is intercepted natively by the keyboard's embedded
microcontroller and is never transmitted to the host computer as a USB HID usage or an
operating system scancode.23 It is entirely OS-invisible. A pure physical geometry model,
however, must be capable of charting its physical dimension, location, and keycap size. To
resolve this, modern schemas must assign a geometric placeholder for these non-reporting
physical actuators, acknowledging their spatial footprint even if their logical footprint is silent.
Comparative Analysis of Geometry Schemas
The following table synthesizes the architectural approaches of the evaluated geometry formats
across critical system vectors.
Feature / KLE JSON QMK VIA / Vial XKB ISO/IEC
Capability info.json Geometry 9995-1 Grid
Coordinate Stateful Stateless Overloaded Stateless Rigid
/ Units relative absolute KLE stateful hierarchical ortholinear
Model parsing; array; JSON format. logical grid.
Cartesian Cartesian parsed into Units Intersecting
offsets. [x, y]. Units dynamic defined in Alpha/Num
Units explicit (u). frontend absolute eric Rows &
implicit memory. mm/10. Columns.
(default 1u).

Rotation /  Origin rx, ry;  Inherited  Identical to  Vector  Irrelevant.
| Odd     | angle r.    | from KLE UI  | KLE.       | polygon      | The grid     |
| ------- | ----------- | ------------ | ---------- | ------------ | ------------ |
| Shapes  | Shapes via  | exports.     | Variant    | pathing      | defines      |
|         | secondary   | Shapes via   | switching  | (points and  | topological  |
overlaid  standard w,  for rotated  outlines) for  hierarchy,
|             | rects (x2,  | h bounding   | keys is       | exact       | not physical  |
| ----------- | ----------- | ------------ | ------------- | ----------- | ------------- |
|             | y2).        | boxes.       | unsupporte    | physical    | morphology.   |
|             |             |              | d natively.   | shapes.     |               |
| Encodes     | No. Purely  | Yes.         | Yes.          | No. Solely  | No. Purely    |
| Electrical  | defines     | Dedicated    | Encoded       | defines     | a             |
| Matrix?     | visual      | matrix       | via string    | physical    | topological   |
|             | physical    | property     | parsing of    | rendering   | key           |
|             | geometry.   | explicitly   | KLE top-left  | and         | reference     |
|             |             | mapping      | legend        | hardware    | standard for  |
|             |             | [row, col].  | indices.      | component   | manufactur    |
|             |             |              |               | location.   | ers.          |
| Form-Fact   | No native   | Multiple     | Robust        | Variant     | Implicit.     |
or / Variant  support.  discrete  dynamic UI  variants  Accommod
| Handling  | Keys  | layout  | overlay.  | managed  | ates  |
| --------- | ----- | ------- | --------- | -------- | ----- |
physically  arrays (e.g.,  Encoded  via distinct  variants via
|     | overlap in  | LAYOUT_a  | via KLE       | files/section | reserved   |
| --- | ----------- | --------- | ------------- | ------------- | ---------- |
|     | the UI if   | nsi,      | bottom-right  | s overriding  | column     |
|     | drawn       | LAYOUT_is | legend        | defaults.     | locations  |
|     | together.   | o).       | (option,choi  |               | (e.g.,     |
|     |             |           | ce).          |               | <B00>).    |
Legend /  Explicit  Not natively  Overloaded  Complex  Defines
Label  12-position  defined in  KLE legend.  properties  logical
| Placement  | array      | schema.      | Text maps    | inherited     | character    |
| ---------- | ---------- | ------------ | ------------ | ------------- | ------------ |
|            | dictating  | Relies       | to UI logic  | from base     | groups and   |
|            | exact      | entirely on  | matrices,    | shapes and    | levels, not  |
|            | spatial    | external     | not visual   | font string   | physical     |
|            | quadrants  | rendering    | print.       | definitions.  | print        |
|            | on the     | logic.       |              |               | topology.    |
keycap.
Tooling /  Universal  QMK  Real-time  Legacy X11  Internationa
| Ecosystem  | hobbyist  | Firmware  | dynamic  | Linux  | l   |
| ---------- | --------- | --------- | -------- | ------ | --- |
standard.  compilation.  configurator standard.  engineering

Massive Strictly s (VIA/Vial Highly and
adoption, schema-vali desktop & verbose, hardware
weak dated browser computation manufacturi
typing/sche JSON. web apps). ally heavy ng
ma rules. to parse. compliance
framework.
Cross-Scheme Physical Key Identification
To construct an interoperable open layout schema, one must establish an immutable
methodology for referencing the exact same physical key across completely disparate systems.
The core engineering challenge lies in reconciling raw physical location (geometry) with
electrical routing (the PCB matrix) and logical output (scancodes).
Hardware Agnostic vs. Hardware Dependent Tracking
Within the QMK, VIA, and Vial ecosystems, a key is tracked internally by its electrical matrix
coordinates (row,col).5 This methodology is inherently and dangerously hardware-dependent. A
minor revision to the PCB traces by the manufacturer will alter the matrix coordinates, even if
the physical layout geometry and the user experience remain totally static. Consequently, matrix
coordinates are entirely invalid as stable primary keys for an open, hardware-agnostic geometry
schema.
Conversely, the ISO/IEC 9995-1 naming scheme (e.g., <AD01>) provides a strictly
hardware-agnostic physical reference.26 The architects of XKB universally adopted this
methodology, mapping raw evdev kernel scancodes directly to ISO physical locations before
applying any localized character mapping.26 By using <AD01>, an application knows with
absolute certainty that it is referencing the second key from the left on the second alphabetical
row from the top, regardless of how the traces are routed underneath.
Reconciling with USB HID and W3C UI Events
When an electrical switch closes, the microcontroller firmware transmits a USB HID Usage ID to
the host machine. The HID Keyboard/Keypad Page (0x07) assigns usage IDs based heavily on
the physical locations of the standard US QWERTY layout.47 For instance, Usage ID 0x04
corresponds to the physical "A" key location (Row C, Column 01), while 0x2A corresponds to
the Backspace location.48 The HID specification explicitly mandates that these codes refer to the
physical key position, regardless of the user's software localization. A German QWERTZ board
still sends the "Y" usage code (0x1C) when the physical key located at row D, column 06 is
pressed, because that is where the "Y" switch lives on an American board.47 This minimizes the
need for localized microcontroller firmware.
Modern web browsers and software applications interpret these raw inputs via the W3C UI
Events KeyboardEvent.code attribute.23 Crucially, the code attribute is designed to be purely a

physical identifier, distinct from the localized key attribute (which reports the actual letter
typed).27 Values like KeyQ, Digit1, Backspace, and Space map directly back to the physical ISO
grid coordinates.26 The code specification perfectly captures physical form-factor anomalies: the
extra key adjacent to the Left Shift on an ISO layout (<B00>) generates the IntlBackslash code,
while the extra keys on a JIS layout generate IntlRo and IntlYen.27
Furthermore, the W3C specification accounts for keys that the OS may not traditionally see, or
keys specific to varied form factors. It clearly delineates Numpad prefix codes (e.g.,
NumpadMultiply, Numpad1) to distinguish numeric pad keypresses from the identical digits in
the alphanumeric block.27 For the inherently invisible Fn key, the W3C specifies a distinct Fn
code value string. This allows a standardized geometry schema to assign a stable, universally
recognized semantic identifier to a physical key location, even if the underlying firmware
absorbs the electrical signal and never transmits a USB code.23
Therefore, to identify the same physical key definitively across all schemes, an open layout
model must map the physical geometry object directly to the stable W3C code strings (which
map exactly to the USB HID usage table), utilizing the ISO 9995-1 grid logic as the theoretical,
cross-platform basis for that mapping.
Implications for an Open Layout Model
The synthesis of the aforementioned formats, hardware constraints, and systemic limitations
yields precise architectural requirements for the geometric layer of a new open keyboard layout
model. The model must transcend the stateful parsing complexity of KLE, the hardware-coupled
matrix limitations of QMK and VIA, and the archaic verbosity of XKB geometry. The following
structural paradigms are recommended for adoption by systems engineers.
A Stateless, Explicit Coordinate Representation
The geometry layer must adopt a strictly stateless, explicit coordinate system.5 The KLE state
machine—reliant on parsing arrays sequentially and calculating relative mathematical
offsets—is a source of widespread parser incompatibility, algorithmic friction, and UI rendering
bugs.4
Each key entity in the schema layout must independently declare its absolute and
origin. The Cartesian origin `` should be standardized as the top-left corner of the physical
keyboard bounding box, with the positive axis extending to the right and the positive
axis extending downwards, mirroring standard graphical canvas and SVG implementations.5
This stateless approach allows arbitrary insertion, deletion, subsetting, and sorting of key
objects without corrupting the spatial integrity of the remaining layout structure.12
Floating-Point Units Based on the Key Unit (u)
While XKB's use of tenths of a millimeter (mm/10) 33 provides extreme physical manufacturing
accuracy, it is highly cumbersome for human maintainability and incompatible with the standard
intuitive scaling practices of the mechanical keyboard industry. The open model should define

distances using the standard Key Unit (u, where 1u generally equals 19.05 mm).5
Coordinate and dimension properties (width w, height h) should strictly accept floating-point
numbers to accommodate granular fractional spacing (e.g., an x position of 1.25, a width of 6.25
for an ANSI spacebar, or 7.0 for a Tsangan spacebar).18 Downstream tooling, CAD generators,
or UI rendering layers can internally multiply these floating-point unit values by the desired
millimeter, inch, or pixel pitch to generate physical plates or on-screen graphics.6
Stable Semantic Physical Key Identification
The model must sever the physical key identity from the hardware electrical matrix. The QMK
[row, col] paradigm restricts geometry data to a specific, potentially fleeting PCB revision.5
Instead, every physical key object must possess an immutable, semantic string ID. It is highly
recommended to adopt the W3C KeyboardEvent.code strings as the primary physical key
identifier (e.g., id: "KeyA", id: "Backspace", id: "IntlBackslash", id: "Fn").23
This guarantees universal cross-compatibility:
1. It aligns seamlessly with USB HID Usage IDs and operating system mapping behavior.50
2. It explicitly accounts for the physical differences between ANSI, ISO, and JIS layouts via
specific code strings.27
3. It accommodates non-character hardware elements, such as Fn, media controls, and
distinct Numpad keys, which possess specific W3C designations.23
4. It maps smoothly to ISO 9995-1 coordinate names if translation to Linux XKB
environments is required.26
If a specific implementation or firmware compiler requires matrix mapping, the schema should
permit an optional, entirely separate matrix object that maps the stable code IDs to specific [row,
col] hardware intersections, maintaining a strict firewall between physical geometry and
electronics routing.
Formalized Variant and Form-Factor Handling
The VIA and Vial methodology of encoding variant layout options (like split spacebars or
different bottom rows) in the bottom-right text legend of a KLE file is an ingenious hack for visual
tools, but woefully inadequate for a strict, typed data schema.1 The open layout model must
formally incorporate variant geometries as primary citizens of the schema.
This can be achieved by allowing a parent variants object containing arrays of mutually
exclusive key arrangements. Borrowing from VIA's highly effective geometric bounding logic 1,
the schema should enforce that variant options occupy the precise same outer dimensional
bounding box. Renderers can then seamlessly toggle between these arrays without affecting the
surrounding invariant geometry. To accommodate physical gaps (such as the unpopulated
blockers on a Winkeyless layout), the model should include a native is_decal or is_blocker
boolean. This formalizes the VIA/KLE decal workaround into a strictly typed property, allowing
plate generators to ignore the key while UI renderers draw the empty space.1
Handling Rotations and Complex Morphologies

To support split ergonomic keyboards, column-staggered designs, or heavily splayed thumb
clusters, the schema must support rotational properties explicitly and robustly. Drawing from
KLE's effective but flawed approach, the new schema should embed rotation_x, rotation_y, and
rotation_angle parameters strictly inside the individual key object.7 By defining the transform
origin coordinates (rx, ry) and angle (r) at the object level, the rotation remains localized and
mathematically isolated. This completely prevents the axis-shifting cascade that plagues
sequential KLE parser logic, allowing the absolute and coordinates of surrounding keys
to remain uncontaminated.7
For irregular key morphologies—specifically the L-shaped ISO Enter key and large "stepped"
modifiers—the model must absolutely eschew KLE's secondary overlaid rectangle (x2, y2, w2,
h2).7 This approach is visually limited and geometrically imprecise for plate generation.8 Instead,
the schema should utilize a shape enum (Standard, ISO_Enter, Stepped_Left, etc.) or borrow
the vector polygon path methodology from XKB to define a distinct, unified outline.33 Because
the vast majority of commercial keyboard layouts rely heavily on only a handful of
non-rectangular shapes, maintaining standard shape definitions at the schema level is far more
maintainable and computationally efficient than requiring custom rectangular offset mathematics
for every stepped keycap.8
By implementing these structural paradigms, systems engineers can guarantee a geometric
representation that is highly performant to parse, hand-maintainable for hobbyists, and
seamlessly interoperable across the entire human-computer interface stack, from firmware
compilation to physical CAD generation.
Sources des citations
1. Layouts | VIA, consulté le juin 7, 2026, https://caniusevia.com/docs/layouts/
2. keyboard-layout-editor/kb.html at master - GitHub, consulté le juin 7, 2026,
https://github.com/ijprest/keyboard-layout-editor/blob/master/kb.html
3. Paged Out! #3, consulté le juin 7, 2026,
https://pagedout.institute/download/PagedOut_003.pdf
4. ijprest/kle-serial: Serialization library for keyboard-layout-editor.com - GitHub,
consulté le juin 7, 2026, https://github.com/ijprest/kle-serial
5. info.json Reference | QMK Firmware, consulté le juin 7, 2026,
https://docs.qmk.fm/reference_info_json
6. Units | Ergogen docs, consulté le juin 7, 2026, https://docs.ergogen.xyz/units/
7. Keyboard Layout Editor JSONの使い方 - yskoht's blog, consulté le juin 7, 2026,
https://yskoht.hatenablog.com/entry/2020/12/08/001444
8. Design of mechanical keyboard - Theses, consulté le juin 7, 2026,
https://theses.cz/id/7t72mn/dp_2023_andrej_pillar.pdf?lang=en;stahnout=1;dk=qVf
FLydh
9. A Complete Guide To Building a Hand-Wired Keyboard | Cracked the Code,
consulté le juin 7, 2026,
https://www.crackedthecode.co/a-complete-guide-to-building-a-hand-wired-keyboa
rd/

10. Data Driven Configuration - QMK Firmware, consulté le juin 7, 2026,
https://docs.qmk.fm/data_driven_config
11. qmk-firmware/docs/reference_info_json.md at master - GitHub, consulté le juin 7,
2026,
https://github.com/samhocevar/fork-qmk-firmware/blob/master/docs/reference_inf
o_json.md
12. Supporting Your Keyboard in QMK Configurator, consulté le juin 7, 2026,
https://docs.qmk.fm/reference_configurator_support
13. Build support 1 - Create JSON - Vial, consulté le juin 7, 2026,
https://get.vial.today/docs/porting-to-via.html
14. Custom Keycode - Vial, consulté le juin 7, 2026,
https://get.vial.today/docs/custom_keycode.html
15. Porting guide - Vial, consulté le juin 7, 2026, https://get.vial.today/docs/
16. VIA Usage Guide - Keebio Documentation, consulté le juin 7, 2026,
https://docs.keeb.io/via
17. Specification - VIA, consulté le juin 7, 2026,
https://caniusevia.com/docs/specification/
18. KeybayPCB Screw-in Stabilizers - KeyBay Tech, consulté le juin 7, 2026,
https://keybay.tech/products/keybay-pcb-screw-in-stabilizers
19. INTERNATIONAL STANDARD - Open Standards, consulté le juin 7, 2026,
https://www.open-std.org/jtc1/sc35/wg1/docs/madison/SC35N791%20ISO-CEI%2
09995-1%20FCD(en).doc
20. ISO/IEC 9995-1:2026, consulté le juin 7, 2026,
https://webstore.iec.ch/en/publication/111520
21. ISO/IEC 9995 - Wikipedia, consulté le juin 7, 2026,
https://en.wikipedia.org/wiki/ISO/IEC_9995
22. ISO/IEC 9995-1 - iTeh Standards, consulté le juin 7, 2026,
https://cdn.standards.iteh.ai/samples/51645/8a32c7971efc4a52ac12e9416f82875
8/ISO-IEC-9995-1-2009.pdf
23. UI Events KeyboardEvent code Values - W3C, consulté le juin 7, 2026,
https://www.w3.org/TR/2015/WD-uievents-code-20151215/
24. Information technology — Keyboard layouts for text and ... - Unicode, consulté le
juin 7, 2026,
https://www.unicode.org/L2/Historical/EdHart-X3L2-Arch-2004-02-12/ISO09995/C
opy%20of%20ISO%209995-1%20Principles.html
25. ISOJIEC 995-l - iTeh Standards, consulté le juin 7, 2026,
https://cdn.standards.iteh.ai/samples/17909/8845f18596a942f0b796cbec1fd192ea
/ISO-IEC-9995-1-1994.pdf
26. The XKB keymap text format, V1 and V2 - xkbcommon, consulté le juin 7, 2026,
https://xkbcommon.org/doc/current/keymap-text-format-v1-v2.html
27. UI Events KeyboardEvent code Values - W3C, consulté le juin 7, 2026,
https://www.w3.org/TR/uievents-code/
28. Latin International keyboard layout - Wikipedia, consulté le juin 7, 2026,
https://en.wikipedia.org/wiki/Latin_International_keyboard_layout
29. Keyboard layout - Wikipedia, consulté le juin 7, 2026,

https://en.wikipedia.org/wiki/Keyboard_layout
30. The XKB Configuration Guide - FreeDesktop.Org, consulté le juin 7, 2026,
https://people.freedesktop.org/~alanc/input/XKB-Config.html
31. A simple, humble but comprehensive guide to XKB for linux | by damko - Medium,
consulté le juin 7, 2026,
https://medium.com/@damko/a-simple-humble-but-comprehensive-guide-to-xkb-f
or-linux-6f1ad5e13450
32. The X Keyboard Extension:, consulté le juin 7, 2026,
https://www.x.org/releases/X11R7.6/doc/libX11/specs/XKB/xkblib.html
33. The X Keyboard Extension:, consulté le juin 7, 2026,
https://www.x.org/releases/X11R7.7-RC1/doc/libX11/XKB/xkblib.html
34. first feed-in of the layouts. The revolution is coming - xkeyboard-config - XKB data.
(mirrored from https://gitlab.freedesktop.org/xkeyboard-config/xkeyboard-config),
consulté le juin 7, 2026,
https://cgit.freedesktop.org/xkeyboard-config/commit/?id=9bbda6b
35. The X Keyboard Extension: Protocol Specification - X Consortium Standard - xorg,
consulté le juin 7, 2026,
https://xorg.freedesktop.org/archive/current/doc/kbproto/xkbproto.pdf
36. Introduction to XKB - xkbcommon, consulté le juin 7, 2026,
https://xkbcommon.org/doc/current/xkb-intro.html
37. Let's Design A Keyboard With Ergogen v4: Introduction - FlatFootFox, consulté le
juin 7, 2026, https://flatfootfox.com/ergogen-introduction/
38. Let's Design A Keyboard With Ergogen v4: Units & Points (Part 1) - FlatFootFox,
consulté le juin 7, 2026, https://flatfootfox.com/ergogen-part1-units-points/
39. I need help with Ergogen and Kicad : r/ErgoMechKeyboards - Reddit, consulté le
juin 7, 2026,
https://www.reddit.com/r/ErgoMechKeyboards/comments/1gq8m4q/i_need_help_
with_ergogen_and_kicad/
40. Keycap profile: Ultimate comparison 2024 - Thekapco, consulté le juin 7, 2026,
https://www.thekapco.com/blogs/article/keycap-profile-ultimate-comparison-2024
41. Comparison of Different Keycap Profile : SA, DSA, OEM, Cherry, and XDA -
Goblintechkeys, consulté le juin 7, 2026,
https://goblintechkeys.com/blogs/news/comparison-of-different-keycap-profile-sa-d
sa-oem-cherry-and-xda
42. Keycap Profiles Explained: A 2026 Guide to Feel, Sound & Ergonomics - HHKB,
consulté le juin 7, 2026, https://hhkeyboard.us/blog/keycap-profiles
43. A Closer Look at Keycap Profiles: Cherry, OEM, SA, DSA, XDA Explained - Apos,
consulté le juin 7, 2026,
https://apos.audio/blogs/news/keycap-types-explained-compared
44. Why Legend Alignment Matters in High-End Keycap Sets – Gimsun, consulté le
juin 7, 2026,
https://gimsuncustom.com/blogs/gimsuncustom-keyboard-keycaps/why-legend-ali
gnment-matters-high-end-keycap-sets
45. Stabilizer V3 Screw in Stabilizers with 2u 6.25u 7u Wires PCB Mount Keyboard ...
| eBay, consulté le juin 7, 2026, https://www.ebay.com/itm/205741412295

46. xkeyboard-config/docs/README.enhancing at master - GitHub, consulté le juin 7,
2026,
https://github.com/GalliumOS/xkeyboard-config/blob/master/docs/README.enhan
cing
47. Universal Serial Bus HID Usage Tables - USB-IF, consulté le juin 7, 2026,
https://www.usb.org/sites/default/files/documents/hut1_12v2.pdf
48. USB: HID Usage Table · tmk/tmk_keyboard Wiki - GitHub, consulté le juin 7, 2026,
https://github.com/tmk/tmk_keyboard/wiki/USB:-HID-Usage-Table
49. UI Events KeyboardEvent key Values - W3C, consulté le juin 7, 2026,
https://www.w3.org/TR/uievents-key/
50. ui/base/keycodes/usb_keycode_map.h - chromium/chromium - Git at Google,
consulté le juin 7, 2026,
https://chromium.googlesource.com/chromium/chromium/+/master/ui/base/keycod
es/usb_keycode_map.h
51. Cracking the Code: Unveiling the Hidden Language of USB HID Keyboards!,
consulté le juin 7, 2026,
https://www.kenkoonwong.com/blog/usb-hid-key-press-report/