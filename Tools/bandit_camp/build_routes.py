"""Draw stealth routes into L_BanditCamp as flat coloured strips (editor only, no collision, hidden in game).

Červená = varianta A (měšec u kápa, mytí v potoce 13-14), modrá = varianta B (truhla ve stanu, oběd 12-13).
Světlejší odstín = alternativní cesta dané varianty.
"""
import math
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
MAT_DIR = "/Game/Skvt/BanditCamp/Materials"
COLORS = {"RouteA": (1.0, 0.0, 0.0), "RouteA_Alt": (1.0, 0.45, 0.45),
          "RouteB": (0.0, 0.25, 1.0), "RouteB_Alt": (0.4, 0.75, 1.0),
          "PatrolLoop": (1.0, 0.85, 0.0), "NovacekLoop": (0.75, 0.2, 1.0)}


def unlit_parent():
    """Unlit colour material so the routes stay readable in shadow (e.g. inside the goat path)."""
    path = f"{MAT_DIR}/M_Camp_Unlit"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)
    mel = unreal.MaterialEditingLibrary
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_Camp_Unlit", MAT_DIR, unreal.Material,
                                                                unreal.MaterialFactoryNew())
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    col = mel.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -300, 0)
    col.set_editor_property("parameter_name", "Color")
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m


def material(name):
    path = f"{MAT_DIR}/MI_Route_{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)
    mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        f"MI_Route_{name}", MAT_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, unlit_parent())
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        mi, "Color", unreal.LinearColor(*COLORS[name], 1.0))
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return mi


for a in eas.get_all_level_actors():
    if str(a.get_folder_path()).startswith("Camp/Routes"):
        eas.destroy_actor(a)


def route(name, pts, mat, width=45, lift=12):
    m = material(mat)
    for i in range(len(pts) - 1):
        a, b = unreal.Vector(*pts[i]), unreal.Vector(*pts[i + 1])
        d = b - a
        horiz = math.hypot(d.x, d.y)
        yaw = math.degrees(math.atan2(d.y, d.x))
        pitch = math.degrees(math.atan2(d.z, horiz))
        mid = (a + b) * 0.5 + unreal.Vector(0, 0, lift)
        seg = eas.spawn_actor_from_class(unreal.StaticMeshActor, mid, unreal.Rotator(roll=0, pitch=pitch, yaw=yaw))
        seg.set_actor_label(f"{name}_{i:02d}")
        seg.set_folder_path(f"Camp/Routes/{name}")
        seg.set_actor_scale3d(unreal.Vector((d.length() + width) / 100.0, width / 100.0, 0.05))
        smc = seg.static_mesh_component
        smc.set_static_mesh(CUBE)
        smc.set_material(0, m)
        smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        smc.set_editor_property("can_ever_affect_navigation", False)
        smc.set_editor_property("cast_shadow", False)
        seg.set_actor_hidden_in_game(True)


# společný začátek: lesní cesta -> rampa na vyhlídku
START = [(-2850, 0, 0), (-2950, -650, 0), (-3000, -2650, 0), (-2500, -2650, 300), (-2250, -2650, 300)]

# A: vyhlídka -> sestup do houští -> kozí stezka (plechovky) -> za hromadu dřeva -> za stany ->
#    za kápův stan -> za vůz/koně -> křoví u potoka -> kapsaření při mytí -> únik korytem na sever
route("A_Hlavni", START + [
    (-2150, -2400, 300), (-2150, -1950, 0), (-1750, -2110, 0), (100, -2110, 0), (100, -1800, 0),
    (250, -1680, 0), (800, -1620, 0), (1520, -1560, 0), (1530, -900, 0), (1530, 0, 0), (1520, 700, 0),
    (1450, 1300, 0), (1100, 1780, 0), (500, 1960, 0), (350, 2080, -110), (900, 2350, -110), (2950, 2350, -110)],
    "RouteA")
# A alt: 14-16 kápo spí -> přes skálu (jako B) a měšec vzít spícímu ve stanu
route("A_Alt", [(1530, 0, 0), (1360, 0, 0), (1050, 200, 0)], "RouteA_Alt", width=30)

# B: vyhlídka -> hřeben Vraní skály -> po skále nad stan -> lano/schody za stan -> prořízne zadní stěnu ->
#    truhla (oběd 12-13) -> zpět po laně
route("B_Hlavni", START + [
    (-2000, -2700, 300), (1800, -2700, 600), (2050, -2600, 600), (2050, 340, 600), (1700, 340, 600),
    (1700, -330, 0), (1530, -200, 0), (1460, 0, 0), (1350, -150, 0)], "RouteB", lift=20)
# B alt: od jihovýchodu korytem potoka -> kryt za vozem -> boční vchod stanu (pozor na posed)
route("B_Alt", [(-2850, 0, 0), (-2700, 1500, 0), (-2900, 2300, -110), (900, 2300, -110), (1000, 2000, 0),
                (1150, 1250, 0), (1150, 750, 0), (1150, 420, 0), (1300, 0, 0)], "RouteB_Alt", width=30, lift=20)

# hlídky (podle Target Pointů): žlutě pochůzkář ~90 s, fialově nováček ~60 s
tps = {a.get_actor_label(): a.get_actor_location() for a in eas.get_all_level_actors()
       if a.get_actor_label().startswith("TP_")}
for who, mat, n in [("Pochuzkar", "PatrolLoop", 6), ("Novacek", "NovacekLoop", 3)]:
    pts = [tps[f"TP_{who}_{i}"] for i in range(1, n + 1)]
    pts = [(p.x, p.y, 0) for p in pts + pts[:1]]
    route(f"Hlidka_{who}", pts, mat, width=20, lift=4)

unreal.EditorLoadingAndSavingUtils.save_current_level()
print("routes drawn")
