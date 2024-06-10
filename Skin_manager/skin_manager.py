import maya.cmds as mc
import pymel.core as pm
from ngSkinTools2 import api as ng

import os
from pathlib import Path
import re
from collections import namedtuple as nt


Messages = nt('Messages', 'mode_select import_skin export backup_export sandbox')


def export_weights(mesh, filename, location):
    ng.export_json(mesh, file=str(location.joinpath(filename)))
    print('Exported skin:', filename)


class Directories:
    def __init__(self):
        self.project = Path(mc.file(q=True, sn=True)).parent
        self.sandbox = self.project.parent.joinpath('_SANDBOX')
        self.increment = self.sandbox.joinpath('Backups')
        self.characters = self.project.parent.parent.parent.parent
        self.vitruve_sandbox = self.characters.joinpath('Vitruve').joinpath('rigging').joinpath('main').joinpath('_SANDBOX')


class SkinningTools:
    name = 'skinning_tools'
    skin_joints = 'skin_joints_set'
    face_skin_joints = 'face_joints_set'
    margin = 5
    bgc = 0.17

    def __init__(self):
        name = SkinningTools.name

        if mc.window(name, exists=True):
            mc.deleteUI(name, window=True)
        self.window = mc.window(name, iconName='Skinning tools')

        self.dir = Directories()

        self.messages = Messages(
            mode_select='Select import mode',
            import_skin='Imports skin from the Sandbox folder',
            export='Exports skin into the Sandbox folder',
            backup_export='Exports skin into the Sandbox/Backups folder, with increment',
            sandbox='Opens the Sandbox folder',
        )

        mc.columnLayout('Core', adj=True, rs=10)
        mc.separator(style='none')

        mc.frameLayout('Import', mw=self.margin, mh=self.margin, bgc=(self.bgc, self.bgc, self.bgc), cll=True)
        mc.separator(style='none')

        self.mode = mc.optionMenu(l=' Mode:', sbm=self.messages.mode_select)
        mc.menuItem(l='Vertex ID')
        mc.menuItem(l='Closest Point')
        mc.menuItem(l='UV space')

        mc.button(l='Import Skin', command=pm.Callback(self.import_skin, self.dir.sandbox), sbm=self.messages.import_skin)
        mc.button(l='Import Body', command=self.import_body, sbm=self.messages.import_skin)
        mc.button(l='Import Vitruve skin', command=pm.Callback(self.import_skin, self.dir.vitruve_sandbox))
        mc.setParent('..')

        mc.separator(style='in')

        mc.frameLayout('Export', mw=self.margin, mh=self.margin, bgc=(self.bgc, self.bgc, self.bgc), cll=True)
        mc.separator(style='none')
        mc.button(l='Export skin', command=self.export_layers, sbm=self.messages.export)
        mc.button(l='Backup export', command=self.export_layers_with_increment, sbm=self.messages.backup_export)
        mc.setParent('..')

        mc.separator(style='in')
        mc.separator(style='in')

        mc.button(l='Sandbox', command=self.open_sandbox, sbm=self.messages.sandbox)
        mc.separator(style='none')
        mc.separator(style='none')

        # mc.setParent('..')

        mc.showWindow(self.window)

    @staticmethod
    def weights_name(mesh):
        raw_name = re.split(':', mesh)[-1]
        return f'{raw_name}_weights.json'

    def bind_skin(self, node):
        if not mc.objExists(self.face_skin_joints):
            mc.skinCluster(self.skin_joints, node, tsb=True)
        else:
            mc.skinCluster(self.face_skin_joints, self.skin_joints, node, tsb=True)

    def import_layers(self, mesh, source, directory):
        text_mode = mc.optionMenu(self.mode, q=True, v=True)
        transfer_mode = ng.VertexTransferMode.vertexId
        if text_mode == 'Closest Point':
            transfer_mode = ng.VertexTransferMode.closestPoint
        elif text_mode == 'UV space':
            transfer_mode = ng.VertexTransferMode.uvSpace

        config = ng.InfluenceMappingConfig()
        config.use_distance_matching = False
        config.use_name_matching = True

        # run the import
        filename = str(directory.joinpath(self.weights_name(source)))
        ng.import_json(
            mesh,
            file=filename,
            vertex_transfer_mode=transfer_mode,
            influences_mapping_config=config,
        )
        print('Imported: ', filename)

    def import_skin(self, directory, *args):
        selection = mc.ls(sl=True)
        for mesh in selection:
            self.bind_skin(mesh)
            self.import_layers(mesh, mesh, directory)

    def import_body(self, *args):
        selection = mc.ls(sl=True)
        namespace = f'{re.split(":", selection[0])[0]}:'
        body = f'{namespace}body'
        for mesh in selection:
            self.bind_skin(mesh)
            self.import_layers(mesh, body, self.dir.sandbox)

    def export_layers(self, *args):
        for mesh in mc.ls(sl=True):
            filename = self.weights_name(mesh)
            export_weights(mesh, filename, self.dir.sandbox)

    def export_layers_with_increment(self, *args):
        self.dir.increment.mkdir(parents=True, exist_ok=True)

        for mesh in mc.ls(sl=True):
            filename = self.weights_name(mesh)
            extension = '.json'
            count = 1
            raw_name = re.split(extension, filename)[0]

            new_file = f'{raw_name}_{count:03d}{extension}'
            while self.dir.increment.joinpath(new_file).is_file():
                count += 1
                new_file = f'{raw_name}_{count:03d}{extension}'

            export_weights(mesh, new_file, self.dir.increment)

    def open_sandbox(self, *args):
        os.startfile(self.dir.sandbox)
