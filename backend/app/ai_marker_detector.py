import json
import re
from typing import Any

# Standard IPTC Digital Source Types and human labels
DIGITAL_SOURCE_TYPES = {
    "compositewithtrainedalgorithmicmedia": "AI-generated content composited with other media",
    "trainedalgorithmicmedia": "Pure AI-generated content",
    "algorithmicmedia": "Algorithmic / computational media",
    "compositesynthetic": "Composite synthetic media",
    "virtualrecording": "Virtual recording",
}

AI_TOOLS = {
    "Canva AI": [
        "canva ai",
        "canva magic",
        "magic media",
        "canva-magic",
    ],
    "OpenAI (DALL-E / ChatGPT)": [
        "openai",
        "dall-e",
        "dalle",
        "chatgpt",
        "gpt-4o",
    ],
    "Midjourney": [
        "midjourney",
    ],
    "Stable Diffusion": [
        "stable diffusion",
        "stablediffusion",
        "sdxl",
        "dreamstudio",
        "stability ai",
    ],
    "AUTOMATIC1111 WebUI": [
        "automatic1111",
        "stable-diffusion-webui",
    ],
    "ComfyUI": [
        "comfyui",
    ],
    "Adobe Firefly": [
        "adobe firefly",
        "firefly",
        "generative fill",
        "generative expand",
    ],
    "Google Imagen / SynthID": [
        "imagen",
        "google imagen",
        "synthid",
        "deepmind",
    ],
    "Flux": [
        "flux.1",
        "black forest labs",
    ],
    "NovelAI": [
        "novelai",
    ],
    "Leonardo.ai": [
        "leonardo.ai",
        "leonardo ai",
    ],
    "Fooocus": [
        "fooocus",
    ],
    "Civitai": [
        "civitai",
    ],
    "InvokeAI": [
        "invokeai",
    ],
    "Microsoft Designer / Copilot": [
        "bing image creator",
        "copilot designer",
        "image creator from designer",
    ],
}


def _clean_source_type(raw_val: str) -> tuple[str, str, bool]:
    """Parse raw digital source type URI or string into short name, human label, and whether it is AI."""
    lower = raw_val.lower().strip()
    short_name = lower.split("/")[-1].split("#")[-1]

    for key, label in DIGITAL_SOURCE_TYPES.items():
        if key in short_name or key in lower:
            return short_name, label, True

    if "digitalcapture" in lower:
        return "digitalCapture", "Original digital capture (camera)", False
    if "minorhumanedits" in lower:
        return "minorHumanEdits", "Minor human edits applied", False

    return short_name or raw_val, raw_val, False


def detect_ai_markers(metadata: dict[str, Any], c2pa: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """
    Comprehensive search across ExifTool metadata, XMP, IPTC, and C2PA credentials
    for known AI indicators, digital source types, and generative declarations.
    """
    detected: list[dict[str, Any]] = []
    meta = metadata or {}
    c2pa_data = c2pa or {}

    # 1. Check IPTC / C2PA Digital Source Type
    source_types_found: set[str] = set()

    # From C2PA
    if c2pa_data.get("digital_source_type"):
        source_types_found.add(str(c2pa_data["digital_source_type"]))

    # From C2PA assertions
    for assertion in c2pa_data.get("assertions", []):
        data = assertion.get("data", {})
        if isinstance(data, dict):
            for action in data.get("actions", []):
                dst = action.get("digitalSourceType")
                if dst:
                    source_types_found.add(str(dst))
            if data.get("digitalSourceType"):
                source_types_found.add(str(data["digitalSourceType"]))

    # From ExifTool metadata keys
    for k, v in meta.items():
        k_lower = k.lower()
        if "digitalsourcetype" in k_lower and v:
            source_types_found.add(str(v))

    for raw_st in source_types_found:
        short_name, human_label, is_ai = _clean_source_type(raw_st)
        if is_ai:
            detected.append({
                "tool": "IPTC / C2PA AI Declaration",
                "matched_markers": [short_name],
                "evidence_type": "c2pa_digital_source_type",
                "description": f"Digital source declared as '{human_label}'",
                "raw_value": raw_st,
            })

    # 2. Check Explicit AI Generation Flags (e.g. ContainsAiGeneratedContent: Yes)
    for k, v in meta.items():
        k_lower = k.lower()
        if "containsaigeneratedcontent" in k_lower or "aigeneratedcontent" in k_lower:
            val_str = str(v).strip().lower()
            if val_str in ("yes", "true", "1"):
                detected.append({
                    "tool": "AI Content Declaration",
                    "matched_markers": [f"{k.split(':')[-1]}: {v}"],
                    "evidence_type": "xmp_ai_declaration",
                    "description": f"Explicit metadata flag: {k.split(':')[-1]} = '{v}'",
                })

    # 3. Check C2PA / CBOR SoftwareAgent (e.g. "Canva AI", "Adobe Firefly")
    software_agents: set[str] = set()
    if meta.get("CBOR:ActionsSoftwareAgent"):
        software_agents.add(str(meta["CBOR:ActionsSoftwareAgent"]))

    for assertion in c2pa_data.get("assertions", []):
        data = assertion.get("data", {})
        if isinstance(data, dict):
            for action in data.get("actions", []):
                agent = action.get("softwareAgent")
                if agent:
                    software_agents.add(str(agent))

    for agent in software_agents:
        agent_lower = agent.lower()
        # If agent mentions "ai" or matches known generators
        if " ai" in agent_lower or "ai " in agent_lower or agent_lower.endswith("ai") or any(t.lower() in agent_lower for t in AI_TOOLS):
            detected.append({
                "tool": agent,
                "matched_markers": [agent],
                "evidence_type": "c2pa_software_agent",
                "description": f"C2PA Actions SoftwareAgent identified as '{agent}'",
            })

    # 4. Search text and key-value fields for known AI tool signatures
    # Build a flattened searchable string
    searchable = json.dumps(
        {
            "metadata": meta,
            "c2pa": c2pa_data,
        },
        ensure_ascii=False,
        default=str,
    ).lower()

    for tool_name, markers in AI_TOOLS.items():
        matched = []
        for marker in markers:
            # Match marker with word boundaries or punctuation boundaries
            pattern = r"(?:^|[^a-z0-9])" + re.escape(marker) + r"(?:$|[^a-z0-9])"
            if re.search(pattern, searchable):
                matched.append(marker)

        if matched:
            detected.append({
                "tool": tool_name,
                "matched_markers": matched,
                "evidence_type": "generator_signature",
                "description": f"Matched generator marker: {', '.join(matched)}",
            })

    # Remove duplicates
    unique: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    for item in detected:
        key = (item["tool"], tuple(item.get("matched_markers", [])))
        unique[key] = item

    return list(unique.values())


def format_ai_markers_for_ui(signals: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Format AI marker signals for UI components."""
    formatted = []
    for sig in signals:
        tool = sig.get("tool", "AI Indicator")
        matched = sig.get("matched_markers", [])
        evidence = sig.get("evidence_type", "metadata")
        desc = sig.get("description") or (f"Matched terms: {', '.join(matched)}" if matched else "Identified as AI-generated")
        formatted.append({
            "name": tool,
            "source": evidence.replace("_", " ").upper(),
            "description": desc,
        })
    return formatted


def generate_structured_report(
    metadata: dict[str, Any],
    c2pa_data: dict[str, Any],
    ai_signals_list: list[dict[str, Any]],
    image_info: dict[str, Any]
) -> dict[str, Any]:
    """
    Generate complete structured report with verdict, detailed AI signals breakdown,
    and organized groups (AI Provenance Signals, Identifying Data, C2PA Structure, Technical Data).
    """
    ai_count = len(ai_signals_list)
    has_ai = ai_count > 0

    # 1. Verdict
    if has_ai:
        verdict = {
            "kind": "ai-signals",
            "headline": "AI metadata detected",
            "detail": f"Found {ai_count} AI marker signal{'s' if ai_count > 1 else ''} in image provenance and metadata.",
        }
    else:
        verdict = {
            "kind": "no-ai-signals",
            "headline": "No known AI metadata detected",
            "detail": "Metadata can be stripped or missing, so absence of markers is not proof an image is human-made.",
        }

    # 2. Extract Digital Source Type detail
    digital_source_type_info = None
    for sig in ai_signals_list:
        if sig.get("evidence_type") == "c2pa_digital_source_type":
            raw_val = sig.get("raw_value") or sig.get("matched_markers", [""])[0]
            short_name, human_label, _ = _clean_source_type(raw_val)
            digital_source_type_info = {
                "raw": raw_val,
                "label": human_label,
            }
            break

    # 3. Extract C2PA boxes and structure
    jumbf_boxes = []
    for k, v in metadata.items():
        if k.startswith("JUMBF:") or k.startswith("CBOR:"):
            jumbf_boxes.append({"label": k, "value": str(v)})

    # Determine signature and signer
    sig_info = c2pa_data.get("signature_info", {})
    signer = sig_info.get("issuer") or sig_info.get("common_name") or metadata.get("CBOR:ActionsSoftwareAgent") or (
        "Signed" if c2pa_data.get("has_manifest") else None
    )

    # 4. Form Groups
    groups = []

    # Group: AI Provenance Signals
    ai_fields = []
    if digital_source_type_info:
        ai_fields.append({"label": "Digital source type", "value": digital_source_type_info["label"]})
    if signer:
        ai_fields.append({"label": "Signed by / Generator", "value": signer})
    if c2pa_data.get("recorded_actions"):
        ai_fields.append({"label": "Recorded actions", "value": ", ".join(c2pa_data["recorded_actions"])})
    elif metadata.get("CBOR:ActionsAction"):
        ai_fields.append({"label": "Recorded actions", "value": str(metadata["CBOR:ActionsAction"])})

    for k, v in metadata.items():
        if "containsaigeneratedcontent" in k.lower():
            ai_fields.append({"label": "AI Generated Content", "value": str(v)})

    for sig in ai_signals_list:
        if sig.get("evidence_type") == "generator_signature":
            ai_fields.append({"label": "Tool signature", "value": sig.get("tool", "")})

    if c2pa_data.get("has_manifest"):
        manifest_status = f"{c2pa_data.get('manifest_count', 1)} manifest, {'signed' if signer else 'unsigned'}"
        ai_fields.append({"label": "Content Credentials", "value": manifest_status})

    if ai_fields:
        groups.append({
            "id": "ai",
            "title": "AI Provenance Signals",
            "fields": ai_fields,
        })

    # Group: Identifying Data (Privacy)
    privacy_fields = []
    for k, v in metadata.items():
        k_lower = k.lower()
        if any(term in k_lower for term in ("software", "creatortool", "author", "artist", "owner", "ads", "touchtype", "title")):
            clean_label = k.split(":")[-1]
            privacy_fields.append({"label": clean_label, "value": str(v)})

    if privacy_fields:
        groups.append({
            "id": "privacy",
            "title": "Identifying & Author Data",
            "fields": privacy_fields,
        })

    # Group: C2PA Manifest Structure
    c2pa_fields = []
    if c2pa_data.get("has_manifest"):
        if c2pa_data.get("active_manifest"):
            c2pa_fields.append({"label": "Active Manifest URN", "value": c2pa_data["active_manifest"]})
        if c2pa_data.get("validation_state"):
            c2pa_fields.append({"label": "Validation State", "value": c2pa_data["validation_state"]})

    for b in jumbf_boxes[:15]:
        c2pa_fields.append({"label": b["label"].split(":")[-1], "value": b["value"]})

    if c2pa_fields:
        groups.append({
            "id": "c2pa-structure",
            "title": "C2PA Manifest Structure",
            "fields": c2pa_fields,
        })

    # Group: Technical Data
    technical_fields = []
    for k in ("format", "width", "height", "mode"):
        if image_info.get(k):
            technical_fields.append({"label": k.capitalize(), "value": str(image_info[k])})

    for k, v in metadata.items():
        k_lower = k.lower()
        if any(term in k_lower for term in ("bitdepth", "colortype", "compression", "filter", "interlace", "resolution", "colorspace", "orientation")):
            clean_label = k.split(":")[-1]
            technical_fields.append({"label": clean_label, "value": str(v)})

    if technical_fields:
        groups.append({
            "id": "technical",
            "title": "Technical Specifications",
            "fields": technical_fields,
        })

    generator_sigs = [
        sig["tool"] for sig in ai_signals_list if sig.get("evidence_type") in ("generator_signature", "c2pa_software_agent")
    ]

    digital_source_types = [
        sig["raw_value"] for sig in ai_signals_list if sig.get("raw_value")
    ]
    if not digital_source_types and c2pa_data.get("digital_source_type"):
        digital_source_types = [str(c2pa_data["digital_source_type"])]

    ai_signals_obj = {
        "count": ai_count,
        "digitalSourceType": digital_source_type_info,
        "c2paManifestDetected": bool(c2pa_data.get("has_manifest")),
        "c2pa": {
            "present": bool(c2pa_data.get("has_manifest")),
            "signed": bool(signer),
            "claimGenerator": signer or "c2pa-rs",
            "actions": c2pa_data.get("recorded_actions") or ([str(metadata.get("CBOR:ActionsAction"))] if metadata.get("CBOR:ActionsAction") else []),
            "manifestCount": c2pa_data.get("manifest_count", 1 if c2pa_data.get("has_manifest") else 0),
            "digitalSourceTypes": digital_source_types,
        },
        "generatorSignatures": list(set(generator_sigs)),
        "explicitAiDeclarations": [
            {"field": sig["matched_markers"][0], "description": sig["description"]}
            for sig in ai_signals_list if sig.get("evidence_type") == "xmp_ai_declaration"
        ],
    }

    return {
        "verdict": verdict,
        "ai_signals": ai_signals_obj,
        "groups": groups,
    }
