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

class BakeToolsBakeOp(bpy.types.Operator):
    '''Bakes'''
    bl_idname = "baketools.bake"
    bl_label = "Bake"

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
        
        row_rem = layout.row(align=True)
        row_rem.alignment = 'EXPAND'
        row_rem.operator("baketools.bake", text='Bake')
        
    
def register():
    bpy.utils.register_module(__name__)
    
    
def unregister():
    print("Goodbye World!")
    

if __name__ == "__main__":
    register()