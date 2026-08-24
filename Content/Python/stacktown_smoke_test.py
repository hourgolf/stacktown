"""Read-only-by-default Portland smoke inspection for Unreal Editor 5.8."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


def _project_path(*parts: str) -> Path:
    return Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), *parts)


def _load_config() -> dict:
    with _project_path("Config", "StacktownValidation.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def _current_map_name() -> str:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world is None:
        return ""
    try:
        return str(world.get_outermost().get_name())
    except Exception:
        return str(world.get_path_name()).split(".", 1)[0]


def run_smoke() -> dict:
    config = _load_config()
    smoke = config["smoke"]
    target_map = smoke["target_map"]
    report = {
        "schema_version": 1,
        "mode": "inspect_only",
        "target_map": target_map,
        "current_map": _current_map_name(),
        "failures": [],
        "warnings": [],
        "passed": [],
        "pending_decisions": [],
    }

    if not unreal.EditorAssetLibrary.does_asset_exist(target_map):
        report["failures"].append({"code": "TARGET_MAP_MISSING", "detail": target_map})
    else:
        report["passed"].append("Target Portland map asset exists.")

    if report["current_map"] == target_map:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        labels = {actor.get_actor_label() for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)}
        missing = sorted(set(smoke["required_actor_labels"]) - labels)
        if missing:
            report["failures"].append({"code": "CRITICAL_ACTORS_MISSING", "detail": missing})
        else:
            report["passed"].append("All configured critical actor labels exist.")
    else:
        report["warnings"].append({
            "code": "TARGET_MAP_NOT_OPEN",
            "detail": "Inspect-only mode will not replace the current editor map. Open the target safely through native Unreal MCP, then rerun.",
        })

    if smoke["designated_pcg_actor"] is None:
        report["pending_decisions"].append("Designate a sandbox PCG actor/component before regeneration automation is enabled.")
    if smoke["approved_camera"] is None or smoke["approved_baseline"] is None:
        report["pending_decisions"].append("Approve the Portland camera and baseline before visual comparison is enabled.")

    output = _project_path("Saved", "Automation", "stacktown_smoke.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"Stacktown smoke report: {output}")
    if report["failures"]:
        raise RuntimeError(f"Stacktown smoke found {len(report['failures'])} hard failure(s). See {output}")
    return report


if __name__ == "__main__":
    run_smoke()
