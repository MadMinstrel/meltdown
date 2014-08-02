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

import os
import bpy
from bpy.props import *
from bpy.utils import register_class, unregister_class

class BakePair(bpy.types.PropertyGroup):
    lowpoly = bpy.props.StringProperty(name="", description="", default="")
    cage = bpy.props.StringProperty(name="", description="", default="")
    highpoly = bpy.props.StringProperty(name="", description="", default="")
    hp_obj_vs_group = EnumProperty(name="Object vs Group", description="", default="OBJ", items = [('OBJ', '', 'Object', 'MESH_CUBE', 0), ('GRP', '', 'Group', 'GROUP', 1)])
    extrusion_vs_cage = EnumProperty(name="Extrusion vs Cage", description="", default="EXT", items = [('EXT', '', 'Extrusion', 'OUTLINER_DATA_META', 0), ('CAGE', '', 'Cage', 'OUTLINER_OB_LATTICE', 1)])
    extrusion = bpy.props.FloatProperty(name="Extrusion", description="", default=0.5, min=0.0)
register_class(BakePair)

class BakePass(bpy.types.PropertyGroup):
    pass_name = bpy.props.EnumProperty(name = "Pass", default = "NORMAL",
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
    
    material_override = bpy.props.StringProperty(name="Material Override", description="", default="")
    ao_distance = bpy.props.FloatProperty(name="Distance", description="", default=1.0)
    samples = bpy.props.IntProperty(name="Samples", description="", default=1)
    suffix = bpy.props.StringProperty(name="Suffix", description="", default="")
    
    def get_filepath(self, bj):
        path = bj.output + bj.name 
        if len(self.suffix)>0:
            path += "_" + self.suffix
        path += ".png"
        return path
    
register_class(BakePass)
                                            
    
class BakeJob(bpy.types.PropertyGroup):
    resolution_x = bpy.props.IntProperty(name="Resolution X",
                                                default = 1024)
    resolution_y = bpy.props.IntProperty(name="Resolution Y",
                                                default = 1024)
    output = bpy.props.StringProperty(name = 'File path',
                            description = 'The path of the output image.',
                            default = '//textures/',
                            subtype = 'FILE_PATH')
    name = bpy.props.StringProperty(name = 'name',
                            description = '',
                            default = 'bake')
    
    bake_queue = bpy.props.CollectionProperty(type=BakePair)
    bake_pass_queue = bpy.props.CollectionProperty(type=BakePass)
    
register_class(BakeJob)

class BakeToolsSettings(bpy.types.PropertyGroup):
    bl_idname = __name__
    bake_job_queue = bpy.props.CollectionProperty(type=BakeJob)
    
register_class(BakeToolsSettings)
bpy.types.Scene.baketools_settings = PointerProperty(type = BakeToolsSettings)

class BakeToolsBakeOp(bpy.types.Operator):
    '''Bake'''

    bl_idname = "baketools.bake"
    bl_label = "Bake"
    
    def execute(self, context):
        bts = context.scene.baketools_settings
        
        #cycles baking currently crashes on gpu bake
        cycles_device = bpy.data.scenes['Scene'].cycles.device
        bpy.data.scenes['Scene'].cycles.device = 'CPU'

        for i_job, bj in enumerate(bts.bake_job_queue):
            
            #ensure save path exists
            if not os.path.exists(bpy.path.abspath(bj.output)):
                os.makedirs(bpy.path.abspath(bj.output))
            
            for i, bakepass in enumerate(bj.bake_pass_queue):
                #get rid of old image
                if 'target' in bpy.data.images:
                    bpy.data.images['target'].user_clear()
                    bpy.data.images.remove(bpy.data.images['target'])
            
                #create render target
                bpy.ops.image.new(name="target", width= bj.resolution_x, height = bj.resolution_y, color=(0.0, 0.0, 0.0, 1.0), alpha=True, generated_type='BLANK', float=False)
                #assign file path to render target
                bpy.data.images['target'].filepath = bakepass.get_filepath(bj)
                bpy.data.scenes[0].cycles.bake_type = bakepass.pass_name
                
                clear = True
                for i, pair in enumerate(bj.bake_queue):
                    # make selections
                    bpy.ops.object.select_all(action='DESELECT')
                    # !!!! hardcoded scene name !!!!
                    if pair.hp_obj_vs_group == "GRP":
                        for object in bpy.data.groups[pair.highpoly].objects:
                            object.select = True
                    else:
                        bpy.data.scenes["Scene"].objects[pair.highpoly].select = True
                    
                    bpy.data.scenes["Scene"].objects[pair.lowpoly].select = True
                    bpy.context.scene.objects.active = bpy.data.scenes["Scene"].objects[pair.lowpoly]
                    
                    #add an image node to the lowpoly model's material
                    bake_mat = context.active_object.active_material
                    if "target" not in bake_mat.node_tree.nodes:
                        imgnode = bake_mat.node_tree.nodes.new(type = "ShaderNodeTexImage")
                        imgnode.image = bpy.data.images['target']
                        imgnode.name = 'target'
                        imgnode.label = 'target'
                    else:
                        imgnode = bake_mat.node_tree.nodes['target']
                        imgnode.image = bpy.data.images['target']
                    
                    if i>0:
                        clear = False
                    
                    if pair.extrusion_vs_cage == "CAGE":
                        pair_use_cage = True
                    else:
                        pair_use_cage = False
                    
                    #bake
                    bpy.ops.object.bake(type=context.scene.cycles.bake_type, filepath="", \
                    width=bj.resolution_x, height=bj.resolution_y, margin=16, \
                    use_selected_to_active=True, cage_extrusion=pair.extrusion, cage_object=pair.cage, \
                    normal_space='TANGENT', normal_r='POS_X', normal_g='POS_Y', normal_b='POS_Z', \
                    save_mode='INTERNAL', use_clear=clear, use_cage=pair_use_cage, \
                    use_split_materials=False, use_automatic_name=False)
                
                    bake_mat.node_tree.nodes.remove(imgnode)
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
        bts = context.scene.baketools_settings
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("baketools.bake", text='Bake')

        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.separator()
        
        for job_i, bj in enumerate(bts.bake_job_queue):        
            row = layout.row(align=True)
            row.alignment = 'EXPAND'
            row.prop(bj, 'resolution_x', text="X")
            row.prop(bj, 'resolution_y', text="Y")
            
            row = layout.row(align=True)
            row.alignment = 'EXPAND'
            row.prop(bj, 'output', text="Path")
            
            row = layout.row(align=True)
            row.alignment = 'EXPAND'
            row.prop(bj, 'name', text="Name")
        
            for pair_i, pair in enumerate(bj.bake_queue):
                box = layout.box().column(align=True)
                row = box.row(align=True)
                row.alignment = 'EXPAND'
                row.prop_search(pair, "lowpoly", bpy.context.scene, "objects")
                    
                row = box.row(align=True)
                row.prop(pair, 'hp_obj_vs_group', expand=True)
                if pair.hp_obj_vs_group == 'OBJ':
                    row.prop_search(pair, "highpoly", bpy.context.scene, "objects")
                else:
                    row.prop_search(pair, "highpoly", bpy.data, "groups")
                row = box.row(align=True)
                
                row.prop(pair, 'extrusion_vs_cage', expand=True)
                if pair.extrusion_vs_cage == "EXT":
                    row.prop(pair, 'extrusion', expand=True)
                else:
                    row.prop_search(pair, "cage", bpy.context.scene, "objects")
                
                rem = row.operator("baketools.rem_pair", text = "", icon = "X")
                rem.pair_index = pair_i
                rem.job_index = job_i
            
            row = layout.row(align=True)
            row.alignment = 'EXPAND'
            addpair = row.operator("baketools.add_pair")
            addpair.job_index = job_i
            
            for pass_i, bakepass in enumerate(bj.bake_pass_queue):
                box = layout.box().column(align=True)
                row = box.row(align=True)
                row.alignment = 'EXPAND'
                row.label(text=bakepass.get_filepath(bj = bj))
                
                rem = row.operator("baketools.rem_pass", text = "", icon = "X")
                rem.pass_index = pass_i
                rem.job_index = job_i
                
                row = box.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(bakepass, 'pass_name')
                            
                row = box.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(bakepass, 'suffix')

            row = layout.row(align=True)
            row.alignment = 'EXPAND'
            addpass = row.operator("baketools.add_pass")
            addpass.job_index = job_i
            
            row = layout.row(align=True)
            row.alignment = 'EXPAND'
            row.separator()
            
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("baketools.add_job")

class BakeToolsAddPairOp(bpy.types.Operator):
    '''add pair'''

    bl_idname = "baketools.add_pair"
    bl_label = "Add Pair"
    
    job_index = bpy.props.IntProperty()
    def execute(self, context):
        bpy.data.scenes[0].baketools_settings.bake_job_queue[self.job_index].bake_queue.add()
        
        return {'FINISHED'}

class BakeToolsRemPairOp(bpy.types.Operator):
    '''delete pair'''

    bl_idname = "baketools.rem_pair"
    bl_label = "Remove Pair"
    
    pair_index = bpy.props.IntProperty()
    job_index = bpy.props.IntProperty()
    def execute(self, context):
        bpy.data.scenes[0].baketools_settings.bake_job_queue[self.job_index].bake_queue.remove(self.pair_index)
        
        return {'FINISHED'}
        
class BakeToolsAddPassOp(bpy.types.Operator):
    '''add pass'''

    bl_idname = "baketools.add_pass"
    bl_label = "Add Pass"
    
    job_index = bpy.props.IntProperty()
    def execute(self, context):
        bpy.data.scenes[0].baketools_settings.bake_job_queue[self.job_index].bake_pass_queue.add()
        return {'FINISHED'}

class BakeToolsRemPassOp(bpy.types.Operator):
    '''delete pass'''

    bl_idname = "baketools.rem_pass"
    bl_label = "Remove Pass"
    
    pass_index = bpy.props.IntProperty()
    job_index = bpy.props.IntProperty()
    def execute(self, context):
        bpy.data.scenes[0].baketools_settings.bake_job_queue[self.job_index].bake_pass_queue.remove(self.pass_index)
        return {'FINISHED'}

class BakeToolsAddJobOp(bpy.types.Operator):
    '''add job'''

    bl_idname = "baketools.add_job"
    bl_label = "Add Bake Job"
    
    def execute(self, context):
        bpy.data.scenes[0].baketools_settings.bake_job_queue.add()
        return {'FINISHED'}

class BakeToolsRemJobOp(bpy.types.Operator):
    '''delete job'''

    bl_idname = "baketools.rem_job"
    bl_label = "Remove Bake Job"
    
    job_index = bpy.props.IntProperty()
    def execute(self, context):
        bpy.data.scenes[0].baketools_settings.bake_job_queue.remove(self.pass_index)
        return {'FINISHED'}
    
def register():
    bpy.utils.register_module(__name__)
    
    #bpy.data.scenes[0].bakejob_settings.bake_queue.add()
    
    
def unregister():
    print("Goodbye World!")
    

if __name__ == "__main__":
    register()