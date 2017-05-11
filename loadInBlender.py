# This script loads Allen Brain Institute of Science models in blender based on a supplied ontology
# Here's an example of how to call it:
#		blender -P loadInBlender.py -- --ontologyPath "path/to/ontology.json" --objsDir "path/to/dir/with/*.obj"

import bpy
import sys
import os
import argparse
import os.path
import logging
import json

# Setup logging
root = logging.getLogger()
root.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

# Parse the arguments expected by this script
parser = argparse.ArgumentParser(description='Process arguments')
parser.add_argument('--ontologyPath', required="true", help="Path to the ontology");
parser.add_argument('--objsDir', required="true", help="Folder containing the obj files");

# All arguments after the "--" are for this script
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:]);

# Get an RGB dict from the hex string
# Borrowed from https://gist.github.com/dyf/51b25bddfc3338c5cdf3311402dc3610
def hex_str_to_rgb(hex_str):
	# convert a hex string (e.g. "FFFFFF") to an RGB dictionary
	val = int(hex_str, 16)
	return { 
		'r': val & 0x0000ff,
		'g': (val & 0x00ff00) >> 8,
		'b': val >> 16
	}

def center_everything ():
	# Deselect everything
	for obj in bpy.data.objects:
		obj.select = False;

	# Get all of the meshes
	meshes = [item for item in bpy.data.objects if item.type == "MESH"]
	
	# Select each mesh
	for mesh in meshes:
		mesh.select = True;

	# Make the orgin of each selected mesh its own geometry
	bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

	# Get the 3D view context so we can begin moving things around
	context = None
	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			context = bpy.context.copy()
			context['area'] = area
			break;

	# Move each mesh to the center
	bpy.ops.view3d.snap_cursor_to_center( context );
	bpy.ops.view3d.snap_selected_to_cursor( context, use_offset=True )

# Loads the structure's obj in blender
def load_structure_obj (structure, structure_to_obj_dict):
	# Load this structure's obj file
	modelPath = os.path.join(args.objsDir, structure['id'] + '.obj')
	if os.path.isfile(modelPath):
		# Deselect all selected objs
		logging.info('Deselecting all selected objs')
		for obj in bpy.context.selected_objects:
			obj.select = False

		logging.info('Openning file ' + modelPath)
		bpy.ops.import_scene.obj(filepath=modelPath)

		# Create a new material for the imported obj
		rgb_dict = hex_str_to_rgb(structure['color_hex_triplet'])
		mat_name = str(structure['id']) + '-mat'
		mat = bpy.data.materials.new(mat_name)
		mat.diffuse_color = (rgb_dict['r'], rgb_dict['g'], rgb_dict['b'])
		mat.diffuse_shader = 'LAMBERT'
		mat.diffuse_intensity = 1.0

		# Get a handle on the added obj
		obj = bpy.context.selected_objects[0]

		# Update the objs name
		logging.info('Setting obj name to ' + structure['name'])
		obj.name = structure['name']

		# set current object to the active one
		bpy.context.scene.objects.active = obj

		# get the generated material
		mat = bpy.data.materials[mat_name]

		# if a material exists overwrite it
		logging.info('Applying material of color ' + structure['color_hex_triplet'])
		if len(obj.data.materials):
			# assign to 1st material slot
			obj.data.materials[0] = mat

		# if there is no material append it
		else:
			obj.data.materials.append(mat)

		# Make the obj a child of its parent
		parent_id = structure.get('parent_structure_id', None)
		if parent_id:
			logging.info('Making obj a parent of ' + parent_id)

			# Get the objs parent
			parent = structure_to_obj_dict[ parent_id ]

			# Update the parent child relationship
			obj.select = True
			parent.select = True
			bpy.context.scene.objects.active = parent
			bpy.ops.object.parent_set(keep_transform=True)

			# Reset state
			bpy.context.scene.objects.active = obj
			parent.select = False

		return obj
	else:
		logging.info('File ' + modelPath + ' does not exist')
		return None

def load_models_in_ontology ():
	structures = json.load(open(args.ontologyPath,'r'))

	# maps a structures obj to its id
	structure_to_obj_dict = {}

	for structure in structures:
		obj = load_structure_obj(structure, structure_to_obj_dict)
		if obj is not None:
			structure_to_obj_dict[ structure['id'] ] = obj

load_models_in_ontology()
center_everything()