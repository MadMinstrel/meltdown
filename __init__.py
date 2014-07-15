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

class BakeToolsSettings(bpy.types.PropertyGroup):
    bl_idname = __name__
    resolution_x = bpy.props.IntProperty(name="Resolution X",
                                                default = 1024)
    resolution_y = bpy.props.IntProperty(name="Resolution Y",
                                                default = 1024)
    output = StringProperty(name = 'File path',
                            description = 'The path of the output image. The given extension determines the file type!',
                            default = '//file.png',
                            subtype = 'FILE_PATH')
    
register_class(BakeToolsSettings)
bpy.types.Scene.baketools_settings = PointerProperty(type = BakeToolsSettings)

class BakeToolsBakeOp(bpy.types.Operator):
    '''Bakes'''

    bl_idname = "baketools.bake"
    bl_label = "Bake"
    
    def execute(self, context):
        bts = context.scene.baketools_settings
        
        #cycles baking currently crashes on gpu bake
        bpy.data.scenes['Scene'].cycles.device = 'CPU'
        
        #get rid of old image
        if 'target' in bpy.data.images:
            bpy.data.images['target'].user_clear()
            bpy.data.images.remove(bpy.data.images['target'])
        
        #create render target
        bpy.ops.image.new(name="target", width= bts.resolution_x, height = bts.resolution_y, color=(0.0, 0.0, 0.0, 1.0), alpha=True, generated_type='BLANK', float=False)
        
        #assign file path to render target
        bpy.data.images['target'].filepath = bts.output
        
        #add an image node to the lowpoly model's material
        if "target" not in bpy.data.materials[0].node_tree.nodes:
            imgnode = bpy.data.materials[0].node_tree.nodes.new(type = "ShaderNodeTexImage")
            imgnode.image = bpy.data.images['target']
            imgnode.name = 'target'
            imgnode.label = 'target'
        else:
            imgnode = bpy.data.materials[0].node_tree.nodes['target']
            imgnode.image = bpy.data.images['target']
        
        #bake
        bpy.ops.object.bake(type='NORMAL', filepath="", width=bts.resolution_x, height=bts.resolution_y, margin=16, use_selected_to_active=True, cage_extrusion=0.2, cage_object="", normal_space='TANGENT', normal_r='POS_X', normal_g='POS_Y', normal_b='POS_Z', save_mode='INTERNAL', use_clear=False, use_cage=False, use_split_materials=False, use_automatic_name=False)
        
        #save resulting image
        bpy.data.images['target'].save()
        
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
        bts = context.scene.baketools_settings
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("baketools.bake", text='Bake')
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(bts, 'resolution_x', text="X")
        row.prop(bts, 'resolution_y', text="Y")
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(bts, 'output', text="path")
        
    
def register():
    bpy.utils.register_module(__name__)
    
    
def unregister():
    print("Goodbye World!")
    

if __name__ == "__main__":
    register()