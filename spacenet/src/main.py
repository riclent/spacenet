# Licensed to the Apache Software Foundation (ASF) under one or more contributor license agreements; and to You under the Apache License, Version 2.0.

import math
#import time
import json
#import yaml
#from datetime import datetime, timezone
from browser import document, window, ajax
from browser.html import A,B
from javascript import UNDEFINED as undefined
from abc import ABC, abstractmethod
from util import *
from orbiter import *
from planet import Planet
from dtn import *

#
# Notes:
# - DTN edges are unidirectional

sim_time_str = "2024-04-01 12:00:00"

camera = None
renderer = None
scene = None
earth, moon, sun = None, None, None
config = {}

earth_tex_fname="textures/2k_earth_daymap.jpg"
moon_tex_fname="textures/lroc_color_poles_2k.jpg"
config_fname="conf/config.json"
sim_time_s = getTimestampSinceJ2000Epoch(sim_time_str)
three_epoch_ms = -1

view_from_earth = False

view_id = 0
animEnabled = False

vis_factor = 0.1        # compressed distances (useful for easier visualization of Earth-Moon links)
#vis_factor = 1         # normal distances  
now_s = sim_time_s
real_time = False
sim_step = 10           # if not real time (s)

show_helpers = False

   

# --------
class Moon(Planet, Orbiter):
    def __init__(self):
        global earth
        Planet.__init__(self, "moon", MOON_RADIUS, spin_period_s=29.53*day2sec,
                    rot_correction_deg=(0, 20, -40))

        Orbiter.__init__(self, "Moon", earth, inclination_deg=5.145 - 23.4, raan=173.99, eccentricity=0.0549, aperiapsis_deg=318.15, mean_anomaly_deg=8, mean_motion=1.0/29.53, semi_major_axis_km=0.3844e6 *vis_factor)

        self.orbit_mesh = self.build_orbit_mesh()

    def update(self, clock):
        global camera
        if not self.mesh: return
        
        self.group.position.x = 0
        self.group.position.y = 0
        self.group.position.z = 0
        Planet.update(self, clock)
        
        theta = clock*self.rotFactor
        x, y, z = self.getPos(theta)
        self.group.position.x = x
        self.group.position.y = y
        self.group.position.z = z

        if view_from_earth:
            camera.lookAt(x, y, z)


class Sun(Planet, Orbiter):
    def __init__(self):
        global earth
        
        Planet.__init__(self, "sun", SUN_RADIUS, spin_period_s=0)
        Orbiter.__init__(self, "sun", earth, inclination_deg=23.4406, raan=0, eccentricity=0.0167133, aperiapsis_deg=282.7685, mean_anomaly_deg=357.5277233, mean_motion=1.0/357.6205, semi_major_axis_km=149597870*vis_factor)

        self.orbit_mesh = self.build_orbit_mesh()
        
        pointLight = PointLight(0xcccccc)
        self.group.add(pointLight)


    def update(self, clock):
        global camera
        if not self.mesh: return
        
        theta = clock*self.rotFactor
        x, y, z = self.getPos(theta)
        #print("ACA", x, y, z )
        self.group.position.x = x
        self.group.position.y = y
        self.group.position.z = z
        
 
 
class Earth(Planet):
    def __init__(self):
        Planet.__init__(self, "earth", EARTH_RADIUS, spin_period_s=23.93*hrs2sec, rot_correction_deg=(0,0,-90))


# --------
def animate(clock_ms):
    global document, earth, moon, scene, three_epoch_ms, animEnabled, real_time, now_s, sim_time_s
    window.requestAnimationFrame( animate )
    
    if three_epoch_ms<0:
        three_epoch_ms=clock_ms
        return

    if animEnabled:
        if real_time:
            now_s = (clock_ms-three_epoch_ms)/1e3 + sim_time_s
        else:
            now_s += sim_step
            
        dt = datetime.fromtimestamp(getTimestampUNIX(now_s)).strftime("%m/%d/%Y %H:%M:%S")
        document["time"].innerHTML=dt
        for p in [earth, moon, sun]:
            if p: p.update(now_s)
        Dtn.update(now_s, scene)
        
    renderer.render( scene, camera )
    
    
def onError(error):
    print(error)


def addGroundStations(central_obj):
    if "ground" in config[central_obj.primary_name]:
        for station_name, pos in config[central_obj.primary_name]["ground"].items():
            central_obj.addGroundStationAtLonLat(station_name, pos["lon"], pos["lat"])

def addOrbiters(central_obj):
    if "orbiter" in config[central_obj.primary_name]:
        if config[central_obj.primary_name]["orbiter"] is None: return
        for orbiter_name, data in config[central_obj.primary_name]["orbiter"].items():
            print("Add orbiter:", orbiter_name)
            orb_obj = Satellite(
                        orbiter_name,
                        central_obj,
                        data["inclination"],
                        data["raan"],
                        data["eccentricity"],
                        data["aperiapsis"],
                        data["mean_anomaly"],
                        data["mean_motion"],
                        data["altitude_km"] + central_obj.radius,
                        data["epoch"],
                        shape_radius=100
                    )
            central_obj.add_orbiter(orb_obj)

    
def onLoad_earth(texture):
    global earth, sim_time_s, sun

    earth = Earth()
    earth.build_mesh(texture)
    addGroundStations(earth)
    scene.add(earth.group)
    Dtn.earth_mesh = earth.mesh
    addOrbiters(earth)
    earth.update(sim_time_s)

    sun = Sun()
    sun.build_mesh(None)
    scene.add(sun.group)
    scene.add(sun.orbit_mesh)
    sun.update(sim_time_s)


def onLoad_moon(texture):
    global earth, moon, scene, camera, sim_time_s
    
    moon = Moon()
    moon.build_mesh(texture)
    addGroundStations(moon)
    scene.add(moon.group)
    scene.add(moon.orbit_mesh)
    Dtn.moon_mesh = moon.mesh
    addOrbiters(moon)
    
    moon.update(sim_time_s)
    
    # moon.group.add(camera)


def process_config(req):
    global textureLoader, config, document, sim_time_s
    config = json.loads(req.text)
    print(config)
    Dtn.document = document
    Dtn.sim_time_s = sim_time_s 
    if "dtn" in config:
        for edge in config["dtn"]:

            #Dtn.edgeL.append(tuple(edge))
            Dtn.add_edge(tuple(edge))
    if "moon" in config:
        texture_moon = textureLoader.load(moon_tex_fname, onLoad_moon, undefined, onError)
    if "earth" in config:
        texture_earth = textureLoader.load(earth_tex_fname, onLoad_earth, undefined, onError)
        
        

def handle_win_resize(x):
    global renderer, camera
    renderer.setSize( window.innerWidth, window.innerHeight-25 )
    camera.aspect = window.innerWidth / window.innerHeight
    camera.updateProjectionMatrix()
   
def handle_keydown(e):
    global animEnabled, view_id, camera, moon
    #print("e.code", e.code)
    if e.code=='Space':
        animEnabled = not animEnabled
    if e.code=='KeyV':
        view_id = (view_id+1)%2
        print("change view:", view_id)

        if view_id == 0:
            camera.position.x = EARTH_RADIUS*5
            camera.position.y = camera.position.z = 0
            camera.lookAt(0,0,0)
        elif view_id == 1:
            m = Vector3()
            m.setFromMatrixPosition(moon.mesh.matrixWorld)
            camera.position.x = m.x*1.2
            camera.position.y = m.y*1.2
            camera.position.z = m.z*1.2
            camera.lookAt(0,0,0)

            
    if e.code=='KeyZ':
            m = Vector3()
            m.setFromMatrixPosition(moon.mesh.matrixWorld)
            #m = Vector3().getPositionFromMatrix(moon.mesh.matrixWorld)
            print(f"moon: {m.x} {m.y} {m.z}")


    
    
###
print("\n\n\nStart")
#Object3D.DefaultUp = Vector3(0,0,1)
OrbitControls = window.THREE.OrbitControls.new

renderer = WebGLRenderer( { 'antialias': True } )
renderer.setSize( window.innerWidth, window.innerHeight-25 )
document.body.appendChild( renderer.domElement )

document  <= B('<div id="time"/>')
document  <= B('<div id="contacts" overflow-y: scroll/>')

window.addEventListener('resize', handle_win_resize)
window.onkeydown = handle_keydown


#document.body.appendChild( window.THREE.VRButton.createButton( renderer ) )

camera = PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 2000, 200e6 )
camera.up.set(0, 0, 1)  # Set the up vector to point upwards
if not view_from_earth:
    camera.position.x = EARTH_RADIUS*5

#
scene = Scene()
controls = OrbitControls(camera, renderer.domElement)



# backdrop
geometry = SphereGeometry(EARTH_RADIUS*100, 32, 32);
material = MeshBasicMaterial( { 'color': 0x000000 } )
material.side = window.THREE.DoubleSide
mesh = Mesh( geometry, material )
scene.add(mesh)



if show_helpers:
    grid = GridHelper( EARTH_RADIUS*100, 100, 0xffffff, 0xffffff )
    grid.material.opacity = 0.2
    grid.material.depthWrite = False
    grid.material.transparent = True
    grid.rotation.x = math.pi/2
    scene.add( grid )
    axesHelper = AxesHelper( 100000 )
    scene.add( axesHelper )


ambient = AmbientLight(0x999999)
scene.add(ambient)
    
textureLoader = TextureLoader()
ajax.get(config_fname, oncomplete=process_config)

animate(0)


