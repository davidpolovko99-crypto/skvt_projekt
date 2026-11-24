"""Rebuild the whole bandit camp: level blockout, AI + NPCs, drawn routes, navmesh.

python Tools/ue_exec.py --timeout 10 -f Tools/bandit_camp/build_all.py
"""
import os
import unreal

HERE = os.path.join(unreal.Paths.project_dir(), "Tools", "bandit_camp")
for script in ("build_level.py", "build_ai.py", "build_routes.py"):
    with open(os.path.join(HERE, script), encoding="utf-8") as f:
        exec(compile(f.read(), script, "exec"), {"__name__": "__main__"})
unreal.SystemLibrary.execute_console_command(
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(), "RebuildNavigation")
