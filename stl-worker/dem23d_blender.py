"""Blender batch script for creating 3D-printable DEMs"""
import sys
import os
import subprocess

usage = "blender --background --python {} --".format(__file__)

try:
    import bpy
except ModuleNotFoundError:
    print('usage: ' + usage + ' [options]')
    sys.exit(1)

def set_scene_scale():
    """Change units from m -> mm"""
    bpy.context.scene.unit_settings.scale_length = 0.001
    bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'

def clear_all():
    """Clear the scene for a fresh start"""
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)

    for tex in bpy.data.textures:
        bpy.data.textures.remove(tex)

    for img in bpy.data.images:
        bpy.data.images.remove(img)


class Dem3D():
    def make_terrain_grid(self):
        bpy.ops.image.open(filepath=self.img_path)
        img = bpy.data.images[0]
        img.colorspace_settings.name = 'Non-Color'

        bpy.ops.texture.new()
        height_map = bpy.data.textures[0]
        height_map.name = 'HeightMap'
        height_map.extension = 'EXTEND'
        height_map.image = img

        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions=self.subdivisions,
            y_subdivisions=self.subdivisions,
            location=(0, 0, 0),
        )
        bpy.context.object.name = "Top"

        bpy.ops.object.modifier_add(type='DISPLACE')
        displace = bpy.context.object.modifiers['Displace']
        displace.mid_level = 0

        # Divide by 2 so the mountains come out the right size.
        # I'm not sure what's going on in Blender's scaling algorithm,
        # because I'm feeding in numbers in the thousands, (eg mountains tend
        # to be around 2000m tall) and despite that I get reasonable-looking
        # displacements.  Blender's dividing something somewhere in its algo
        # and it's not clear what or where.
        displace.strength = self.strength / 2
        displace.texture = height_map

        bpy.ops.object.modifier_apply(modifier='Displace')

        scale = self.final_size / 2 # default size is "2mm"
        bpy.ops.transform.resize(value=(scale,scale,scale))

        # Add some thickness for 0-height locations (eg. water)
        bpy.ops.transform.translate(value=(0, 0, self.base_height))

    def fill_base(self):
        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions=self.subdivisions,
            y_subdivisions=self.subdivisions,
            size=self.final_size,
            location=(0, 0, 0),
        )
        bpy.context.object.name = "Bottom"

        for obj in bpy.data.objects:
            obj.select_set(True)
        bpy.ops.object.join()

        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_non_manifold(extend=False)
        bpy.ops.mesh.bridge_edge_loops()
        bpy.ops.object.editmode_toggle()

        bpy.context.object.name = "Model"

    def simplify(self):
        bpy.ops.object.modifier_add(type='DECIMATE')
        decimate = bpy.context.object.modifiers['Decimate']
        decimate.decimate_type = 'UNSUBDIV'
        decimate.iterations = 1

    def to_stl(self, path):
        bpy.ops.export_mesh.stl(filepath=path)

    def create(self):
        self.make_terrain_grid()
        self.fill_base()
        self.simplify()

    def __init__(self, img_path, strength=3,
                 final_size=200, subdivisions=100,
                 base_height=0.2):
        self.img_path = img_path
        self.strength = strength
        self.final_size = final_size
        self.subdivisions = subdivisions
        self.base_height = base_height

        self.create()

def shift_argv(sys_argv):
    if '--' not in sys_argv:
        return []
    else:
        return sys_argv[sys_argv.index('--') + 1:] # Get args after '--'

def parse_args():
    import sys
    import argparse

    parser = argparse.ArgumentParser(prog=usage)

    parser.add_argument('input_image', type=str, help="Input TIFF file")
    parser.add_argument('output_stl', type=str, help="Output STL file")
    parser.add_argument('--final-size', type=float, default=200,
                        help="Length of model in mm")
    parser.add_argument('--subdivisions', type=int, default=500,
                        help="Number of grid points in each axis")
    parser.add_argument('--strength', type=float, default=3,
                        help="Terrain exaggeration")
    parser.add_argument('--base_height', type=float, default=.1,
                        help="Base height in mm")

    return parser.parse_args(shift_argv(sys.argv))

def main():
    args = parse_args()

    clear_all()
    set_scene_scale()

    model = Dem3D(args.input_image,
                  strength=args.strength,
                  final_size=args.final_size,
                  subdivisions=args.subdivisions,
                  base_height=args.base_height)

    model.to_stl(args.output_stl)

def main_prof():
    import line_profiler
    prof = line_profiler.LineProfiler(main,
                                      Dem3D.create,
                                      Dem3D.make_terrain_grid,
                                      Dem3D.fill_base,
                                      Dem3D.to_stl,
                                      Dem3D.simplify)
    prof.runcall(main)
    prof.print_stats()


if __name__ == '__main__':
    if '--profile' in sys.argv:
        sys.argv.remove('--profile')
        main_prof()
    else:
        main()
