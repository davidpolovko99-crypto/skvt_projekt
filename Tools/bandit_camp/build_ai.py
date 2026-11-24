"""Bandit AI assets + NPC placement for L_BanditCamp (Úkol 3, sekce 5: hlídky, vidění, statické postavy).

Run after build_level.py:  python Tools/ue_exec.py -f Tools/bandit_camp/build_ai.py
Graphs (task logic, BT nodes, BT asset pin in the AI controller) can't be edited from Python in UE 5.5;
see Tools/bandit_camp/README.md for the few manual steps.
"""
import math
import unreal

AI = "/Game/Skvt/BanditCamp/AI"
NPC = "/Game/Skvt/Characters/NPC/BehaviorTrees"
MI = "/Game/Skvt/Characters/Materials/Instances/Manny"

eal = unreal.EditorAssetLibrary
bel = unreal.BlueprintEditorLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()


def bp_child(name, parent_class):
    path = f"{AI}/{name}"
    if eal.does_asset_exist(path):
        return unreal.load_asset(path)
    f = unreal.BlueprintFactory()
    f.set_editor_property("parent_class", parent_class)
    return tools.create_asset(name, AI, unreal.Blueprint, f)


def has_var(bp, name):
    try:
        unreal.get_default_object(bp.generated_class()).get_editor_property(name)
        return True
    except Exception:
        return False


def add_var(bp, name, pin_type, editable=True):
    if has_var(bp, name):
        return
    bel.add_member_variable(bp, name, pin_type)
    if editable:
        bel.set_blueprint_variable_instance_editable(bp, name, True)


def add_component(bp, comp_class, name):
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h))
        if o and o.get_class() == comp_class.static_class():
            return
    params = unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=comp_class, blueprint_context=bp)
    new_handle, fail = sds.add_new_subobject(params)
    sds.rename_subobject(new_handle, name)


def component_template(bp, comp_class):
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h))
        if o and o.get_class() == comp_class.static_class():
            return o
    return None


# ---------------------------------------------------------------- blackboard
bb_path = f"{AI}/BB_Bandit"
if not eal.does_asset_exist(bb_path):
    eal.duplicate_asset(f"{NPC}/BB_BT_NPCBase", bb_path)
bb = unreal.load_asset(bb_path)
keys = list(bb.get_editor_property("keys"))
if "PatrolTarget" not in [str(k.get_editor_property("entry_name")) for k in keys]:
    kt = unreal.new_object(keys[0].get_editor_property("key_type").get_class(), outer=bb)  # SelfActor = Object key
    e = unreal.BlackboardEntry()
    e.set_editor_property("entry_name", "PatrolTarget")
    e.set_editor_property("key_type", kt)
    keys.append(e)
    bb.set_editor_property("keys", keys)
eal.save_loaded_asset(bb)

# ---------------------------------------------------------------- BT task: vyber další Target Point z pole
task = bp_child("BTTask_NextPatrolPoint", unreal.BTTask_BlueprintBase)
add_var(task, "PatrolTargetKey", bel.get_struct_type(unreal.BlackboardKeySelector.static_struct()))
add_var(task, "PatrolIndex", bel.get_basic_type_by_name("int"), editable=False)
bel.compile_blueprint(task)
eal.save_loaded_asset(task)

# ---------------------------------------------------------------- behavior tree asset (nodes: README)
bt_path = f"{AI}/BT_BanditPatrol"
if not eal.does_asset_exist(bt_path):
    tools.create_asset("BT_BanditPatrol", AI, unreal.BehaviorTree, unreal.BehaviorTreeFactory())
bt = unreal.load_asset(bt_path)
# Blackboard (BB_Bandit) se nastavuje na Root uzlu v BT editoru - z Pythonu nejde.
eal.save_loaded_asset(bt)

# ---------------------------------------------------------------- AI controller (copy of lesson-15 one)
aic_path = f"{AI}/AIC_BanditPatrol"
if not eal.does_asset_exist(aic_path):
    eal.duplicate_asset(f"{NPC}/AIC_BT_NPCBase", aic_path)
aic = unreal.load_asset(aic_path)

# ---------------------------------------------------------------- pawns
base = unreal.load_asset(f"{NPC}/BP_NPC_BT_base").generated_class()

bandit = bp_child("BP_Bandit", base)
add_var(bandit, "PatrolPoints", bel.get_array_type(bel.get_object_reference_type(unreal.Actor)))
add_component(bandit, unreal.PawnSensingComponent, "PawnSensing")
bel.compile_blueprint(bandit)
ps = component_template(bandit, unreal.PawnSensingComponent)
ps.set_editor_property("sight_radius", 1500.0)
ps.set_editor_property("peripheral_vision_angle", 60.0)
cdo = unreal.get_default_object(bandit.generated_class())
cdo.set_editor_property("auto_possess_ai", unreal.AutoPossessAI.DISABLED)  # statické postavy bez AI
eal.save_loaded_asset(bandit)

patrol = bp_child("BP_BanditPatrol", bandit.generated_class())
bel.compile_blueprint(patrol)
cdo = unreal.get_default_object(patrol.generated_class())
cdo.set_editor_property("auto_possess_ai", unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
cdo.set_editor_property("ai_controller_class", aic.generated_class())
cdo.get_editor_property("character_movement").set_editor_property("max_walk_speed", 200.0)
eal.save_loaded_asset(patrol)

guard = bp_child("BP_BanditGuard", bandit.generated_class())
add_component(guard, unreal.RotatingMovementComponent, "OtaceniPohledu")
bel.compile_blueprint(guard)
rm = component_template(guard, unreal.RotatingMovementComponent)
rm.set_editor_property("rotation_rate", unreal.Rotator(roll=0, pitch=0, yaw=90.0 / 8.0))  # 90° za 8 s
eal.save_loaded_asset(guard)

# ---------------------------------------------------------------- placement in the level
for a in eas.get_all_level_actors():
    if str(a.get_folder_path()).startswith("Camp/AI"):
        eas.destroy_actor(a)


def target_points(prefix, pts):
    out = []
    for i, (x, y) in enumerate(pts, 1):
        tp = eas.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(x, y, 50))
        tp.set_actor_label(f"TP_{prefix}_{i}")
        tp.set_folder_path(f"Camp/AI/{prefix}")
        out.append(tp)
    return out


def bandit_actor(bp, label, loc, yaw, color, folder="Camp/AI/Bandits"):
    a = eas.spawn_actor_from_class(bp.generated_class(), unreal.Vector(*loc), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    a.set_actor_label(label)
    a.set_folder_path(folder)
    mesh = a.get_editor_property("mesh")
    mesh.set_material(0, unreal.load_asset(f"{MI}/MI_Manny_01_{color}"))
    mesh.set_material(1, unreal.load_asset(f"{MI}/MI_Manny_02_{color}"))
    return a


def face(frm, to):
    return math.degrees(math.atan2(to[1] - frm[1], to[0] - frm[0]))


FIRE = (250, 0)
# Pochůzkář: 6 bodů po vnějším okruhu (skála, houští, JZ, posed, potok jih, potok sever)
p_pts = target_points("Pochuzkar", [(1600, -1650), (-400, -1650), (-1500, -1100), (-1150, 450),
                                    (-600, 1800), (1350, 1750)])
# Nováček: kratší okruh potok - oheň - dřevo
n_pts = target_points("Novacek", [(-150, 1850), (150, 300), (-50, -1250)])

pochuzkar = bandit_actor(patrol, "Bandita_Pochuzkar", (1600, -1650, 100), 180, "Blue")
pochuzkar.set_editor_property("PatrolPoints", p_pts)
novacek = bandit_actor(patrol, "Bandita_Novacek", (-150, 1850, 100), -90, "Purple")
novacek.set_editor_property("PatrolPoints", n_pts)
novacek.get_editor_property("character_movement").set_editor_property("max_walk_speed", 150.0)  # okruh ~60 s

# statické postavy na místě polední aktivity
kapo_loc = (250, -280, 100)
bandit_actor(bandit, "Bandita_Kapo_Reznik", kapo_loc, face(kapo_loc, FIRE), "Red")
kuchar_loc = (470, 180, 100)
bandit_actor(bandit, "Bandita_Kuchar", kuchar_loc, face(kuchar_loc, FIRE), "Green")
bandit_actor(guard, "Bandita_Strazny_Posed", (-1400, 700, 400), 180, "Yellow")

unreal.EditorLoadingAndSavingUtils.save_current_level()
print("AI ready:", [a.get_actor_label() for a in eas.get_all_level_actors()
                    if str(a.get_folder_path()).startswith("Camp/AI/Bandits")])
