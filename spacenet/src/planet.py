# Licensed to the Apache Software Foundation (ASF) under one or more contributor license agreements; and to You under the Apache License, Version 2.0.

import math
from abc import ABC, abstractmethod
from pyweb3d.pyweb3d import *
from util import *
from dtn import *

class Planet:

    def __init__(self, name, radius, spin_period_s, rot_correction_deg=(0,0,0)):
        self.radius = radius # *km2gm
        self.primary_name = name.lower()
        if spin_period_s:
            self.rotFactor = 2.0*math.pi/ spin_period_s
        else:
            self.rotFactor = 0
        self.rot_correction_rad = (math.radians(rot_correction_deg[0]), math.radians(rot_correction_deg[1]), math.radians(rot_correction_deg[2]))
        #self.mass = 5.972e24  # mass of the self (kg)
        #self.G = 6.67430e-11  # gravitational constant (m^3 kg^-1 s^-2)
        #self.sunFactor =  2.0*math.pi/(365.25 *day2sec)
        self.mesh = None
        self.group = Group()                 # translation group
        self.rotation_group = Group()
        self.orbiter_lst = []

    def build_mesh(self, texture):
        
        geometry = SphereGeometry(self.radius, 32, 32);
        
        if texture is not None:
            texture.anisotropy = 16
            texture.minFilter = LinearFilter
            texture.maxFilter = NearestFilter
            texture.mapping = EquirectangularReflectionMapping
            material = MeshLambertMaterial( {'map': texture} )
        else:
            material = MeshBasicMaterial( { 'color': 0xffff00 } )
        
        self.mesh = Mesh( geometry, material )
        self.mesh.renderOrder = 10
        self.mesh.rotation.x = math.pi/2                    # original coord
        self.rotation_group.add(self.mesh)
        #+ 3*math.pi/8 + 0.05

        self.group.add(self.rotation_group)

    def update(self, clock):
        if not self.mesh: return
        self.rotation_group.rotation.x = self.rot_correction_rad[0]
        self.rotation_group.rotation.y = self.rot_correction_rad[1]
        self.rotation_group.rotation.z = self.rot_correction_rad[2] + self.rotFactor*clock

        for orb in self.orbiter_lst:
            orb.update(clock)
        
    def addGroundStationAtLonLat(self, name, lon, lat):
        print("Adding station:", name)
        geometry = BoxGeometry( 50, 50, 50 )
        material = MeshBasicMaterial({'color': 0xffff00 })
        mesh = Mesh( geometry, material )
        mesh.name = name
        mesh.renderOrder = 20
        
        p = geoToCart(lon, lat, self.radius)
        mesh.position.set( p[0], p[1], p[2] )

        self.rotation_group.add(mesh)


    def add_orbiter(self, orb):
        self.orbiter_lst.append(orb)
        if orb.mesh:
            orb.mesh.renderOrder = 30
            self.group.add(orb.mesh)
        if orb.orbit_mesh:
            self.group.add(orb.orbit_mesh)
