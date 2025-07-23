# Licensed to the Apache Software Foundation (ASF) under one or more contributor license agreements; and to You under the Apache License, Version 2.0.

import math
from pyweb3d.pyweb3d import *
from util import *

class Orbiter:
    def __init__(self, 
        name,
        ref_obj,
        inclination_deg,
        raan,
        eccentricity,
        aperiapsis_deg,
        mean_anomaly_deg,
        mean_motion,
        semi_major_axis_km,
        epochstr=J2000):

        self.name = name
        self.ref_obj = ref_obj
        self.inclination =  math.radians(inclination_deg)                # inclination
        self.raan = math.radians(raan)                     # right ascension of ascending node (eastwards)
        self.eccentricity = eccentricity                                  # eccentricity (0: circle)
        self.aperiapsis = math.radians(aperiapsis_deg)                         # argument of periapsis
        self.mean_anomaly =  math.radians(mean_anomaly_deg)
        self.mean_motion = mean_motion                  # revolutions per day                               # in km
        #self.epoch = self.toTimestamp(epochstr)

        print("Calculations:", name)
        orbital_period = day2sec / mean_motion
        print(f"Approximate Orbital Period: {orbital_period/60:.2f} min")
        self.rotFactor = 2.0*math.pi/orbital_period
        
        #ean_motion_value = (ref_obj.G * ref_obj.mass / (semi_major_axis**3))**.5
        #self.a = (ref_obj.G * ref_obj.mass * (period / (2 * math.pi)) ** 2) ** (1 / 3)
        #self.b = math.sqrt(a*a-self.c*self.c)       # semi-minor axis
        
        self.a = semi_major_axis_km
        self.b = self.a * (1-(eccentricity**2))**.5      # Assuming eccentricity (e)
        self.c = self.a*eccentricity                     # focus distance
        print("a/b/c", self.a, self.b, self.c)
        
        self.mesh = None
        self.orbit_mesh = None

    def getPos(self, theta):
    
        angle = theta + self.mean_anomaly
    
        r = self.a*(1-self.eccentricity**2)/(1+self.eccentricity*math.cos(angle))
        x = r * (math.cos(self.raan)*math.cos(self.aperiapsis+angle) - math.sin(self.raan)*math.sin(self.aperiapsis+angle) *math.cos(self.inclination))
        y = r * (math.sin(self.raan)*math.cos(self.aperiapsis+angle) + math.cos(self.raan)*math.sin(self.aperiapsis+angle) *math.cos(self.inclination));
        z = r * math.sin(self.aperiapsis+angle)*math.sin(self.inclination);
        #return y, z, x
        return x, y, z


    def update(self, clock):
        if not self.mesh: return
        theta = clock*self.rotFactor
        x, y, z = self.getPos(theta)
        self.mesh.position.x = x
        self.mesh.position.y = y
        self.mesh.position.z = z

        
    def build_orbit_mesh(self):
        #material = LineBasicMaterial({'color':0x333333, 'opacity':1})
        material = LineBasicMaterial({'color':0xcccccc, 'opacity':1})
        #ellipse = EllipseCurve(0, 0, self.a, self.b, 0, 2.0*math.pi, False)
        #points = ellipse.getPoints(100)
        #geometry = BufferGeometry().setFromPoints( points )
        
        theta = 0
        points = []
        while theta <= 2*math.pi:
            x, y, z = self.getPos(theta)
            points.append(Vector3(x,y,z))
            theta += 0.1
        points.append(Vector3(points[0].x, points[0].y, points[0].z))
        geometry = BufferGeometry().setFromPoints( points )

        orbit = Line( geometry, material )
        return orbit
        
        
        
class Satellite(Orbiter):

    def __init__(self,
        name,
        ref_obj,
        inclination,
        raan,
        eccentricity,
        aperiapsis,
        mean_anomaly,
        mean_motion,
        semi_major_axis_km,
        epochstr=J2000,
        shape_radius=1):
        
        Orbiter.__init__(self,
        name,
        ref_obj,
        inclination,
        raan,
        eccentricity,
        aperiapsis,
        mean_anomaly,
        mean_motion,
        semi_major_axis_km,
        epochstr)
        
        self.shape_radius = shape_radius
        self.mesh = self.build_mesh()
        self.orbit_mesh = self.build_orbit_mesh()

        
    def build_mesh(self):
        geometry = BoxGeometry( 2*self.shape_radius, 2*self.shape_radius, 2*self.shape_radius )
        # material = MeshBasicMaterial( { 'color': 0xffff00 } )
        material = MeshBasicMaterial( { 'color': 0x0000ff } )
        mesh = Mesh( geometry, material )
        print("MESH BUILT", self .name)
        mesh.name = self.name
        return mesh
        

        


        
        




