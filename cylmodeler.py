# *** Notes ***
#
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
###### END GPL LICENSE BLOCK #####

# <pep8 compliant>

bl_info = {
    'name': 'Cylinder modeler',
    'author': 'Miguel Jimenez',
    'version': (0, 4),
    "blender": (2, 5, 8),
    "api": 35622,
    'location': '',
    'description': 'Model a cylinder in function of a sound wave.',
    'warning': '',
    'wiki_url': '',
    'tracker_url': '',
    'category': 'Specific art installation'}
'''
-------------------------------------------------------------------------

-------------------------------------------------------------------------
'''

import bpy
from bpy import * 
from bpy.props import StringProperty, BoolProperty, CollectionProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import IntProperty, BoolProperty, FloatVectorProperty
from io_mesh_stl import stl_utils
from io_mesh_stl import blender_utils

import os,sys
import struct
import mmap
import contextlib
import itertools
import mathutils
import random
import math
import cmath
import webbrowser
import subprocess as sub
from subprocess import *
import string
import re
import socket
import shlex
import time
from time import strftime

### CONFIG VARIABLES ###

absolutepath = "/home/sio2/projectroom/screamprinter/software/screamroom_stable_soundserver/"
objectpath = absolutepath + "stl/"
virginobjectpath = objectpath + "virgins/"
soundpath = absolutepath+"sound/"
timeofrecord = 4
debugprecord = False
debug = False
debugnotprint = True
debugplot = True
wavfilename = "20120229_201830"

### DCR ###
gain = 100
mapping = False
chopping = False
doublechopping = True
mappinglimit = 30
choppinglimit = 50
choppinglimitmax = 70
choppinglimitmin = 10
offsetloud = 10

### DT ###
scalexyaverage = True
scalezlength = True


######
# UI #
######

# class GeneralUI(bpy.types.Panel):
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'TOOLS'
#     bl_label = "Cylinder modeler"
#     bl_context = "objectmode"

#     def draw(self, context):
#         layout = self.layout
#         obj = context.object
#         scene = context.scene
#         col = layout.column(align=True)
#         row = col.row()
#         row.operator("start.buttom", text="Start")        
        
# class StartButtom(bpy.types.Operator):
#     #''''''
#     bl_idname = "start.buttom"
#     bl_label = "Start"

#     @classmethod
#     def poll(cls, context):
#         return context.active_object != None

#     def execute(self, context):
#         return {'FINISHED'}

def createMesh(name, verts, edges, faces):
    me = bpy.data.meshes.new(name+'Mesh')     # Create mesh and object
    ob = bpy.data.objects.new(name, me)
    ob.show_name = True
    bpy.context.scene.objects.link(ob)     # Link object to scene
    me.from_pydata(verts, edges, faces)
    me.update(calc_edges=True)    # Update mesh with new data
    return ob

def load_object():
    """ Loads an object """
    faces,verts = stl_utils.read_stl(virginobjectpath+'basic_cilinder_30_4_quad'+'.stl')
    ob1 = createMesh('virgin', verts, [], faces)

def save_object(filename,faces):
    """ Save object into stl """
    stl_utils.write_stl(filename,faces,False)

def delete_object():
    """ deletes an object """
    bpy.ops.object.delete()

# def register():
#     bpy.utils.register_class(GeneralUI)
#     bpy.utils.register_class(StartButtom)
        
# def unregister():
#     bpy.utils.register_class(GeneralUI)
#     bpy.utils.register_class(StartButtom)
#     pass

def randomize_holes(holenum,meshmap,holedeep,holewidth):
    """ Makes holes in object surface """
    obj = bpy.context.selected_objects[0]
    #obj = context.object    
    mesh = obj.data
    copyverts=mesh.vertices[:]

    for idx in range(holenum):
        #get the position for this hole
        holepos = int(random.uniform(0,len(meshmap)-holewidth))
        
        for idx2 in range(holewidth):
            holemappedpos=meshmap[holepos+idx2][2]
            r,phi=cmath.polar(complex(mesh.vertices[holemappedpos].co[0],mesh.vertices[holemappedpos].co[1]))
            r=r-holedeep
            n=cmath.rect(r,phi)
            mesh.vertices[holemappedpos].co[0]= n.real
            mesh.vertices[holemappedpos].co[1]= n.imag

def get_radio_virgin():
    """ Returns the radio of a virgin object loaded """
    obj = bpy.context.selected_objects[0]
    mesh = obj.data
    r,phi=cmath.polar(complex(mesh.vertices[1].co[0],mesh.vertices[1].co[1]))
    return r

def radvector_mod(vol):
    """ Modifies the radios of the cylinder in vertical lines """
    #capture object
    #obj = context.object    
    obj = bpy.context.selected_objects[0]
    mesh = obj.data
    copyverts=mesh.vertices[:]
    covertices=[]

    #map the levels
    levels=[]
    for index,verticeref in enumerate(copyverts):
        if(mesh.vertices[index].co[2] not in levels):
            levels.append(mesh.vertices[index].co[2])    
    sortedlevels = sorted(levels)
    
    if(debug==True):
        print('*** nlevels:'+str(len(sortedlevels)))
        print('*** thelevels:'+str(sortedlevels))

    #map the radios.
    rounds=[]
    for index,verticeref in enumerate(copyverts):
          if(verticeref.co[2]==sortedlevels[1]):
              r,phi=cmath.polar(complex(verticeref.co[0],verticeref.co[1]))
              rounds.append(math.degrees(phi))
              
    sortedrounds=sorted(rounds)

    #vertex radios traveler 
    print(len(vol))
    for k,actround in enumerate(sortedrounds):
        for l,verticeref in enumerate(copyverts):
            r,phi=cmath.polar(complex(verticeref.co[0],verticeref.co[1]))
            degphi=math.degrees(phi)
            if((degphi > actround - 0.1) and (degphi < actround + 0.1)):
                r=r+float(vol[k])
                x=cmath.rect(r,phi)
                mesh.vertices[l].co[0]= x.real
                mesh.vertices[l].co[1]= x.imag
    return


def sorted_levels_mapper():
    """ Returns a index with the sortout vertices(bottom up velels, clockwise)  """
    #obj = context.object
    obj = bpy.context.selected_objects[0]
    
    mesh = obj.data
    copyverts=mesh.vertices[:]
    
    #index the vertices.
    indexedvertex=[]
    for index,verticeref in enumerate(copyverts):
        r,phi=cmath.polar(complex(mesh.vertices[index].co[0],mesh.vertices[index].co[1]))
        levelmap=[ mesh.vertices[index].co[2] , phi , index ]
        indexedvertex.append(levelmap)        

    sortedindexedvertex = sorted(indexedvertex)
    return(sortedindexedvertex)


def math_lev_mod(mathfunc):
    """ Modifies cylinder levels in function of a mathematical function """
    obj = bpy.context.selected_objects[0]
    mesh = obj.data
    copyverts=mesh.vertices[:]        
    sortedlevelsmapped = sorted_levels_mapper()
    mathcommand = command_parser(mathfunc)

    x=0
    for idx,actvertex in enumerate(sortedlevelsmapped):
        r,phi = cmath.polar(complex(copyverts[actvertex[2]].co[0],copyverts[actvertex[2]].co[1]))
        if(actvertex[0]!=sortedlevelsmapped[idx-1][0]):
            x=x+1

        mod = eval(mathcommand)
        r = r + mod                
        n = cmath.rect(r,phi)
        mesh.vertices[sortedlevelsmapped[idx][2]].co[0]= n.real
        mesh.vertices[sortedlevelsmapped[idx][2]].co[1] = n.imag       

    return


def get_numradios():
    """ Returns number of radios """
    sortedvertexmapped = sorted_levels_mapper()
    x=0
    for idx,actvertex in enumerate(sortedvertexmapped):
        if(actvertex[0]==0.0):
            x=x+1
    return(x)


def get_numlevels():
    """ Returns number of levels """
    sortedvertexmapped = sorted_levels_mapper()
    x=0
    for idx,actvertex in enumerate(sortedvertexmapped):
        if(actvertex[0]!=sortedvertexmapped[idx-1][0]):
            x=x+1
    if(debug==True):
        print('[Cylmodeler] Number of levels: '+str(x))
    return(x)

    
def command_parser(string):
    """ Command parser to math module lang """
    symbols=['sin','cos','exp','pi']

    for isymbol in symbols:
        p = re.compile(isymbol)
        for i in p.finditer(string):
            string=string[:i.start()]+'math.'+string[i.start():]
    return(string)



if __name__ == "__main__":
    #register()


    print("[Cylmodeler] Starting main application in blender")
    #connect to the server.
    #a=os.system("python "+absolutepath+"soundserver.py &")
    #time.sleep(1)

    csocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    csocket.connect(('localhost', 2727))
    print("[Cylmodeler] Connected the sound server.")

    cond=1
    while(cond):
    
        timedate =  strftime("%Y%m%d_%H%M%S")        #capture time/date
        delete_object()        #Delete object.
        load_object()

        for object in bpy.data.objects:         #Select the objects
            object.select=1
            bpy.context.scene.objects.active = object

        r = get_radio_virgin()        #get radio of virgin cylinder

        if(debugnotprint==True):        #configure the server
            csocket.send(bytes("primode=false",'UTF-8'))
        else:
            csocket.send(bytes("primode=true",'UTF-8'))
        rep1 = csocket.recv(256)
        if(str(rep1,'UTF-8')=="done"):
            print("[Cylmodeler] printer-mode command accepted")
        else:
            print("[Cylmoderler] ups... the server didn't ack")
            
        if(debugprecord==True):        #configure the server.
            csocket.send (bytes("premode=true", 'UTF-8'))
        else:
            csocket.send (bytes("premode=false",'UTF-8'))
        rep2 = csocket.recv(256)
        if(str(rep2,'UTF-8') =="done"):
            print("[Cylmodeler] pre-mode command accepted")
        else:
            print("[Cylmoderler] ups... the server didn't ack")
    
        
        csocket.send(bytes("record["+soundpath+wavfilename+".wav]",'UTF-8')) #asks for a sound saple and receives it.
        dataraw=csocket.recv(4096)
        dataraw=str(dataraw,'UTF-8')

        data = dataraw[dataraw.find("[")+1:dataraw.find("]")]         #extract data from server
        frec = dataraw[dataraw.find("(")+1:dataraw.find(")")]
        
        spl = shlex.shlex(data, posix=True) #process data to list
        spl.whitespace += ','
        spl.whitespace_split = True
        a=list(spl)

        print('[Cylmodeler] Number of samples before filter: '+str(len(a)))


        meshmap = sorted_levels_mapper()        # Represent the sound modifiying the cylinder.
        nlevels = get_numlevels()
        nradios = get_numradios()
        print('[Cylmodeler] For the object with:')
        print('- N levels: '+str(nlevels))
        print('- N radios: '+str(nradios))

        divfact = len(a)/(nradios-1)
        a = a[::int(divfact)]
        
        if(debug==True):        #debug if necessary
            print(a)
    
        print('[Cylmodeler] Number of samples after filter: '+str(len(a)))
        
        vect=[]
        for index,element in enumerate(a):
            vect.append(float(element)*gain)


        screamlength=0        #Length of the scream
        for idx,element in enumerate(vect):
            if(element > offsetloud):
                screamlength = screamlength+1

        average=0        # Calculate the average loudness
        for idx,element in enumerate(vect):
            average = float(element)+float(average)
            average = average / len(vect)
            

        maxvect = max(vect)        # Calculate max min
        minvect = min(vect)

        # Design check rules #
        if(mapping == True):        #Mapping
            vectmod = []
            for element in vect:
                vectmod.append((radlimit * element) / maxvect)

        if(chopping == True):        #Chopping
            vectmod = []
            for element in vect:
                if(element > choppinglimit):
                    vectmod.append(choppinglimit)
                else:
                    vectmod.append(element)

        
        if(doublechopping == True):        #double chopping
            vectmod = []
            for element in vect:
                if(element >= choppinglimitmax):
                    vectmod.append(choppinglimitmax)

                elif(element < choppinglimitmin):
                     vectmod.append(choppinglimitmin)
    
                else:
                    vectmod.append(element)
          

        # Design transformations. #
        if(scalexyaverage == True):        #scale object
            scalefactor = (maxvect * 1.2) / 100
            if(float(scalefactor) < 0.6):
                scalefactor = 0.6
            elif(scalefactor > 1.2):
                scalefactor = 1.2
            bpy.context.active_object.scale = (scalefactor,scalefactor,1)
      
        if(scalezlength == True):        # Z Axys scale 1 with total length 30  
            if(screamlength < 15):
                screamlength =  15
            if(screamlength > 24):
                screamlength =  24

            zscale = screamlength/24
            bpy.context.active_object.scale = (1,1,zscale)
        
        if(mapping == False and chopping == False and doublechopping == False):
            vectmod = vect
            
        radvector_mod(vectmo)        #for and proccess the object
        math_lev_mod("3*x-10")
        
        nholes = 0.003 * int(frec)
        nholes = int(nholes)

        randomize_holes(nholes,meshmap,8,4)
        bpy.ops.object.modifier_add(type='SUBSURF')
        bpy.ops.object.modifier_add(type='SUBSURF')


        facesgen=[]
        obj = bpy.context.selected_objects[0]
        facestosave = blender_utils.faces_from_mesh(obj,True,True)         #save object 
        save_object(objectpath+timedate+".stl",facestosave)
        
        print("------------ Object data ------------------")
        print("- Frquency data:" +str(frec)+" - N holes: "+str(nholes))
        print("- Legnth scream:" + str(screamlength))
        print("- Average loudness:"+ str(average))
        print("- Max loudness:" + str(maxvect))
        print("- Min loudness:" + str(minvect))
        print("- Scaling XY value: " + str(scalefactor))
        print("- Scaling Z value: " + str(zscale))

        if(debugplot == True):
            csocket.send (bytes("showplots", 'UTF-8'))
            
        # Convert and print the object. Pronsole & skeinforge #
        if(debugnotprint == False):
            print("[Cylmodeler] Converting format & Printing the object, calling Pronsole macro")
            os.system("python "+absolutepath+"conversion_apps/printrun/pronsole.py "+timedate+" "+absolutepath)
        elif(debugnotprint == True):
            cond = 0
        
    print("[Cylmodeler] Closing the servert.")
    csocket.send(bytes("exit",'UTF-8'))
    csocket.close()
