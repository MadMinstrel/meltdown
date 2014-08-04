#  (c) 2014 by Piotr Adamowicz (MadMinstrel)

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Bake Tools",
    "author": "Piotr Adamowicz",
    "version": (0, 2),
    "blender": (2, 7, 1),
    "location": "Properties Editor -> Render Panel",
    "description": "Improved baking UI",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://github.com/MadMinstrel/bake-tools/issues",
    "category": "Baking"}

import code
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
    ao_distance = bpy.props.FloatProperty(name="Distance", description="", default=10.0, min=0.0)
    samples = bpy.props.IntProperty(name="Samples", description="", default=1)
    suffix = bpy.props.StringProperty(name="Suffix", description="", default="")

    nm_space = bpy.props.EnumProperty(name = "Normal map space", default = "TANGENT",
                                    items = (("TANGENT","Tangent",""),
                                            ("OBJECT", "Object", "")))

    normal_r = EnumProperty(name="R", description="", default="POS_X", 
                                    items = (("POS_X", "X+", ""), 
                                            ("NEG_X", "X-", ""),
                                            ("POS_Y", "Y+", ""),
                                            ("NEG_Y", "Y-", ""),
                                            ("POS_Z", "Z+", ""),
                                            ("NEG_Z", "Z-", "")))
    normal_g = EnumProperty(name="G", description="", default="POS_Y", 
                                    items = (("POS_X", "X+", ""), 
                                            ("NEG_X", "X-", ""),
                                            ("POS_Y", "Y+", ""),
                                            ("NEG_Y", "Y-", ""),
                                            ("POS_Z", "Z+", ""),
                                            ("NEG_Z", "Z-", "")))
    normal_b = EnumProperty(name="B", description="", default="POS_Z", 
                                    items = (("POS_X", "X+", ""), 
                                            ("NEG_X", "X-", ""),
                                            ("POS_Y", "Y+", ""),
                                            ("NEG_Y", "Y-", ""),
                                            ("POS_Z", "Z+", ""),
                                            ("NEG_Z", "Z-", "")))
    def props(self):
        props = set()
        if self.pass_name == "COMBINED":
            props = {"samples"}
        if self.pass_name == "SHADOW":
            props = {"samples"}
        if self.pass_name == "AO":
            props = {"ao_distance", "samples"}
        if self.pass_name == "NORMAL":
            props = {"nm_space", "swizzle"}
        if self.pass_name == "DIFFUSE_DIRECT":
            props = {"samples"}
        if self.pass_name == "DIFFUSE_INDIRECT":
            props = {"samples"}
        if self.pass_name == "GLOSSY_DIRECT":
            props = {"samples"}
        if self.pass_name == "GLOSSY_INDIRECT":
            props = {"samples"}
        if self.pass_name == "TRANSMISSION_DIRECT":
            props = {"samples"}
        if self.pass_name == "TRANSMISSION_INDIRECT":
            props = {"samples"}
        if self.pass_name == "SUBSURFACE_DIRECT":
            props = {"samples"}
        if self.pass_name == "SUBSURFACE_INDIRECT":
            props = {"samples"}            
        return props
        
    def get_filepath(self, bj):
        path = bj.output 
        if path[-1:] != "/":
            path = path + "/"
        path = path + bj.name 
        if len(self.suffix)>0:
            path += "_" + self.suffix
        path += ".png"
        return path

    def get_filename(self, bj):
        name = bj.name 
        if len(self.suffix)>0:
            name += "_" + self.suffix
        name += ".png"
        return name        
    
register_class(BakePass)
                                            
    
class BakeJob(bpy.types.PropertyGroup):
    resolution_x = bpy.props.IntProperty(name="Resolution X", default = 1024)
    resolution_y = bpy.props.IntProperty(name="Resolution Y", default = 1024)
    
    margin = bpy.props.IntProperty(name="Margin", default = 16, min = 0)
    
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
                #create render target
                if "BTtarget" not in bpy.data.images:
                    bpy.ops.image.new(name="BTtarget", width= bj.resolution_x, height = bj.resolution_y, \
                                        color=(0.0, 0.0, 0.0, 1.0), alpha=True, generated_type='BLANK', float=False)
                baketarget = bpy.data.images["BTtarget"]
                #assign file path to render target
                baketarget.filepath = bakepass.get_filepath(bj)
                
                #copy pass settings to cycles settings
                bpy.data.scenes[0].cycles.bake_type = bakepass.pass_name
                bpy.data.scenes[0].cycles.samples = bakepass.samples
                bpy.data.worlds[0].light_settings.distance = bakepass.ao_distance
                
                #first pair clears the image
                clear = True
                for i, pair in enumerate(bj.bake_queue):
                    # make selections
                    bpy.ops.object.select_all(action='DESELECT')
                    if pair.hp_obj_vs_group == "GRP":
                        for object in bpy.data.groups[pair.highpoly].objects:
                            object.select = True
                    else:
                        bpy.data.scenes[0].objects[pair.highpoly].select = True
                    
                    bpy.data.scenes[0].objects[pair.lowpoly].select = True
                    bpy.context.scene.objects.active = bpy.data.scenes["Scene"].objects[pair.lowpoly]
                    
                    no_materials = False
                    #ensure lowpoly has material
                    if len(bpy.data.scenes[0].objects[pair.lowpoly].data.materials) == 0 \
                        or bpy.data.scenes[0].objects[pair.lowpoly].material_slots[0].material == None:
                        no_materials = True
                        temp_mat = bpy.data.materials.new("BakeToolsTempMat")
                        temp_mat.use_nodes = True
                        bpy.data.scenes["Scene"].objects[pair.lowpoly].data.materials.append(temp_mat)
                        bpy.data.scenes["Scene"].objects["lowpoly"].active_material = temp_mat
                    
                    #add an image node to the lowpoly model's material
                    bake_mat = context.active_object.active_material
                    
                    #code.interact(local=locals())
                    if "target" not in bake_mat.node_tree.nodes:
                        imgnode = bake_mat.node_tree.nodes.new(type = "ShaderNodeTexImage")
                        imgnode.image = baketarget
                        imgnode.name = 'target'
                        imgnode.label = 'target'
                    else:
                        imgnode = bake_mat.node_tree.nodes['target']
                        imgnode.image = baketarget
                    
                    if i>0:
                        clear = False
                    
                    if pair.extrusion_vs_cage == "CAGE":
                        pair_use_cage = True
                    else:
                        pair_use_cage = False
                    
                    #bake
                    bpy.ops.object.bake(type=context.scene.cycles.bake_type, filepath="", \
                    width=bj.resolution_x, height=bj.resolution_y, margin=bj.margin, \
                    use_selected_to_active=True, cage_extrusion=pair.extrusion, cage_object=pair.cage, \
                    normal_space=bakepass.nm_space, \
                    normal_r=bakepass.normal_r, normal_g=bakepass.normal_g, normal_b=bakepass.normal_b, \
                    save_mode='INTERNAL', use_clear=clear, use_cage=pair_use_cage, \
                    use_split_materials=False, use_automatic_name=False)
                
                    bake_mat.node_tree.nodes.remove(imgnode)
                    
                    if no_materials:
                        bpy.data.scenes["Scene"].objects[pair.lowpoly].data.materials.clear()
                        #bpy.ops.object.material_slot_select()
                        bpy.ops.object.material_slot_remove()
                        
                    
                #save resulting image
                baketarget.save()
                
                #unlink from image editors
                for wm in bpy.data.window_managers:
                    for window in wm.windows:
                        for area in window.screen.areas:
                            if area.type == "IMAGE_EDITOR":
                                area.spaces[0].image = None
                #remove image
                baketarget.user_clear()
                bpy.data.images.remove(baketarget)
                
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
        row.operator("baketools.bake", text='Bake', icon = "RADIO")

        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.separator()
        
        for job_i, bj in enumerate(bts.bake_job_queue):
            
            row = layout.row(align=True)
            row.alignment = 'EXPAND'
            row.label(text="Bake Job " + str(job_i+1))

            rem = row.operator("baketools.rem_job", text = "", icon = "X")
            rem.job_index = job_i            
            
            row = layout.row(align=True)
            row.alignment = 'EXPAND'
            row.prop(bj, 'resolution_x', text="X")
            row.prop(bj, 'resolution_y', text="Y")
            
            row = layout.row(align=True)
            row.alignment = 'EXPAND'
            row.prop(bj, 'margin', text="Margin")
            
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
            addpair = row.operator("baketools.add_pair", icon = "DISCLOSURE_TRI_RIGHT")
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
                
                if len(bakepass.props())>0:
                    row = box.row(align=True)
                    row.alignment = 'EXPAND'
                    row.separator()

                    if "ao_distance" in bakepass.props():
                        row = box.row(align=True)
                        row.alignment = 'EXPAND'
                        row.prop(bakepass, 'ao_distance', text = "AO Distance")
                        
                    if "nm_space" in bakepass.props():
                        row = box.row(align=True)
                        row.alignment = 'EXPAND'
                        row.prop(bakepass, 'nm_space', text = "type")

                    if "swizzle" in bakepass.props():
                        row = box.row(align=True)
                        row.alignment = 'EXPAND'
                        row.label(text="Swizzle")
                        row.prop(bakepass, 'normal_r', text = "")
                        row.prop(bakepass, 'normal_g', text = "")
                        row.prop(bakepass, 'normal_b', text = "")
                        
                    if "samples" in bakepass.props():
                        row = box.row(align=True)
                        row.alignment = 'EXPAND'
                        row.prop(bakepass, 'samples', text = "Samples")                        

            row = layout.row(align=True)
            row.alignment = 'EXPAND'
            addpass = row.operator("baketools.add_pass", icon = "DISCLOSURE_TRI_RIGHT")
            addpass.job_index = job_i
            
            row = layout.row(align=True)
            row.alignment = 'EXPAND'
            row.separator()
            
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("baketools.add_job", icon = "ZOOMIN")

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
        bpy.data.scenes[0].baketools_settings.bake_job_queue.remove(self.job_index)
        return {'FINISHED'}
    
def register():
    bpy.utils.register_module(__name__)
    
    #bpy.data.scenes[0].bakejob_settings.bake_queue.add()
    
    
def unregister():
    print("Goodbye World!")
    

if __name__ == "__main__":
    register()