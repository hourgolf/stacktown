"""Conservative, read-only Stacktown asset validation for Unreal Editor 5.8."""

from __future__ import annotations

import json
import re
from pathlib import Path

import unreal


NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def _project_path(*parts: str) -> Path:
    return Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), *parts)


def _load_config() -> dict:
    with _project_path("Config", "StacktownValidation.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def _asset_class_name(asset_data) -> str:
    class_path = getattr(asset_data, "asset_class_path", None)
    return str(getattr(class_path, "asset_name", class_path or ""))


def _message(results: dict, severity: str, code: str, asset: str, detail: str) -> None:
    results[severity].append({"code": code, "asset": asset, "detail": detail})


def _mesh_dimensions(mesh):
    try:
        bounds = mesh.get_bounds()
        extent = bounds.box_extent
        return (abs(extent.x) * 2.0, abs(extent.y) * 2.0, abs(extent.z) * 2.0), bounds.origin
    except Exception:
        try:
            box = mesh.get_bounding_box()
            size = box.max - box.min
            center = (box.max + box.min) * 0.5
            return (abs(size.x), abs(size.y), abs(size.z)), center
        except Exception:
            return None, None


def _simple_collision_count(mesh):
    try:
        body_setup = mesh.get_editor_property("body_setup")
        aggregate = body_setup.get_editor_property("agg_geom")
        fields = ("box_elems", "sphere_elems", "sphyl_elems", "convex_elems", "tapered_capsule_elems")
        return sum(len(aggregate.get_editor_property(field)) for field in fields)
    except Exception:
        return None


def _validate_static_mesh(mesh, package_name: str, config: dict, results: dict) -> None:
    limits = config["limits"]
    try:
        materials = mesh.get_editor_property("static_materials")
        if not materials:
            _message(results, "failures", "MESH_NO_MATERIAL_SLOTS", package_name, "Static mesh has no material slots.")
        for index, slot in enumerate(materials):
            if slot.get_editor_property("material_interface") is None:
                _message(results, "failures", "MESH_MISSING_MATERIAL", package_name, f"Material slot {index} is empty.")
    except Exception as exc:
        _message(results, "warnings", "MATERIAL_CHECK_UNAVAILABLE", package_name, str(exc))

    dimensions, center = _mesh_dimensions(mesh)
    if dimensions:
        smallest = min(dimensions)
        largest = max(dimensions)
        if smallest < limits["minimum_mesh_dimension_cm"] or largest > limits["maximum_mesh_dimension_cm"]:
            _message(results, "warnings", "SUSPICIOUS_DIMENSIONS", package_name, f"Bounds are {dimensions!r} cm.")
        center_distance = (center.x * center.x + center.y * center.y + center.z * center.z) ** 0.5
        if largest > 0 and center_distance > largest * limits["pivot_warning_distance_ratio"]:
            _message(results, "warnings", "PIVOT_REVIEW", package_name, f"Bounds center is {center_distance:.1f} cm from origin.")
    else:
        _message(results, "warnings", "BOUNDS_CHECK_UNAVAILABLE", package_name, "Could not query mesh bounds.")

    collision_count = _simple_collision_count(mesh)
    if collision_count == 0:
        _message(results, "warnings", "NO_SIMPLE_COLLISION", package_name, "No simple collision primitives were detected; confirm complex collision policy.")
    elif collision_count is None:
        _message(results, "warnings", "COLLISION_CHECK_UNAVAILABLE", package_name, "Could not inspect collision through the current Python API.")


def _validate_texture(texture, package_name: str, config: dict, results: dict) -> None:
    try:
        width = int(texture.blueprint_get_size_x())
        height = int(texture.blueprint_get_size_y())
        maximum = int(config["limits"]["maximum_texture_dimension"])
        if width > maximum or height > maximum:
            _message(results, "warnings", "TEXTURE_DIMENSION", package_name, f"Texture is {width}x{height}; review the {maximum}px advisory budget.")
    except Exception as exc:
        _message(results, "warnings", "TEXTURE_CHECK_UNAVAILABLE", package_name, str(exc))


def run_validation() -> dict:
    config = _load_config()
    results = {"schema_version": 1, "failures": [], "warnings": [], "info": [], "summary": {}}
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    seen = set()
    pcg_graphs = 0

    for root in config["scan_roots"]:
        if not any(root == allowed or root.startswith(allowed + "/") for allowed in config["allowed_managed_roots"]):
            _message(results, "failures", "DISALLOWED_SCAN_ROOT", root, "Configured scan root is outside managed content locations.")
            continue
        for asset_data in registry.get_assets_by_path(unreal.Name(root), recursive=True):
            package_name = str(asset_data.package_name)
            if package_name in seen:
                continue
            seen.add(package_name)
            asset_name = str(asset_data.asset_name)
            if not NAME_PATTERN.fullmatch(asset_name):
                _message(results, "failures", "INVALID_NAME", package_name, "Use letters, digits, and underscores; start with a letter.")
            class_name = _asset_class_name(asset_data)
            if "PCGGraph" in class_name:
                pcg_graphs += 1
            asset = asset_data.get_asset()
            if class_name == "StaticMesh" or isinstance(asset, unreal.StaticMesh):
                _validate_static_mesh(asset, package_name, config, results)
            elif class_name in {"Texture2D", "TextureCube", "TextureRenderTarget2D"} or isinstance(asset, unreal.Texture2D):
                _validate_texture(asset, package_name, config, results)

    if not config["metadata"]["enforce_required_tags"]:
        results["info"].append({"code": "METADATA_ADVISORY_ONLY", "detail": "No repository-wide Unreal metadata-tag convention exists yet; provenance remains documented at intake."})
    if pcg_graphs == 0:
        results["info"].append({"code": "NO_OWNED_PCG_GRAPHS", "detail": "No PCGGraph assets were found under Stacktown-owned scan roots."})

    results["summary"] = {
        "assets_scanned": len(seen),
        "pcg_graphs": pcg_graphs,
        "hard_failures": len(results["failures"]),
        "warnings": len(results["warnings"]),
    }
    output = _project_path("Saved", "Validation", "stacktown_validation.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    unreal.log(f"Stacktown validation: {results['summary']} Report: {output}")
    if results["failures"]:
        raise RuntimeError(f"Stacktown validation found {len(results['failures'])} hard failure(s). See {output}")
    return results


if __name__ == "__main__":
    run_validation()
