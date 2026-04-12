# -*- coding: utf-8 -*-
"""
Heuristic extraction of equipment flags from listing text (title, description,
structured equipment lists). Used by scrapers — no manual admin entry required.
"""
import re
from typing import Any, Dict, Iterable, List, Optional

# Keep literal values in sync with offers.models.AudioSystem
_AUDIO_BOWERS = "bowers_wilkins"
_AUDIO_HK = "harman_kardon"
_AUDIO_STANDARD = "standard"
_AUDIO_OTHER_PREMIUM = "other_premium"


def _norm(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s.lower()).strip()


def _any(hay: str, patterns: Iterable[re.Pattern]) -> bool:
    return any(p.search(hay) for p in patterns)


def _combine_haystack(*parts: str) -> str:
    return _norm(" \n ".join(p for p in parts if p))


def flatten_otomoto_equipment(equipment: Any) -> str:
    if not equipment or not isinstance(equipment, list):
        return ""
    out: List[str] = []
    for grp in equipment:
        if not isinstance(grp, dict):
            continue
        for val in grp.get("values") or []:
            if isinstance(val, dict):
                out.append(val.get("label") or "")
    return " ".join(out)


def flatten_autoscout_equipment(equipment: Any) -> str:
    if not equipment or not isinstance(equipment, dict):
        return ""
    parts: List[str] = []
    for _cat, items in equipment.items():
        if not isinstance(items, list):
            continue
        for it in items:
            if isinstance(it, dict):
                parts.append(it.get("id") or "")
            else:
                parts.append(str(it))
    return " ".join(parts)


def empty_feature_defaults() -> Dict[str, Any]:
    return {
        "feature_awd": None,
        "feature_increased_clearance_off_road_mode": None,
        "feature_hill_descent_control": None,
        "feature_rear_air_suspension": None,
        "feature_pilot_assist": None,
        "feature_city_safety": None,
        "feature_cross_traffic_alert_reverse_brake": None,
        "feature_surround_view_camera_360": None,
        "feature_front_rear_parking_sensors": None,
        "feature_panoramic_roof": None,
        "feature_four_zone_climate": None,
        "feature_power_tailgate": None,
        "feature_remote_rear_seatback_release": None,
        "feature_folding_rear_headrests": None,
        "audio_system": "",
        "feature_google_built_in_infotainment": None,
        "feature_wood_or_metal_inlays": None,
        "feature_crystal_gear_selector": None,
        "feature_ambient_lighting_package": None,
    }


# --- regex patterns (multilingual: EN / DE / PL common in listings) ---

_P = {
    "awd": [
        re.compile(r"\bawd\b", re.I),
        re.compile(r"\b4wd\b", re.I),
        re.compile(r"\b4x4\b", re.I),
        re.compile(r"all[-\s]?wheel", re.I),
        re.compile(r"allrad", re.I),
        re.compile(r"napęd\s+na\s+4\s+koła", re.I),
        re.compile(r"napęd\s+na\s+wszystkie", re.I),
    ],
    "fwd": [
        re.compile(r"\bfwd\b", re.I),
        re.compile(r"front[-\s]?wheel", re.I),
        re.compile(r"vorderradantrieb", re.I),
        re.compile(r"napęd\s+na\s+przednie", re.I),
    ],
    "cross_country": [
        re.compile(r"cross\s*country", re.I),
        re.compile(r"\bv90\s*cc\b", re.I),
        re.compile(r"v60\s*cc\b", re.I),
    ],
    "off_road_mode": [
        re.compile(r"off[-\s]?road", re.I),
        re.compile(r"offroad", re.I),
        re.compile(r"tryb\s+terenowy", re.I),
        re.compile(r"jazda\s+terenowa", re.I),
    ],
    "ground_clearance": [
        re.compile(r"ground\s*clearance", re.I),
        re.compile(r"raised\s+suspension", re.I),
        re.compile(r"większy\s+prześwit", re.I),
        re.compile(r"zwiększon(y|a)\s+prześwit", re.I),
    ],
    "hill_descent": [
        re.compile(r"hill\s*descent", re.I),
        re.compile(r"\bhdc\b", re.I),
        re.compile(r"bergabfahr", re.I),
        re.compile(r"zjazd\s+ze\s+wznies", re.I),
    ],
    "air_susp": [
        re.compile(r"air\s*suspension", re.I),
        re.compile(r"pneumatic\s*suspension", re.I),
        re.compile(r"self[-\s]?levell?ing", re.I),
        re.compile(r"four[-\s]?c\b", re.I),
        re.compile(r"zawieszenie\s+pneumatyczne", re.I),
        re.compile(r"pneumatyczne\s+zawieszenie", re.I),
        re.compile(r"nivelacja", re.I),
        re.compile(r"adaptacyjn(e|y)\s+zawieszen", re.I),
    ],
    "pilot_assist": [
        re.compile(r"pilot\s*assist", re.I),
        re.compile(r"intel\s*safe", re.I),
        re.compile(r"drive\s*assist", re.I),
    ],
    "city_safety": [
        re.compile(r"city\s*safety", re.I),
        re.compile(r"collision\s*avoidance", re.I),
        re.compile(r"aeb\b", re.I),
        re.compile(r"automatyczne\s+hamowanie", re.I),
        re.compile(r"bezpieczeństwo\s+miejskie", re.I),
    ],
    "cta_brake": [
        re.compile(r"cross\s*traffic", re.I),
        re.compile(r"rear\s*collision\s*warning", re.I),
        re.compile(r"auto[-\s]?brake.*revers", re.I),
        re.compile(r"automatyczne\s+hamowanie.*cofan", re.I),
    ],
    "cam360": [
        re.compile(r"360\s*°?\s*camera", re.I),
        re.compile(r"360[-\s]?degree", re.I),
        re.compile(r"surround\s*view", re.I),
        re.compile(r"surround\s*camera", re.I),
        re.compile(r"birds?\s*eye", re.I),
        re.compile(r"widok\s+360", re.I),
        re.compile(r"kamera\s+360", re.I),
    ],
    "parking_sensors": [
        re.compile(r"parking\s*assist\s*system\s*sensors", re.I),
        re.compile(r"park(ing)?\s*distance\s*control", re.I),
        re.compile(r"\bpdc\b", re.I),
        re.compile(r"front.*rear.*sensor", re.I),
        re.compile(r"sensor.*front.*rear", re.I),
        re.compile(r"czujnik(i)?\s+parkowania", re.I),
        re.compile(r"przód.*tył.*czuj", re.I),
    ],
    "panoramic": [
        re.compile(r"panoramic", re.I),
        re.compile(r"panorama", re.I),
        re.compile(r"glass\s*roof", re.I),
        re.compile(r"sun\s*roof", re.I),
        re.compile(r"schiebedach", re.I),
        re.compile(r"dach\s+panoramiczny", re.I),
        re.compile(r"szyberdach", re.I),
    ],
    "four_zone": [
        re.compile(r"four[-\s]?zone", re.I),
        re.compile(r"4[-\s]?zone", re.I),
        re.compile(r"quad[-\s]?zone", re.I),
        re.compile(r"4[-\s]?stref", re.I),
        re.compile(r"czterostref", re.I),
    ],
    "power_tail": [
        re.compile(r"electric\s*tailgate", re.I),
        re.compile(r"power\s*tailgate", re.I),
        re.compile(r"hands[-\s]?free.*tailgate", re.I),
        re.compile(r"elektryczn\w+\s+klap", re.I),
        re.compile(r"elektryczna\s+klapa", re.I),
    ],
    "rear_seat_release": [
        re.compile(r"remote.*rear.*seat", re.I),
        re.compile(r"rear\s*seat.*release", re.I),
        re.compile(r"one[-\s]?touch.*seat", re.I),
        re.compile(r"cargo.*seat.*fold", re.I),
        re.compile(r"składanie\s+foteli.*bagaż", re.I),
    ],
    "fold_headrest": [
        re.compile(r"folding\s*rear\s*headrest", re.I),
        re.compile(r"fold.*headrest", re.I),
        re.compile(r"składane\s+zagłówki", re.I),
    ],
    "bowers": [
        re.compile(r"bowers\s*[&\u0026]?\s*wilkins", re.I),
        re.compile(r"\bb\s*&\s*w\b", re.I),
        re.compile(r"\bb\s*/\s*w\b", re.I),
        re.compile(r"bowers\s+and\s+wilkins", re.I),
    ],
    "harman": [
        re.compile(r"harman\s*/?\s*kardon", re.I),
        re.compile(r"high\s*performance\s*sound", re.I),
    ],
    "google_infotainment": [
        re.compile(r"google\s*built[-\s]?in", re.I),
        re.compile(r"android\s*automotive", re.I),
        re.compile(r"google\s*play\s*store", re.I),
        re.compile(r"google\s*assistant", re.I),
        re.compile(r"google\s*maps", re.I),
    ],
    "wood_metal": [
        re.compile(r"wood\s*(inlay|trim|decor)", re.I),
        re.compile(r"metal\s*inlay", re.I),
        re.compile(r"aluminium\s*trim", re.I),
        re.compile(r"aluminum\s*trim", re.I),
        re.compile(r"intarsja", re.I),
        re.compile(r"fornir", re.I),
        re.compile(r"drewniane\s+wykończen", re.I),
    ],
    "crystal": [
        re.compile(r"crystal\s*gear", re.I),
        re.compile(r"orsefors", re.I),
        re.compile(r"kryształ", re.I),
        re.compile(r"szklana\s+gałka", re.I),
    ],
    "ambient": [
        re.compile(r"ambient\s*light", re.I),
        re.compile(r"mood\s*light", re.I),
        re.compile(r"atmosphere\s*light", re.I),
        re.compile(r"oświetlenie\s+ambient", re.I),
    ],
}


def infer_features_from_text(
    *,
    title: str = "",
    description: str = "",
    equipment_text: str = "",
    main_features_text: str = "",
    drive_train: str = "",
    transmission: str = "",
    model_line: str = "",
) -> Dict[str, Any]:
    """
    Return a dict suitable for merging into CarOffer (all feature keys + audio_system).
    """
    out = empty_feature_defaults()
    hay = _combine_haystack(title, description, equipment_text, main_features_text, drive_train, transmission, model_line)

    if not hay and not _norm(drive_train):
        return out

    dt = _norm(drive_train)
    tr = _norm(transmission)

    # AWD vs FWD from structured fields first
    if dt or tr:
        combined_dt = dt + " " + tr
        if _any(combined_dt, _P["fwd"]):
            out["feature_awd"] = False
        elif _any(combined_dt, _P["awd"]):
            out["feature_awd"] = True

    # Text fallbacks for AWD
    if out["feature_awd"] is None:
        if _any(hay, _P["fwd"]):
            out["feature_awd"] = False
        elif _any(hay, _P["awd"]):
            out["feature_awd"] = True

    # V90/V60 Cross Country → usually raised clearance + AWD
    if _any(hay, _P["cross_country"]):
        out["feature_increased_clearance_off_road_mode"] = True
        if out["feature_awd"] is None:
            out["feature_awd"] = True

    if _any(hay, _P["off_road_mode"]) or _any(hay, _P["ground_clearance"]):
        out["feature_increased_clearance_off_road_mode"] = True

    if _any(hay, _P["hill_descent"]):
        out["feature_hill_descent_control"] = True

    if _any(hay, _P["air_susp"]):
        out["feature_rear_air_suspension"] = True

    if _any(hay, _P["pilot_assist"]):
        out["feature_pilot_assist"] = True

    if _any(hay, _P["city_safety"]):
        out["feature_city_safety"] = True

    if _any(hay, _P["cta_brake"]):
        out["feature_cross_traffic_alert_reverse_brake"] = True

    if _any(hay, _P["cam360"]):
        out["feature_surround_view_camera_360"] = True

    if _any(hay, _P["parking_sensors"]):
        out["feature_front_rear_parking_sensors"] = True

    if _any(hay, _P["panoramic"]):
        out["feature_panoramic_roof"] = True

    if _any(hay, _P["four_zone"]):
        out["feature_four_zone_climate"] = True

    if _any(hay, _P["power_tail"]):
        out["feature_power_tailgate"] = True

    if _any(hay, _P["rear_seat_release"]):
        out["feature_remote_rear_seatback_release"] = True

    if _any(hay, _P["fold_headrest"]):
        out["feature_folding_rear_headrests"] = True

    if _any(hay, _P["google_infotainment"]):
        out["feature_google_built_in_infotainment"] = True

    if _any(hay, _P["wood_metal"]):
        out["feature_wood_or_metal_inlays"] = True

    if _any(hay, _P["crystal"]):
        out["feature_crystal_gear_selector"] = True

    if _any(hay, _P["ambient"]):
        out["feature_ambient_lighting_package"] = True

    # Audio (priority: Bowers > Harman > other premium > standard)
    if _any(hay, _P["bowers"]):
        out["audio_system"] = _AUDIO_BOWERS
    elif _any(hay, _P["harman"]):
        out["audio_system"] = _AUDIO_HK
    elif re.search(r"premium\s*sound|sound\s*system\s*premium|audio\s*premium", hay, re.I):
        out["audio_system"] = _AUDIO_OTHER_PREMIUM
    elif re.search(r"\bstandard\s*audio\b|base\s*audio|radio\s*cd\b", hay, re.I):
        out["audio_system"] = _AUDIO_STANDARD

    return out


def infer_from_otomoto_advert(advert: dict) -> Dict[str, Any]:
    title = advert.get("title") or ""
    desc = advert.get("description") or ""
    mf = advert.get("mainFeatures") or []
    mf_txt = " ".join(str(x) for x in mf) if isinstance(mf, list) else ""
    eq_txt = flatten_otomoto_equipment(advert.get("equipment"))
    pd = advert.get("parametersDict") or {}

    def lbl(key):
        e = pd.get(key)
        if not e:
            return ""
        vals = e.get("values") or []
        if vals and isinstance(vals[0], dict):
            return vals[0].get("label") or ""
        return ""

    model_line = (lbl("model") or "") + " " + (advert.get("title") or "")

    return infer_features_from_text(
        title=title,
        description=desc,
        equipment_text=eq_txt,
        main_features_text=mf_txt,
        drive_train=lbl("transmission"),
        transmission=lbl("gearbox"),
        model_line=model_line,
    )


def _strip_html_basic(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"<[^>]+>", " ", s)


def infer_from_autoscout_listing_details(ld: dict) -> Dict[str, Any]:
    v = ld.get("vehicle") or {}
    desc = _strip_html_basic(ld.get("description") or "")
    eq_txt = flatten_autoscout_equipment(v.get("equipment"))
    marketing = v.get("marketingDescription") or ""
    alt = ld.get("imgAltText") or ""
    drive = v.get("driveTrain") or ""
    title_guess = " ".join(
        filter(
            None,
            [
                v.get("make"),
                v.get("model"),
                v.get("modelVersionInput") or v.get("variant"),
            ],
        )
    )

    return infer_features_from_text(
        title=title_guess + " " + alt,
        description=desc + " " + marketing,
        equipment_text=eq_txt,
        main_features_text="",
        drive_train=drive,
        transmission=v.get("transmissionType") or "",
        model_line=(v.get("variant") or "") + " " + (v.get("model") or ""),
    )
