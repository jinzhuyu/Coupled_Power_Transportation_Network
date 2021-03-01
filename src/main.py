# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 15:52:10 2020

@author: wany105
""" 
from graph import Graph
from PowerNetwork import Power
from TransportationNetwork import Transportation
from Powerflowmodel import PowerFlowModel
from Trafficflowmodel import TrafficFlowModel
import Interdependency as interlink
import ShareFunction as sf
import Tdata as td
import Pdata as pd
from System import system
from Hurricane import Hurricane
import Hdata as Hcd
import numpy as np
from matplotlib import pyplot as plt
import math


def H_perform_plot(performance, hurricane):
    """Plot the performance curve for the power network under different sceneria
    performance: a list of performance under each hurricane sceneria
    hurricane: a list of hurricane
    """
    fig = plt.figure(figsize = (15, 10))
    for i in range(len(performance)):
        temp1 = performance[i]
        temp2 = hurricane[i]
        plt.plot(np.arange(0, len(temp1), 1), temp1, color = temp2.c, label = temp2.name)
        plt.xlabel('Time Step')
        plt.xticks(np.arange(0, len(temp1), 30))
        plt.ylabel('Performance')
        plt.legend(bbox_to_anchor=(1, 1), loc='upper left', ncol=1, frameon = 0)
        plt.grid(True)
        
def Traffic_Perform_Plot(performance, hurricanes):
    """Plot the performance curve for traffic network
    """
    fig = plt.figure(figsize = (8, 6))
    for i in range(len(performance)):
        temp1 = performance[i]
        temp2 = hurricanes[i]
        perform = sf.Normalize(temp1, Type = 'max')
        plt.plot(np.arange(0, len(perform), 1), perform, color = temp2.c, label = temp2.name, marker = 'o')
        plt.xlabel('Time Step')
        plt.xticks(np.arange(0, len(perform), 1))
        plt.ylabel('Performance')
        plt.legend(bbox_to_anchor=(1, 1), loc='upper left', ncol=1, frameon = 0)
        plt.grid(True)        
        
def Failure_Simulation(Num):
    """Perform Hurricane simulation on the whole system
    """
    #Define selected hurricanes
    Hurricanes = list()
    #Hcd.Hnum = 1
    TXpower.single_perform = np.empty([Hcd.Hnum, Num], dtype = object)
    length = np.zeros([Hcd.Hnum, Num]) #adjust the length of different performance list
    TX_TP.fail_history_final = np.empty(Hcd.Hnum, dtype = object)
    TX_TP.fail_history = np.empty(Hcd.Hnum, dtype = object)
    for i in range(Hcd.Hnum):
        TX_TP.fail_history_final[i] = []
        TX_TP.fail_history[i] = []
        
    #Monte Carlo Simulation to calculate the performance
    for i in range(Hcd.Hnum):
        Hurricanes.append(Hurricane(Hcd.Hurricane_name[i], TXpower, Hcd.Latitude[i], Hcd.Longitude[i], Hcd.color[i]))
        Hurricanes[-1].verticexy(Hcd.Data[i], filelocation = Hcd.Data_Location, Type = 'local')
        Hurricanes[-1].trajectory_plot(townlat = 29.3013, townlon = -94.7977)
        Hurricanes[-1].Failprob(mu = 304, sigma = 1, a = 0.5, b = 1)
#        if(i == 0): #Since fail probability is nearly the same among all hurricane sceneria, we need to add some noise
#        Hurricanes[-1].failprob -= 0.3
        
        for j in range(Num):
            TX_TP.fail_simu(Hurricanes[-1])
            TX_TP.Cascading_failure(pd.up_bound, pd.low_bound)
            TX_TP.fail_history[i].append(TX_TP.failsequence)
            TX_TP.fail_history_final[i].append(TX_TP.failsequence[-1]) ##Track down the final stable state for later use to calculate the conditional probability
            TXpower.single_perform[i, j] = TXpower.fperformance
            length[i, j] = len(TXpower.fperformance)
        
    return length, Hurricanes

def Plot_Hurricanes(Hurricanes, Hnum, townlon, townlat):
    """Plot all simulated hurricanes in one basemap
    """
    color = []
    lat = np.zeros([Hnum, 2])
    lon = np.zeros([Hnum, 2])
    name = []
    lat1, lon1 = math.inf, math.inf
    lat2, lon2 = -math.inf, -math.inf
    Type = 'local'
    
    for i in range(Hnum):            
        lat[i, :] = Hurricanes[i].lat
        lon[i, :] = Hurricanes[i].lon
        color.append(Hurricanes[i].c)
        name.append(Hurricanes[i].name)
        if(lat[i, 0] < lat1):
            lat1 = lat[i, 0]
        if(lat[i, 1] > lat2):
            lat2 = lat[i, 1]
        if(lon[i, 0] < lon1):
            lon1 = lon[i, 0]
        if(lon[i, 1] > lon2):
            lon2 = lon[i, 1]
            
    Base = sf.Basemap(Type, [lat1, lat2], [lon1, lon2])
    townx, towny = Base(townlon, townlat)
    
    for i in range(Hcd.Hnum):
        Nx, Ny = Base(Hurricanes[i].Nlon, Hurricanes[i].Nlat)
        Base.plot(Nx, Ny, marker = 'D', color = color[i], label = Hurricanes[i].name, alpha = 0.5)
        plt.legend()
    Base.scatter(townx, towny, marker = 'D', color = 'red', s = 300, label = 'Galveton, Texas')
    plt.legend(bbox_to_anchor=(1, 1), loc='upper left', ncol=1, frameon = 0)
    
def Power_Performance(length, Num):
    """Quantify the performance of the power network
    """
    max_len = np.max(length)
    TXpower.performance = np.zeros([Hcd.Hnum, int(max_len)])
    for i in range(Hcd.Hnum):
        for j in range(Num):
            ##Unify the length of each array so that we can add them
            while(1):
                if(len(TXpower.single_perform[i, j]) == max_len):
                    break
                TXpower.single_perform[i, j].append(TXpower.single_perform[i, j][-1])
                
            TXpower.performance[i] = TXpower.performance[i] + np.array(TXpower.single_perform[i, j])
        
        TXpower.performance[i] = TXpower.performance[i]/Num
    
def Performance(TXTflow, fail_history, Hnum, Num, PowerNum, TXpower, TXtraffic, TX_TPInter1, capacity, theta):
    TXTflow.performance = np.empty([Hnum, Num], dtype = object)
    temp = 0
    Initial_perform = TXTflow.Cal_performance()
    for i in range(Hnum):
        Temp_fail = fail_history[i]
        for j in range(Num):
            single_fail = Temp_fail[j]
            TXTflow.performance[i, j] = [Initial_perform]
            for m in range(len(single_fail)):
                fail_list = single_fail[m]
                SigFun = []
                TXpower.node_fail = fail_list[0:TXpower.Nnum]
                TXtraffic.node_fail = fail_list[TXpower.Nnum:(TXpower.Nnum + TXtraffic.Nnum)]
                TXpower.node_fail_to_link_fail()
                for k in range(len(TXTflow.network.Adjl)):
                    for l in range(len(TXTflow.network.Adjl[k])):
                        if(fail_list[PowerNum + TXTflow.network.Adjl[k][l] - 1] == 1):
                            SigFun.append(1)
                        else:
                            SigFun.append(0)

                TXTflow.link_sigfun = SigFun
                print(SigFun)
                print(TXTflow.link_capacity)
                TX_TPInter1.InterFunc_decrease(theta, capacity)
                TXTflow.solve_CFW(1e-6, 1e-4, 1e-2)
                TXTflow.performance[i, j].append(TXTflow.Cal_performance())

                temp += 1
#Define the traffic network
TXtraffic = Transportation(graph_dict = td.Tadjl, color = td.color, name = td.name, lat = td.lat, lon = td.lon, nodenum = td.nodenum, edgenum = td.edgenum, \
                           O = td.O, D = td.D, nodefile = td.nodefile, edgefile = td.edgefile, Type = td.Type)
#Define the power network
TXpower = Power(graph_dict = pd.Padjl, color = pd.color, name = pd.name, lat = pd.lat, lon = pd.lon, nodenum = pd.nodenum, edgenum = pd.edgenum, \
                nodefile = pd.nodefile, edgefile = pd.edgefile, Type = pd.Type)

##Define the interdependency
TX_TPInter1 = interlink.PTinter1(TXpower, TXtraffic, name = 'TX_PowerSignal', color = 'orange')
TX_TPInter1.distadj()
DepenNum = [5]*TX_TPInter1.network2.Nnum
TX_TPInter1.dependadj(DepenNum)
TX_TPInter1.Intersection()

##Define the power flow
TXPflow = PowerFlowModel(TXpower)
TXPflow.load([100]*TX_TPInter1.network2.Nnum, TX_TPInter1)
TXPflow.optimizationprob(cost = 1)
TXPflow.solve()
TXpower.topology(pd.nodefile, pd.edgefile, pd.Type)
TXpower.Networkflowplot()


##Transportation flow
TXTflow = TrafficFlowModel(td.Tadjl, td.origins, td.destinations, td.demand, td.free_time, td.capacity, td.function, \
                       td.InterType, td.SigFun, td.Cycle, td.Green, td.t_service, td.hd, TXtraffic)

#Goldensection method
#TXTflow.solve(td.accuracy, td.detail, td.precision)

TXTflow.solve_CFW(1e-6, 1e-5, 1e-2)
TXtraffic.flowmodel = TXTflow

TXtraffic.topology(td.nodefile, td.edgefile, td.Type)
TXtraffic.Networkflowplot()

#Plot the traffic and power network in 2D and 3D respectively
TXpower.topology(pd.nodefile, pd.edgefile, pd.Type)
TXpower.Networkflowplot()
TXtraffic.Networkflowplot()
#plt.savefig("GV_topology_flow.png", dpi = 1500, bbox_inches='tight')


TX_TP = system(name = 'TX_TP', networks = [TXpower, TXtraffic], inters = [TX_TPInter1])
TX_TP.Systemplot3d()
TX_TP.local_global_adj_flow()
TX_TPInter1.system = TX_TP
#plt.savefig("GV_topology_flow3d.png", dpi = 1500, bbox_inches='tight')

#Peform the hurricane simulation
Num = 1
Length, Hurricanes = Failure_Simulation(Num)
Power_Performance(Length, Num)


#Plot the power network performance under each hurricane sceneria
H_perform_plot(TXpower.performance[:, :240], Hurricanes)
#plt.savefig("power_performance.png", dpi = 2000, bbox_inches='tight')

#Calculate the conditional failure probability
TX_TPInter1.Conditional_prob(0, Num)
TX_TPInter1.heatmap_conditional_prob()

#Plot the all hurricanes on a single basemap
Plot_Hurricanes(Hurricanes, Hcd.Hnum, townlon = -94.7977, townlat = 29.3013)
#plt.savefig("hurricane.png", dpi = 3000, bbox_inches='tight')
##Traffic Performance
theta = 0.2
Performance(TXTflow, TX_TP.fail_history, Hcd.Hnum, Num, TXpower.Nnum, TXpower, TXtraffic, TX_TPInter1, td.capacity, theta)
TXtraffic.performance = np.average(sf.Unit_Length(TXTflow.performance), axis = 1)
Traffic_Perform_Plot(TXtraffic.performance, Hurricanes)
#plt.savefig("traffic_perform.png", dpi = 2000, bbox_inches='tight')






    
    

