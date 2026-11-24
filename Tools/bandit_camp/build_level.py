"""Greybox blockout of 'Tábor Pod Vraní skálou' (Úkol 3).

Run inside the editor:  python Tools/ue_exec.py -f Tools/bandit_camp/build_level.py
Axes: +X = sever, +Y = východ, Z nahoru, 1 m = 100 UU. Tábor ~4000x4000 kolem (0,0).
Re-running rebuilds everything inside the level (actors in folder "Camp").
"""
import math
import unreal

ROOT = "/Game/Skvt/BanditCamp"
LEVEL = ROOT + "/L_BanditCamp"
MAT_DIR = ROOT + "/Materials"

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assets = unreal.AssetToolsHelpers.get_asset_tools()

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
CYL = unreal.load_asset("/Engine/BasicShapes/Cylinder")
CONE = unreal.load_asset("/Engine/BasicShapes/Cone")
SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere")

# ---------------------------------------------------------------- materials
COLORS = {
    "Ground": (0.16, 0.22, 0.08),
    "Clearing": (0.30, 0.22, 0.12),
    "Road": (0.42, 0.32, 0.18),
    "Rock": (0.25, 0.25, 0.27),
    "Water": (0.05, 0.25, 0.6),
    "Bush": (0.04, 0.16, 0.03),
    "Wood": (0.28, 0.15, 0.06),
    "Canvas": (0.62, 0.55, 0.38),
    "BossCanvas": (0.45, 0.12, 0.08),
    "Trap": (1.0, 0.0, 0.0),
    "Rope": (0.9, 0.75, 0.2),
    "Metal": (0.08, 0.08, 0.09),
    "Fire": (1.0, 0.35, 0.0),
    "Loot": (0.9, 0.7, 0.05),
    "Horse": (0.35, 0.2, 0.1),
    "Canopy": (0.06, 0.3, 0.06),
}


def material(name):
    path = f"{MAT_DIR}/MI_Camp_{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)
    mi = assets.create_asset(f"MI_Camp_{name}", MAT_DIR, unreal.MaterialInstanceConstant,
                             unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(
        mi, unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial"))
    r, g, b = COLORS[name]
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        mi, "Color", unreal.LinearColor(r, g, b, 1.0))
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return mi


MATS = {k: material(k) for k in COLORS}

# ---------------------------------------------------------------- level
if not unreal.EditorAssetLibrary.does_asset_exist(LEVEL):
    les.new_level(LEVEL)
elif unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name().split(".")[0] != LEVEL:
    les.load_level(LEVEL)

for a in eas.get_all_level_actors():
    if str(a.get_folder_path()).startswith("Camp"):
        eas.destroy_actor(a)


def _place(mesh, name, loc, scale, rot, mat, folder, collide):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc),
                                   unreal.Rotator(roll=rot[0], pitch=rot[1], yaw=rot[2]))
    a.set_actor_label(name)
    a.set_folder_path(f"Camp/{folder}")
    a.set_actor_scale3d(unreal.Vector(*scale))
    smc = a.static_mesh_component
    smc.set_static_mesh(mesh)
    smc.set_material(0, MATS[mat])
    if not collide:
        smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        smc.set_editor_property("can_ever_affect_navigation", False)
    return a


def box(name, center, size, mat, folder, rot=(0, 0, 0), collide=True):
    """center = (x, y, z) of the box centre, size in UU; rot = (roll, pitch, yaw)."""
    return _place(CUBE, name, center, [s / 100.0 for s in size], rot, mat, folder, collide)


def floor_box(name, x0, x1, y0, y1, z0, z1, mat, folder, collide=True):
    return box(name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), mat, folder,
               collide=collide)


def cyl(name, x, y, z0, radius, height, mat, folder, rot=(0, 0, 0), collide=True):
    return _place(CYL, name, (x, y, z0 + height / 2), (radius / 50.0, radius / 50.0, height / 100.0),
                  rot, mat, folder, collide)


def label(text, x, y, z=700, size=90, color=unreal.Color(255, 255, 255, 255)):
    t = eas.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(x, y, z), unreal.Rotator(0, 90, 0))
    # pitch 90 -> text faces up, readable from the Top view (north = up on screen)
    t.set_actor_label("Lbl_" + text.split(" ")[0])
    t.set_folder_path("Camp/Labels")
    t.set_actor_rotation(unreal.Rotator(roll=0, pitch=90, yaw=180), False)
    tr = t.text_render
    tr.set_editor_property("text", text)
    tr.set_editor_property("world_size", size)
    tr.set_editor_property("horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER)
    tr.set_editor_property("vertical_alignment", unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    tr.set_editor_property("text_render_color", color)
    t.set_actor_hidden_in_game(True)
    return t


def slab_x(name, x0, x1, z0, z1, yc, width, mat, folder, th=700):
    """Ramp rising along X from (x0, z0) to (x1, z1); a thick tilted box so its underside stays buried."""
    a = math.atan2(z1 - z0, x1 - x0)
    up = (-math.sin(a), math.cos(a))
    c = ((x0 + x1) / 2 - up[0] * th / 2, yc, (z0 + z1) / 2 - up[1] * th / 2)
    return box(name, c, (math.hypot(x1 - x0, z1 - z0) + 40, width, th), mat, folder, rot=(0, math.degrees(a), 0))


def slab_y(name, y0, y1, z0, z1, xc, width, mat, folder, th=700):
    """Ramp along Y from (y0, z0) to (y1, z1)."""
    r = -math.atan2(z1 - z0, y1 - y0)
    up = (math.sin(r), math.cos(r))
    c = (xc, (y0 + y1) / 2 - up[0] * th / 2, (z0 + z1) / 2 - up[1] * th / 2)
    return box(name, c, (width, math.hypot(y1 - y0, z1 - z0) + 40, th), mat, folder, rot=(math.degrees(r), 0, 0))


def tent_solid(name, cx, cy, length, width, mat, folder="Tents"):
    """Regular tent: one cube turned 45 deg about its length axis -> roof profile, height = width/2."""
    a = width / math.sqrt(2)
    return box(name, (cx, cy, 0), (length, a, a), mat, folder, rot=(45, 0, 0))


# ---------------------------------------------------------------- terrain
floor_box("Ground_Main", -3000, 3000, -3000, 2000, -200, 0, "Ground", "Terrain")
floor_box("Creek_Bed", -3000, 3000, 2000, 2600, -220, -120, "Rock", "Terrain")
floor_box("Ground_EastBank", -3000, 3000, 2600, 3000, -200, 0, "Ground", "Terrain")
floor_box("Creek_Water", -3000, 3000, 2010, 2590, -120, -105, "Water", "Terrain", collide=False)
floor_box("Camp_Clearing", -1800, 1800, -1750, 1950, 0, 1, "Clearing", "Terrain", collide=False)
floor_box("Forest_Road", -3000, -1800, 100, 500, 0, 2, "Road", "Terrain", collide=False)

# Vraní skála (sever) + převis nad kápovým stanem
floor_box("VraniSkala", 1800, 3000, -3000, 2000, 0, 600, "Rock", "Rock")
floor_box("VraniSkala_Previs", 1650, 1800, 380, 700, 540, 600, "Rock", "Rock")
for i, (x, y, s) in enumerate([(1760, -2200, 220), (1740, -900, 160), (1770, 900, 200), (1760, 1700, 180)]):
    box(f"Rock_Chunk_{i}", (x, y, s / 2), (s, s * 1.3, s), "Rock", "Rock", rot=(0, 0, 17 * i))

# Vyhlídka (skalka) na jihozápadě + rampa z cesty + hřeben na Vraní skálu + sestup do houští
floor_box("Vyhlidka_Skalka", -2500, -2000, -2900, -2400, 0, 300, "Rock", "Rock")
slab_x("Vyhlidka_Ramp", -3000, -2500, 0, 300, -2650, 300, "Rock", "Rock")
slab_x("Hreben_Ramp", -2000, 1800, 300, 600, -2700, 300, "Rock", "Rock")
slab_y("Vyhlidka_SestupDoHousti", -2400, -1950, 300, 0, -2150, 200, "Rock", "Rock")

# ---------------------------------------------------------------- houští + kozí stezka + plechovky
# west hedge Y -2450..-2170, goat path Y -2170..-2050, east hedge Y -2050..-1800 (gap X 0..200 = exit)
x = -1700
i = 0
while x < 1800:
    w = 260 if i % 3 else 200
    h = 220 + (i * 37) % 80
    box(f"Bush_W_{i}", (x + w / 2, -2310, h / 2), (w + 20, 280, h), "Bush", "Thicket")
    if x + w <= 0 or x >= 200:
        box(f"Bush_E_{i}", (x + w / 2, -1925, h / 2), (w + 20, 250, h), "Bush", "Thicket")
    x += w
    i += 1
floor_box("Bush_N_Cap", 1400, 1800, -2170, -2050, 0, 240, "Bush", "Thicket")
for i, x in enumerate([-1300, -650, 600]):
    cyl(f"Bush_Round_{i}", x, -1700, 0, 90, 170, "Bush", "Thicket")
for j, tx in enumerate([-900, -200]):
    floor_box(f"Trap_String_{j}", tx - 2, tx + 2, -2170, -2050, 25, 29, "Trap", "Traps", collide=False)
    for k, ty in enumerate([-2150, -2110, -2070]):
        floor_box(f"Trap_Can_{j}_{k}", tx - 8, tx + 8, ty - 8, ty + 8, 10, 35, "Trap", "Traps", collide=False)

# ---------------------------------------------------------------- kápův stan (dutý, 2x větší)
KX0, KX1, KW, KH = 850, 1450, 800, 400
KL = KX1 - KX0
slope = KH * math.sqrt(2)
kcx = (KX0 + KX1) / 2
box("KapoStan_PanelWest", (kcx, -KW / 4, KH / 2), (KL, slope, 10), "BossCanvas", "Tents", rot=(-45, 0, 0))
# východní stěna má mezeru = boční vchod (X 1080..1220)
box("KapoStan_PanelEast_S", (KX0 + 115, KW / 4, KH / 2), (230, slope, 10), "BossCanvas", "Tents", rot=(45, 0, 0))
box("KapoStan_PanelEast_N", (KX1 - 115, KW / 4, KH / 2), (230, slope, 10), "BossCanvas", "Tents", rot=(45, 0, 0))
box("KapoStan_BackWall", (KX1, 0, 0), (10, slope, slope), "BossCanvas", "Tents", rot=(45, 0, 0))
floor_box("KapoStan_BackWall_CutHere", KX1 + 6, KX1 + 10, -60, 60, 20, 200, "Trap", "Tents", collide=False)
floor_box("KapoStan_Truhla", 1300, 1400, -260, -120, 0, 80, "Loot", "Tents")
floor_box("KapoStan_Bedroll", 950, 1150, 120, 300, 0, 15, "Canvas", "Tents")

# lano + schované schody za stanem (X 1600..1800, stoupají podél skály na západ->východ)
cyl("Lano", 1700, 450, 0, 4, 540, "Rope", "Rope", collide=False)
steps = 12
for s in range(steps):
    y0 = -350 + s * 60
    floor_box(f"Lano_Schod_{s:02d}", 1620, 1800, y0, y0 + 60, 0, (s + 1) * 50, "Rock", "Rope")

# ---------------------------------------------------------------- běžné stany
tent_solid("Stan_1", 1150, -1250, 400, 360, "Canvas")
tent_solid("Stan_2", 550, -1250, 400, 360, "Canvas")
box("Stan_Bedroll", (850, -1250, 7), (180, 70, 14), "Canvas", "Tents")

# ---------------------------------------------------------------- ohniště, plachta, kostky
cyl("Ohniste", 250, 0, 0, 100, 25, "Rock", "Fire")
cyl("Ohniste_Plamen", 250, 0, 25, 50, 50, "Fire", "Fire", collide=False)
for i in range(4):
    a = math.radians(45 + 90 * i)
    box(f"Ohniste_Lavice_{i}", (250 + 260 * math.cos(a), 260 * math.sin(a), 22), (220, 45, 45), "Wood", "Fire",
        rot=(0, 0, 45 + 90 * i + 90))
cyl("Rozen_Kul_A", 250, -110, 0, 5, 140, "Wood", "Fire")
cyl("Rozen_Kul_B", 250, 110, 0, 5, 140, "Wood", "Fire")
box("Rozen_Tyc", (250, 0, 135), (6, 230, 6), "Wood", "Fire", collide=False)
cyl("Kotlik", 330, 60, 25, 30, 35, "Metal", "Fire", collide=False)
cyl("Sud_Kostky", 0, 260, 0, 40, 90, "Wood", "Fire")
# plachta (úkryt při dešti)
for i, (px, py) in enumerate([(200, -350), (600, -350), (200, -750), (600, -750)]):
    cyl(f"Plachta_Kul_{i}", px, py, 0, 6, 250, "Wood", "Fire")
box("Plachta", (400, -550, 250), (440, 440, 6), "Canvas", "Fire", rot=(0, 3, 0))
# sušení masa
cyl("Suseni_Kul_A", -150, -500, 0, 5, 180, "Wood", "Fire")
cyl("Suseni_Kul_B", -150, -200, 0, 5, 180, "Wood", "Fire")
box("Suseni_Tyc", (-150, -350, 175), (6, 300, 6), "Wood", "Fire", collide=False)
for i in range(4):
    box(f"Suseni_Maso_{i}", (-150, -460 + 70 * i, 140), (10, 30, 60), "Horse", "Fire", collide=False)
# brousek u stanu
cyl("Brousek", 600, -850, 0, 35, 60, "Rock", "Fire", rot=(90, 0, 0))

# ---------------------------------------------------------------- hromada dřeva + špalek
box("Hromada_Dreva", (150, -1560, 60), (340, 130, 120), "Wood", "Wood")
cyl("Spalek", -50, -1400, 0, 40, 55, "Wood", "Wood")
box("Sekera", (-50, -1400, 75), (8, 60, 25), "Metal", "Wood", rot=(0, 0, 30), collide=False)

# ---------------------------------------------------------------- vůz s kořistí + kůň
floor_box("Vuz_Korba", 950, 1350, 940, 1160, 80, 180, "Wood", "Wagon")
for i, (wx, wy) in enumerate([(1020, 925), (1280, 925), (1020, 1175), (1280, 1175)]):
    cyl(f"Vuz_Kolo_{i}", wx, wy, 45 - 15, 45, 30, "Wood", "Wagon", rot=(90, 0, 0))
floor_box("Vuz_Truhla_Korist", 1000, 1120, 970, 1080, 180, 260, "Loot", "Wagon")
floor_box("Vuz_Pytle", 1160, 1320, 980, 1130, 180, 240, "Canvas", "Wagon")
box("Vuz_Oj", (800, 1050, 90), (300, 10, 10), "Wood", "Wagon", collide=False)
floor_box("Kun_Telo", 1080, 1320, 1460, 1540, 110, 190, "Horse", "Wagon")
floor_box("Kun_Krk", 1290, 1360, 1470, 1530, 170, 260, "Horse", "Wagon")
for i, (hx, hy) in enumerate([(1100, 1470), (1100, 1530), (1300, 1470), (1300, 1530)]):
    floor_box(f"Kun_Noha_{i}", hx - 10, hx + 10, hy - 10, hy + 10, 0, 110, "Horse", "Wagon")
floor_box("Kun_Korito", 1400, 1460, 1420, 1580, 0, 60, "Wood", "Wagon")
cyl("Kun_Kul", 1380, 1650, 0, 8, 150, "Wood", "Wagon")

# ---------------------------------------------------------------- potok: křoví, rybaření, mytí
for i, (bx, by) in enumerate([(650, 1880), (820, 1900), (1000, 1870), (1180, 1910), (1400, 1880), (1600, 1900),
                              (-1300, 1900), (-1100, 1880)]):
    cyl(f"Krovi_Potok_{i}", bx, by, 0, 85, 150, "Bush", "Creek")
cyl("Ryby_Stolicka", -600, 1930, 0, 25, 45, "Wood", "Creek")
box("Ryby_Prut", (-600, 2150, 120), (5, 420, 5), "Wood", "Creek", rot=(25, 0, 0), collide=False)
cyl("Ryby_Kos", -500, 1900, 0, 25, 40, "Canvas", "Creek")
floor_box("Myti_Kamen", 250, 380, 2050, 2200, -120, -90, "Rock", "Creek")
cyl("Vedro_Voda", 100, 1920, 0, 20, 40, "Metal", "Creek")

# ---------------------------------------------------------------- posed + zvon u jižní cesty
PX, PY, PH = -1400, 700, 300
for i, (dx, dy) in enumerate([(-90, -90), (90, -90), (-90, 90), (90, 90)]):
    cyl(f"Posed_Noha_{i}", PX + dx, PY + dy, 0, 8, PH + 110, "Wood", "Posed")
floor_box("Posed_Plosina", PX - 100, PX + 100, PY - 100, PY + 100, PH - 15, PH, "Wood", "Posed")
floor_box("Posed_Zabradli_S", PX - 100, PX - 95, PY - 100, PY + 100, PH, PH + 100, "Wood", "Posed")
floor_box("Posed_Zabradli_W", PX - 100, PX + 100, PY - 100, PY - 95, PH, PH + 100, "Wood", "Posed")
floor_box("Posed_Zabradli_E", PX - 100, PX + 100, PY + 95, PY + 100, PH, PH + 100, "Wood", "Posed")
floor_box("Posed_Strecha", PX - 120, PX + 120, PY - 120, PY + 120, PH + 230, PH + 240, "Wood", "Posed")
for r in range(6):
    floor_box(f"Posed_Zebrik_{r}", PX + 100, PX + 106, PY - 30, PY + 30, 40 + r * 50, 46 + r * 50, "Wood", "Posed")
cyl("Posed_Zvon", PX + 85, PY + 85, PH + 140, 15, 30, "Loot", "Posed", collide=False)

# ---------------------------------------------------------------- les kolem tábora
trees = [(-2600, 1200), (-2300, 1700), (-2700, 2300), (-2200, -900), (-2700, -600), (-2500, -1400),
         (-1900, 1500), (-2100, 900), (-2800, 800), (-2000, -300), (2200, 2800), (1200, 2850), (100, 2800),
         (-900, 2850), (-2000, 2800), (2800, 2800), (-1700, -2900), (-900, -2900), (300, -2900),
         (1300, -2900), (-2800, -2000), (-1900, 2200)]
for i, (tx, ty) in enumerate(trees):
    cyl(f"Strom_Kmen_{i}", tx, ty, 0, 30, 450, "Wood", "Forest")
    _place(CONE, f"Strom_Koruna_{i}", (tx, ty, 650), (3.2, 3.2, 5.0), (0, 0, 0), "Canopy", "Forest", True)

# ---------------------------------------------------------------- popisky pro screenshot shora
label("VRANI SKALA (6 m)", 2400, -500, 800, 140)
label("Kapuv stan", 1150, 0, 700)
label("truhla", 1350, -190, 650, 50)
label("lano / schody", 1700, 0, 900, 60)
label("Ohniste", 250, 0, 650)
label("plachta", 400, -550, 650, 60)
label("Stany", 850, -1250, 650)
label("Hromada dreva", 150, -1560, 650, 70)
label("Vuz s koristi + kun", 1150, 1250, 650, 70)
label("POTOK", 0, 2300, 650, 120)
label("myti kapa 13-14", 300, 2120, 650, 50)
label("rybareni", -600, 2000, 650, 50)
label("Posed + zvon", -1400, 700, 900, 70)
label("HOUSTI", -1000, -2310, 650, 120)
label("kozi stezka", 500, -2110, 650, 50)
label("plechovky", -900, -2110, 700, 50, unreal.Color(255, 60, 60, 255))
label("plechovky", -200, -2110, 700, 50, unreal.Color(255, 60, 60, 255))
label("Vyhlidka", -2250, -2650, 800, 80)
label("Hreben", -100, -2700, 900, 70)
label("Lesni cesta (JIH)", -2500, 300, 650, 70)

# ---------------------------------------------------------------- světlo, navmesh, start
def ensure(cls, label_, loc, rot=(0, 0, 0)):
    a = eas.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(*rot))
    a.set_actor_label(label_)
    a.set_folder_path("Camp/Setup")
    return a


sun = ensure(unreal.DirectionalLight, "Sun", (0, 0, 2000), (0, -50, 30))
sun.light_component.set_editor_property("atmosphere_sun_light", True)
sun.light_component.set_editor_property("intensity", 8.0)
ensure(unreal.SkyAtmosphere, "SkyAtmosphere", (0, 0, 0))
sky = ensure(unreal.SkyLight, "SkyLight", (0, 0, 500))
sky.light_component.set_editor_property("real_time_capture", True)
sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
ensure(unreal.ExponentialHeightFog, "Fog", (0, 0, 0))
ensure(unreal.PostProcessVolume, "PostProcess", (0, 0, 0)).set_editor_property("unbound", True)

nav = eas.spawn_actor_from_object(unreal.NavMeshBoundsVolume.static_class(), unreal.Vector(0, 0, 300))
nav.set_actor_label("NavMeshBounds")
nav.set_folder_path("Camp/Setup")
nav.set_actor_scale3d(unreal.Vector(31, 31, 10))  # brush 200 UU -> 6200 x 6200 x 2000

ensure(unreal.PlayerStart, "PlayerStart_LesniCesta", (-2850, 0, 100), (0, 0, 60))

unreal.EditorLoadingAndSavingUtils.save_current_level()
print("Bandit camp built:", len([a for a in eas.get_all_level_actors()
                                  if str(a.get_folder_path()).startswith("Camp")]), "actors")
