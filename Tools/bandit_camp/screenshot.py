"""Render the level from a camera into a PNG via a temporary SceneCapture2D (works with the editor in background).

Set CAM = (x, y, z, pitch, yaw), SHOT name and optionally ORTHO width before running;
defaults give the top-down overview of the whole 60x60 m map.
"""
import os
import unreal

CAM = globals().get("CAM", (0, 0, 9000, -90, 0))
SHOT = globals().get("SHOT", "BanditCamp_Top")
ORTHO = globals().get("ORTHO", 6400)
OUT_DIR = os.path.join(unreal.Paths.project_saved_dir(), "Screenshots", "BanditCamp")

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
x, y, z, pitch, yaw = CAM
cap = eas.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(x, y, z),
                                 unreal.Rotator(roll=0, pitch=pitch, yaw=yaw))
rt = unreal.RenderingLibrary.create_render_target2d(world, 1600, 1600, unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp = cap.capture_component2d
comp.set_editor_property("texture_target", rt)
comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
if ORTHO:
    comp.set_editor_property("projection_type", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    comp.set_editor_property("ortho_width", ORTHO)
else:
    comp.set_editor_property("fov_angle", 70)
# labels/routes are hidden in game; show them just for the capture
shown = [a for a in eas.get_all_level_actors()
         if str(a.get_folder_path()).startswith(("Camp/Labels", "Camp/Routes")) and a.is_hidden_ed() is False]
for a in shown:
    a.set_actor_hidden_in_game(False)
comp.capture_scene()
for a in shown:
    a.set_actor_hidden_in_game(True)
os.makedirs(OUT_DIR, exist_ok=True)
unreal.RenderingLibrary.export_render_target(world, rt, OUT_DIR, SHOT + ".png")
eas.destroy_actor(cap)
print("saved", os.path.join(OUT_DIR, SHOT + ".png"))
