bl_info = {
    "name": "Bake Tools",
    "author": "Piotr Adamowicz",
    "version": (0, 1),
    "blender": (2, 7, 1),
    "location": "  ",
    "description": "  ",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Baking"}

import bpy
from bpy.props import *
from bpy.utils import register_class, unregister_class

class BakeQueue(bpy.types.PropertyGroup):
    a = 3
    
class BakeJobSettings(bpy.types.PropertyGroup):
    bl_idname = __name__
    
    bake_pass = bpy.props.EnumProperty(name = "Pass", default = "NORMAL",
                                    items = (("COMBINED","Combined",""),
                                            #("Z","Depth",""),
                                            #("COLOR","Color",""),
                                            #("DIFFUSE","Diffuse",""),
                                            #("SPECULAR","Specular",""),
                                            ("SHADOW","Shadow",""),
                                            ("AO","Ambient Occlusion",""),
                                            #("REFLECTION","Reflection",""),
                                            ("NORMAL","Normal",""),
                                            #("VECTOR","Vector",""),
                                            #("REFRACTION","Refraction",""),
                                            #("OBJECT_INDEX","Object Index",""),
                                            ("UV","UV",""),
                                            #("MIST","Mist",""),
                                            ("EMIT","Emission",""),
                                            ("ENVIRONMENT","Environment",""),
                                            #("MATERIAL_INDEX","Material Index",""),
                                            ("DIFFUSE_DIRECT","DIffuse Direct",""),
                                            ("DIFFUSE_INDIRECT","Diffuse Indirect",""),
                                            ("DIFFUSE_COLOR","Diffuse Color",""),
                                            ("GLOSSY_DIRECT","Glossy Direct",""),
                                            ("GLOSSY_INDIRECT","Glossy Indirect",""),
                                            ("GLOSSY_COLOR","Glossy Color",""),
                                            ("TRANSMISSION_DIRECT","Transmission Direct",""),
                                            ("TRANSMISSION_INDIRECT","Transmission Indirect",""),
                                            ("TRANSMISSION_COLOR","Transmission Color",""),
                                            ("SUBSURFACE_DIRECT","Subsurface Direct",""),
                                            ("SUBSURFACE_INDIRECT","Subsurface Indirect",""),
                                            ("SUBSURFACE_COLOR","Subsurface Color","")))
    
    resolution_x = bpy.props.IntProperty(name="Resolution X",
                                                default = 1024)
    resolution_y = bpy.props.IntProperty(name="Resolution Y",
                                                default = 1024)
    output = bpy.props.StringProperty(name = 'File path',
                            description = 'The path of the output image.',
                            default = '//file.png',
                            subtype = 'FILE_PATH')
    
    lowpoly = bpy.props.StringProperty(name="", description="", default="")
    highpoly = bpy.props.StringProperty(name="", description="", default="")
    hp_obj_vs_group = EnumProperty(name="Object or Group", description="", default="OBJ", items = [('OBJ', '', 'Object', 'MESH_CUBE', 0), ('GRP', '', 'Group', 'GROUP', 1)])
    #hp_obj_vs_group = bpy.props.IntProperty(name="Resolution Y",
    #                                            default = 1024)
    #row.prop_search(m, "sources_chosen_object", scene, "objects")
    
register_class(BakeJobSettings)
bpy.types.Scene.bakejob_settings = PointerProperty(type = BakeJobSettings)

class BakeToolsBakeOp(bpy.types.Operator):
    '''Bakes'''

    bl_idname = "baketools.bake"
    bl_label = "Bake"
    
    def execute(self, context):
        bjs = context.scene.bakejob_settings
        
        #cycles baking currently crashes on gpu bake
        cycles_device = bpy.data.scenes['Scene'].cycles.device
        bpy.data.scenes['Scene'].cycles.device = 'CPU'
        
        #get rid of old image
        if 'target' in bpy.data.images:
            bpy.data.images['target'].user_clear()
            bpy.data.images.remove(bpy.data.images['target'])
        
        #create render target
        bpy.ops.image.new(name="target", width= bjs.resolution_x, height = bjs.resolution_y, color=(0.0, 0.0, 0.0, 1.0), alpha=True, generated_type='BLANK', float=False)
        
        #assign file path to render target
        bpy.data.images['target'].filepath = bjs.output
        
        bake_mat = context.active_object.active_material
        
        #add an image node to the lowpoly model's material
        if "target" not in bake_mat.node_tree.nodes:
            imgnode = bake_mat.node_tree.nodes.new(type = "ShaderNodeTexImage")
            imgnode.image = bpy.data.images['target']
            imgnode.name = 'target'
            imgnode.label = 'target'
        else:
            imgnode = bake_mat.node_tree.nodes['target']
            imgnode.image = bpy.data.images['target']
        
        bpy.data.scenes[0].cycles.bake_type = bjs.bake_pass
        
        # make selections
        bpy.ops.object.select_all(action='DESELECT')
        # !!!! hardcoded scene name !!!!
        if bjs.hp_obj_vs_group == "GRP":
            for object in bpy.data.groups[bjs.highpoly].objects:
                object.select = True
        else:
            bpy.data.scenes["Scene"].objects[bjs.highpoly].select = True
        
        bpy.data.scenes["Scene"].objects[bjs.lowpoly].select = True
        bpy.context.scene.objects.active = bpy.data.scenes["Scene"].objects[bjs.lowpoly]
        
        
        #bake
        bpy.ops.object.bake(type=context.scene.cycles.bake_type, filepath="", width=bjs.resolution_x, height=bjs.resolution_y, margin=16, use_selected_to_active=True, cage_extrusion=1, cage_object="", normal_space='TANGENT', normal_r='POS_X', normal_g='POS_Y', normal_b='POS_Z', save_mode='INTERNAL', use_clear=False, use_cage=False, use_split_materials=False, use_automatic_name=False)
        
        #save resulting image
        bpy.data.images['target'].save()
        
        #restore cycles device after bake
        bpy.data.scenes['Scene'].cycles.device = cycles_device
        
        return {'FINISHED'}

class BakeToolsPanel(bpy.types.Panel):
    bl_label = "Bake Tools"
    bl_idname = "OBJECT_PT_baketools"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        edit = context.user_preferences.edit
        wm = context.window_manager
        bjs = context.scene.bakejob_settings
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("baketools.bake", text='Bake')
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.prop_search(bjs, "lowpoly", bpy.context.scene, "objects")
        
        row = layout.row(align=True)
        row.prop(bjs, 'hp_obj_vs_group', expand=True)
        if bjs.hp_obj_vs_group == 'OBJ':
            row.prop_search(bjs, "highpoly", bpy.context.scene, "objects")
        else:
            row.prop_search(bjs, "highpoly", bpy.data, "groups")
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(bjs, 'resolution_x', text="X")
        row.prop(bjs, 'resolution_y', text="Y")
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(bjs, 'output', text="path")
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(bjs, 'bake_pass')
        

        
    
def register():
    bpy.utils.register_module(__name__)
    
    
def unregister():
    print("Goodbye World!")
    

if __name__ == "__main__":
    register()