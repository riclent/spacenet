# Licensed to the Apache Software Foundation (ASF) under one or more contributor license agreements; and to You under the Apache License, Version 2.0.

from javascript import UNDEFINED as undefined
from pyweb3d.pyweb3d import *

class Dtn:

    earth_mesh = None
    moon_mesh = None
    document = None
    edge_stimeD = {}
    sim_time_s = None

    @classmethod
    def add_edge(cls, edge):
        print("Adding DTN edge:", edge)
        Dtn.edge_stimeD[edge] = -1                   # -1 = link down
        
    @classmethod
    def update(cls, clock, scene):
        material = LineBasicMaterial({'color':0xffffff, 'opacity':1, 'linewidth': 5})
                
        #print(Dtn.edge_stimeD)
        
        for i, edge in enumerate(cls.edge_stimeD.keys()):
            s_name, d_name = edge
    
            if not edge in Dtn.edge_stimeD: return      # should not happen
            
            #print(s_name, d_name)
            s_mesh = scene.getObjectByName(s_name)
            if s_mesh==undefined: continue

            d_mesh = scene.getObjectByName(d_name)
            if d_mesh==undefined: continue
            link_name = f"link_{i}"

            # test collision
            p0 = Vector3().setFromMatrixPosition(s_mesh.matrixWorld)
            p1 = Vector3().setFromMatrixPosition(d_mesh.matrixWorld)
            raycaster = Raycaster(p1, p0.clone().sub(p1).normalize())
            
            candidates = [s_mesh]
            if Dtn.earth_mesh is not None: candidates.append(Dtn.earth_mesh)
            if Dtn.moon_mesh is not None: candidates.append(Dtn.moon_mesh)

            intersects = raycaster.intersectObjects(candidates)
            
            #print(intersects)
            
            lnk = scene.getObjectByName(link_name)
            if lnk: scene.remove(lnk)
            
            if len(intersects) and intersects[0].object == s_mesh:

                # redraw line
                points = [p0, p1]
                geometry = BufferGeometry().setFromPoints( points )
                e = Line( geometry, material )
                e.name = link_name
                scene.add(e)

                # update contact info
                if Dtn.edge_stimeD[edge] == -1:     # previously down
                    #print(clock, edge, "link up")
                    Dtn.edge_stimeD[edge] = clock

            else:
                # update contact info
                #print(">>", Dtn.edge_stimeD)
                if Dtn.edge_stimeD[edge] >= 0:     # previously up
                    #print(clock, edge, "link down")
                    #print(p0, p1)
                    dist = p0.distanceTo(p1)
                    info = f"{edge[0]} {edge[1]} {Dtn.edge_stimeD[edge]-Dtn.sim_time_s} {clock-Dtn.sim_time_s} {dist}"
                    Dtn.edge_stimeD[edge] = -1

                    #print(":"+info)
                    Dtn.document["contacts"].innerHTML +=  "<br>"+ info 


