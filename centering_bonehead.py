import bpy
from bpy.types import Panel, Operator
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatVectorProperty,
    StringProperty
)
import bmesh
from mathutils import Matrix, Vector


bl_info = {
    "name": "centering bonehead",
    "author": "Kageji",
    "version": (0, 0, 1),
    "blender": (4, 2, 0),
    "location": "3D View > Sidebar",
    "description": "centering bonehead",
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "https://github.com/kioshiki3d/centering_bonehead/",
    "tracker_url": "https://twitter.com/shadow003min",
    "category": "Object",
}


class KJ_CBH_Panel(Panel):
    bl_label = "centering bonehead"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "kjtools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mode = context.mode
        layout.label(text="simple centering bonehead")
        simple_btn = layout.row(align=True)
        simple_enble = False
        if mode == "EDIT_MESH":
            simple_enble = True
        simple_btn.enabled = simple_enble
        simple_btn.operator(KJ_CenteringBoneHead.bl_idname, text="Centering").slot = 0

        layout.label(text="advance centering bonehead")
        advance_btn = layout.row(align=True)
        advance_enble = False
        adv_btn_text = "Get Center"
        slot = 1
        if mode == "EDIT_MESH":
            advance_enble = True
        if (mode == "EDIT_ARMATURE") and scene.kjcbhCenterFlag:
            advance_enble = True
            slot = 2
            adv_btn_text = "Move Bone"
        advance_btn.enabled = advance_enble
        advance_btn.operator(KJ_CenteringBoneHead.bl_idname, text=adv_btn_text).slot = slot


class KJ_CenteringBoneHead(Operator):
    bl_idname = "kjcenteringbonehead.operator"
    bl_label = "set_centering_bonehead"
    bl_description = "Set Centering Bonehead"

    slot: IntProperty(name="operation Slot", default=0, min=0, max=2)

    def execute(self, context):
        scene = context.scene
        mesh_obj = context.active_object

        if self.slot in (0, 1):
            armature_obj = mesh_obj.parent  # メッシュの親であるアーマチュア
            if armature_obj is None:
                self.report({"ERROR"}, "No armature parent found!")
                return {"CANCELLED"}

            # メッシュの編集モードで選択された頂点を取得
            bm = bmesh.from_edit_mesh(mesh_obj.data)
            selected_verts = [v for v in bm.verts if v.select]
            if not selected_verts:
                self.report({"ERROR"}, "No vertices selected!")
                return {"CANCELLED"}

            scene.kjcbhCenterMmeshObj = mesh_obj.name

            # 選択された頂点の平均位置を計算
            avg_pos = Vector((0, 0, 0))
            for vert in selected_verts:
                avg_pos += vert.co
            avg_pos /= len(selected_verts)
            # メッシュのワールド座標に変換
            world_pos = mesh_obj.matrix_world @ avg_pos
            scene.kjcbhCenter = world_pos
            scene.kjcbhCenterFlag = True

            # アーマチュアの編集モードに切り替え
            bpy.ops.object.mode_set(mode="OBJECT")
            context.view_layer.objects.active = armature_obj
            bpy.ops.object.mode_set(mode="EDIT")

        if self.slot in (0,2):
            armature_obj = context.active_object
            # アーマチュア内のボーンを走査し、ワールド座標で最も近いボーンを選択
            world_pos = Vector(scene.kjcbhCenter)
            selected_bone = None
            if self.slot == 0:
                min_distance = float("inf")
                for bone in armature_obj.data.bones:
                    bone_head_world = armature_obj.matrix_world @ bone.head_local
                    distance = (bone_head_world - world_pos).length
                    if distance < min_distance:
                        min_distance = distance
                        selected_bone = bone
                if not selected_bone:
                    self.report({"ERROR"}, "No bones found in the armature!")
                    return {"CANCELLED"}
            elif self.slot == 2:
                selected_bone = armature_obj.data.edit_bones.active
                if not selected_bone:
                    self.report({"ERROR"}, "No active bone selected!")
                    return {"CANCELLED"}

            # 最も近いボーンのヘッドを移動
            edit_bone = armature_obj.data.edit_bones[selected_bone.name]
            edit_bone.head = armature_obj.matrix_world.inverted() @ world_pos

            # メッシュの編集モードに戻す
            bpy.ops.object.mode_set(mode="OBJECT")
            mesh_obj = bpy.data.objects.get(scene.kjcbhCenterMmeshObj)
            context.view_layer.objects.active = mesh_obj
            bpy.ops.object.mode_set(mode="EDIT")
            scene.kjcbhCenter = (0, 0, 0)
            scene.kjcbhCenterFlag = False
            scene.kjcbhCenterMmeshObj = ""

        return {"FINISHED"}


def set_props():
    scene = bpy.types.Scene
    scene.kjcbhCenterFlag = BoolProperty(default=False)
    scene.kjcbhCenter = FloatVectorProperty(name="vertex center")
    scene.kjcbhCenterMmeshObj = StringProperty(
        name="Mesh Object Name",
        default=""
    )


def clear_props():
    scene = bpy.types.Scene
    del scene.kjcbhCenterFlag
    del scene.kjcbhCenter
    del scene.kjcbhCenterMmeshObj


classes = (
    KJ_CBH_Panel,
    KJ_CenteringBoneHead,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    set_props()


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    clear_props()


if __name__ == "__main__":
    register()
