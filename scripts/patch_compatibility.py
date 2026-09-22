#!/usr/bin/env python3
"""
Patch compatibility issues between comfy_kitchen and PyTorch < 2.7.
Fixes: ValueError: infer_schema(func): Parameter stride has unsupported type list[int]
"""

import sys
import pathlib

def patch_comfy_kitchen():
    try:
        import comfy_kitchen
        ck_dir = pathlib.Path(comfy_kitchen.__file__).parent
        patched_count = 0
        for py_file in ck_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                modified = False
                if "list[int]" in content:
                    content = content.replace("list[int]", "typing.Sequence[int]")
                    modified = True
                if "list[float]" in content:
                    content = content.replace("list[float]", "typing.Sequence[float]")
                    modified = True
                if "list[bool]" in content:
                    content = content.replace("list[bool]", "typing.Sequence[bool]")
                    modified = True

                if modified:
                    if "import typing" not in content:
                        content = "import typing\n" + content
                    py_file.write_text(content, encoding="utf-8")
                    print(f"[PATCH] Patched type hints in: {py_file}")
                    patched_count += 1
            except Exception as e:
                print(f"[WARN] Could not patch {py_file}: {e}")

        print(f"[PATCH] comfy_kitchen patching complete. {patched_count} files patched.")
    except ImportError:
        print("[INFO] comfy_kitchen not installed yet, skipping comfy_kitchen patch.")

def patch_torch_infer_schema():
    try:
        import torch._library.infer_schema as s
        schema_file = pathlib.Path(s.__file__)
        content = schema_file.read_text(encoding="utf-8")
        marker = "# --- COMFY_KITCHEN_COMPAT_PATCH ---"
        if marker not in content:
            patch = f"""
{marker}
try:
    import typing
    import torch
    if "SUPPORTED_PARAM_TYPES" in globals():
        for py_type, mapped in [
            (list[int], SUPPORTED_PARAM_TYPES.get(typing.List[int], "int[]")),
            (list[float], SUPPORTED_PARAM_TYPES.get(typing.List[float], "float[]")),
            (list[bool], SUPPORTED_PARAM_TYPES.get(typing.List[bool], "bool[]")),
            (list[torch.Tensor], SUPPORTED_PARAM_TYPES.get(typing.List[torch.Tensor], "Tensor[]")),
        ]:
            SUPPORTED_PARAM_TYPES[py_type] = mapped
except Exception as _patch_err:
    pass
"""
            schema_file.write_text(content + "\n" + patch, encoding="utf-8")
            print(f"[PATCH] Successfully patched torch._library.infer_schema at {schema_file}")
        else:
            print("[INFO] torch._library.infer_schema already patched.")
    except ImportError:
        print("[INFO] torch not installed in this environment, skipping torch patch.")

def main():
    print("[INFO] Running PyTorch / ComfyUI compatibility patches...")
    patch_comfy_kitchen()
    patch_torch_infer_schema()
    print("[INFO] Compatibility patches finished.")

if __name__ == "__main__":
    main()

