# -*- coding: utf-8 -*-
"""Tables et conversions de base partagees par les outils OKLM.

- POSITION_TABLE : position ISO/IEC 9995-1 -> (HID page 0x07, alias XKB, W3C KeyboardEvent.code)
- SCANCODE_TO_HID : scancode Windows set 1 -> HID, contre-verification de POSITION_TABLE
- LEVEL_MAP / LEVEL_SELECTORS : champs de la source -> niveaux ISO -> selecteurs OKLM
- dead_key_id / convert_output : identifiants de touches mortes et sorties de touche

Module suivi, sans dependance : tools/qwerty_global.py en depend. Source unique de ces tables dans le depot.
"""

# Table ISO/IEC 9995-1 -> (HID page 0x07, alias XKB, W3C KeyboardEvent.code).
POSITION_TABLE = {
    "E00": ("0x35", "TLDE", "Backquote"),
    "E01": ("0x1E", "AE01", "Digit1"), "E02": ("0x1F", "AE02", "Digit2"),
    "E03": ("0x20", "AE03", "Digit3"), "E04": ("0x21", "AE04", "Digit4"),
    "E05": ("0x22", "AE05", "Digit5"), "E06": ("0x23", "AE06", "Digit6"),
    "E07": ("0x24", "AE07", "Digit7"), "E08": ("0x25", "AE08", "Digit8"),
    "E09": ("0x26", "AE09", "Digit9"), "E10": ("0x27", "AE10", "Digit0"),
    "E11": ("0x2D", "AE11", "Minus"), "E12": ("0x2E", "AE12", "Equal"),
    "D01": ("0x14", "AD01", "KeyQ"), "D02": ("0x1A", "AD02", "KeyW"),
    "D03": ("0x08", "AD03", "KeyE"), "D04": ("0x15", "AD04", "KeyR"),
    "D05": ("0x17", "AD05", "KeyT"), "D06": ("0x1C", "AD06", "KeyY"),
    "D07": ("0x18", "AD07", "KeyU"), "D08": ("0x0C", "AD08", "KeyI"),
    "D09": ("0x12", "AD09", "KeyO"), "D10": ("0x13", "AD10", "KeyP"),
    "D11": ("0x2F", "AD11", "BracketLeft"), "D12": ("0x30", "AD12", "BracketRight"),
    "D13": ("0x31", "BKSL", "Backslash"),
    "C01": ("0x04", "AC01", "KeyA"), "C02": ("0x16", "AC02", "KeyS"),
    "C03": ("0x07", "AC03", "KeyD"), "C04": ("0x09", "AC04", "KeyF"),
    "C05": ("0x0A", "AC05", "KeyG"), "C06": ("0x0B", "AC06", "KeyH"),
    "C07": ("0x0D", "AC07", "KeyJ"), "C08": ("0x0E", "AC08", "KeyK"),
    "C09": ("0x0F", "AC09", "KeyL"), "C10": ("0x33", "AC10", "Semicolon"),
    "C11": ("0x34", "AC11", "Quote"), "C12": ("0x31", "BKSL", "Backslash"),
    "B00": ("0x64", "LSGT", "IntlBackslash"),
    "B01": ("0x1D", "AB01", "KeyZ"), "B02": ("0x1B", "AB02", "KeyX"),
    "B03": ("0x06", "AB03", "KeyC"), "B04": ("0x19", "AB04", "KeyV"),
    "B05": ("0x05", "AB05", "KeyB"), "B06": ("0x11", "AB06", "KeyN"),
    "B07": ("0x10", "AB07", "KeyM"), "B08": ("0x36", "AB08", "Comma"),
    "B09": ("0x37", "AB09", "Period"), "B10": ("0x38", "AB10", "Slash"),
    "A03": ("0x2C", "SPCE", "Space"),
}

# Contre-vérification : scancode Windows set 1 (champ `scancode` de la source)
# -> HID usage attendu. Toute divergence avec POSITION_TABLE est une erreur.
SCANCODE_TO_HID = {
    "SC029": "0x35",
    "SC002": "0x1E", "SC003": "0x1F", "SC004": "0x20", "SC005": "0x21",
    "SC006": "0x22", "SC007": "0x23", "SC008": "0x24", "SC009": "0x25",
    "SC00A": "0x26", "SC00B": "0x27", "SC00C": "0x2D", "SC00D": "0x2E",
    "SC010": "0x14", "SC011": "0x1A", "SC012": "0x08", "SC013": "0x15",
    "SC014": "0x17", "SC015": "0x1C", "SC016": "0x18", "SC017": "0x0C",
    "SC018": "0x12", "SC019": "0x13", "SC01A": "0x2F", "SC01B": "0x30",
    "SC01E": "0x04", "SC01F": "0x16", "SC020": "0x07", "SC021": "0x09",
    "SC022": "0x0A", "SC023": "0x0B", "SC024": "0x0D", "SC025": "0x0E",
    "SC026": "0x0F", "SC027": "0x33", "SC028": "0x34", "SC02B": "0x31",
    "SC056": "0x64",
    "SC02C": "0x1D", "SC02D": "0x1B", "SC02E": "0x06", "SC02F": "0x19",
    "SC030": "0x05", "SC031": "0x11", "SC032": "0x10", "SC033": "0x36",
    "SC034": "0x37", "SC035": "0x38", "SC039": "0x2C",
}

# Champ source -> niveau ISO.
LEVEL_MAP = [
    ("base", "1"), ("shift", "2"), ("alt_gr", "3"), ("shift_alt_gr", "4"),
    ("caps", "5"), ("caps_shift", "6"), ("caps_alt_gr", "7"),
    ("caps_shift_alt_gr", "8"),
]

LEVEL_SELECTORS = {
    "2": ["Level2Shift"],
    "3": ["Level3Shift"],
    "4": ["Level2Shift", "Level3Shift"],
    "5": ["CapsLock"],
    "6": ["CapsLock", "Level2Shift"],
    "7": ["CapsLock", "Level3Shift"],
    "8": ["CapsLock", "Level2Shift", "Level3Shift"],
}


def dead_key_id(raw):
    """dk_misc_symbols -> misc-symbols (pattern OKLM ^[a-z][a-z0-9-]*$)."""
    if not raw.startswith("dk_"):
        raise ValueError(f"identifiant de touche morte sans prefixe dk_ : {raw!r}")
    return raw[3:].replace("_", "-")


def convert_output(value):
    if value.startswith("dk_"):
        return {"deadKey": dead_key_id(value)}
    return value
