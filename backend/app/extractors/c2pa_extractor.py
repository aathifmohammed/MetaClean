import json
from pathlib import Path
from typing import Any

try:
    import c2pa
    HAS_C2PA = True
except ImportError:
    c2pa = None
    HAS_C2PA = False


def extract_c2pa(file_path: str) -> dict[str, Any]:
    """Read C2PA credentials and manifest information if present."""
    base_result: dict[str, Any] = {
        "available": HAS_C2PA,
        "has_manifest": False,
        "active_manifest": None,
        "manifest_count": 0,
        "digital_source_type": None,
        "recorded_actions": [],
        "ingredients": [],
        "assertions": [],
        "signature_info": {},
        "validation_state": None,
        "validation_results": None,
        "raw_manifest": None,
        "error": None,
    }

    path = Path(file_path)
    if not path.is_file():
        base_result["error"] = f"File not found: {file_path}"
        return base_result

    if not HAS_C2PA:
        base_result["error"] = "c2pa library is not installed in the environment."
        return base_result

    try:
        reader = c2pa.Reader.try_create(str(path))
        if reader is None:
            # Asset has no C2PA / JUMBF manifest
            return base_result

        with reader:
            manifest_json_str = reader.json()
            manifest_data = json.loads(manifest_json_str) if manifest_json_str else {}

            active_manifest_label = manifest_data.get("active_manifest")
            manifests = manifest_data.get("manifests", {})
            active_manifest = manifests.get(active_manifest_label, {}) if active_manifest_label else {}

            # Extract assertions & actions
            assertions = active_manifest.get("assertions", [])
            recorded_actions = []
            digital_source_type = None

            for assertion in assertions:
                label = assertion.get("label", "")
                data = assertion.get("data", {})
                if "c2pa.actions" in label and isinstance(data, dict):
                    actions = data.get("actions", [])
                    for act in actions:
                        action_name = act.get("action", "")
                        if action_name:
                            recorded_actions.append(action_name)
                        # Digital source type might be under action
                        dst = act.get("digitalSourceType")
                        if dst and not digital_source_type:
                            digital_source_type = dst
                if "digitalSourceType" in data and not digital_source_type:
                    digital_source_type = data["digitalSourceType"]

            base_result.update({
                "has_manifest": True,
                "active_manifest": active_manifest_label,
                "manifest_count": len(manifests),
                "digital_source_type": digital_source_type,
                "recorded_actions": recorded_actions,
                "ingredients": active_manifest.get("ingredients", []),
                "assertions": assertions,
                "signature_info": active_manifest.get("signature_info", {}),
                "validation_state": getattr(reader, "get_validation_state", lambda: None)(),
                "raw_manifest": manifest_data,
            })
            return base_result

    except Exception as exc:
        base_result["error"] = str(exc)
        return base_result
