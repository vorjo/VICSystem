# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 10:39:50 2022

@author: vorwerkj
"""


import pandas as pd
import numpy as np
import subprocess
import seaborn as sns
import matplotlib.pyplot as plt
import shutil

powerFactor = 0.98
artere = {}
tmax = 48

date = '12_22' # available days:    days = ['5_15','7_17','8_9','10_21','12_22']
electrification = '0_0'   # keep at 0, no added thermal load


#%% Extract Results & set Plot Parameters
plt.style.use("ggplot")
sns.set_style('darkgrid', {'axes.facecolor':'0.9'})
cm = 1/2.54
sns.set_context("paper", font_scale = 1.6, rc={"grid.linewidth": 0.6})
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica"]})
# for Palatino and other serif fonts use:
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ["Palatino"],
})
palette = ["#1269b0","#a8322d",'#edb120','#72791c', "#91056a", '#6f6f64', '#007a96', '#1f407a','#485a2c']
sns.set_palette(palette)

Vmin =[]
Vmax=[]
Generation=[]
Generation_LF=[]
Interconnectors=[]
Demand = []
Losses =[]
Losses_LF =[]

scen_file = 'Scenarios/Thesis/Output_elec_2025_'+date+'_step_'+electrification+'.xlsx'
demand_file = "Scenarios/Thesis/demand_"+date+"_"+electrification+".xlsx"

for time in range(1,tmax):
    
#%% Buses and loads
    # read all buses
    bus = pd.read_excel('GridData/SteadyStateData.xlsx', sheet_name='Buses')
    bus.index = bus['Name']
    bus.index = bus.index.astype("string")
    
    # background load
    load = pd.read_excel(demand_file, sheet_name='electricity_demand') 
    load.index=load.index+1
    
    
    # thermal load
    loadT = pd.read_excel(demand_file, sheet_name = 'electrified_demand')
    loadT.index = loadT.index+1
    #loadT = loadT.drop("ti", axis = 1)
    loadT = loadT.T
    loadT.index.name = 'Name'
    loadT.index= loadT.index.astype("string")
    
    # compute load per bus
    # background load with specific power factor, thermal loads with pf = 1
    bus['Pb'] = load.loc[time, 'x1']*bus['Pshare']
    bus['Q'] = bus['Pb']*np.sqrt(1/((powerFactor)**2)-1)      # Q = P sqrt(1/cosp^2-1)
    
    # check if low voltage node was added, and add thermal load at low voltage node
    bus['Pt'] = 0
    
    for row in loadT.index:
        if row+'a' in bus.index:
           bus.loc[row+'a', 'Pt'] = loadT.loc[row, time]
        else:
            bus.loc[row, 'Pt'] = loadT.loc[row, time]  
    
    bus['Pt'] = bus['Pt'].fillna(0)         # fill non existing with 0
    
    # need to add VPPs 
    VPP = pd.read_excel(scen_file,
                      sheet_name =  'VPP_MW').drop('ID', axis = 1)
    VPP.index = VPP['Bus'].astype("string")
    bus['PVPP'] = 0
    for row in VPP.index:
        if str(int(row))+'a' in bus.index: bus.loc[row+'a', 'PVPP'] =VPP.loc[row, str(time)]
        else: bus.loc[row, 'PVPP'] = VPP.loc[row, str(time)]
    bus['Pt'] = bus['Pt'].fillna(0)         # fill non existing with 0
    
    # need to add Batteries 
    Bess = pd.read_excel(scen_file,
                      sheet_name =  'Battery_MW').drop('ID', axis = 1)
    Bess.index = Bess['Bus'].astype("string")
    bus['PBess'] = 0
    for row in Bess.index:
        if (row)+'a' in bus.index: bus.loc[row+'a', 'PBess'] =Bess.loc[row, str(time)]
        else: bus.loc[row, 'PBess'] = Bess.loc[row, str(time)]
    bus['PBess'] = bus['PBess'].fillna(0)         # fill non existing with 0
    
    # sum active load per node
    bus['P'] = bus['Pb']+bus['Pt']+bus['PVPP']+bus['PBess']
    
    # Copy artere data in correct order
    bus = bus.filter(['Type', 'Name', 'Voltage', 'P', 'Q'], axis = 1)
    
    # add columns required for artere
    bus['Bshunt'] = 0
    bus['Qshunt'] = 0
    
    
    
    
    #%% Handle Generators
    gens = pd.read_excel('GridData/SteadyStateData.xlsx', sheet_name = 'Generators')
    gens.index = gens['Bus']
    
    sheets={'GPG' : {'name' : 'GPG', 'identifier' : 'G'},
            'Cgens' : {'name' : 'CGens', 'identifier' : 'G'},
            'Hydro' : {'name' : 'Hydro', 'identifier' : 'G'},
            'Wind' : {'name' : 'Wind', 'identifier' : 'W'},
            'PV' : {'name' : 'Solar', 'identifier' : 'PV'},
            }
    
    # Operating points for all generators
    for sheet in sheets: 
        gen_c = pd.read_excel(scen_file,
                          sheet_name =  sheets[sheet]['name'], index_col = 1).drop('ID', axis = 1)
        for row in gen_c.index:
            if str(row)+sheets[sheet]['identifier'] in gens.index:gens.loc[str(row)+sheets[sheet]['identifier'],'P'] = gen_c.loc[row, str(time)].sum()
            elif row in gens.index: gens.loc[row,'P'] = gen_c.loc[row, str(time)].sum()
    
    gens['P'] = gens['P'].fillna(0)
    
    # Update reactive power
    gens['Q'] = 0
    
    # only dispatch generators that are producing
    gens.loc[gens['P']==0,'Breaker'] = 0
    gens.loc[gens['P']>0,'Breaker'] = 1
    
    
    gens['Vcontrl'] = 1
    
    
    #%% Interconnectors
    # handle imports and exports
    # read import and exports
    cons = pd.read_excel('GridData/SteadyStateData.xlsx', sheet_name = 'Interconnectors')
    cons.index = cons['ID']
    
    imports = pd.read_excel(scen_file,
                         sheet_name='Imports', index_col=0)
    
    exports = pd.read_excel(scen_file,
                         sheet_name='Exports', index_col=0)
    
    for row in imports.index:
        cons.loc[row, 'P'] = -exports.loc[row, str(time)].sum()+imports.loc[row, str(time)].sum()
    cons['P'] = cons['P'].fillna(0)         # fill non existing with 0
    
    # drop ID column
    cons = cons.drop('ID',axis = 1)
    
    cons['end']=';'
    
    #%% other equipment
    svcs = pd.read_excel('GridData/SteadyStateData.xlsx', sheet_name = 'SVC')
    svcs.index = svcs['Node']
    
    # read all lines
    lines = pd.read_excel('GridData/SteadyStateData.xlsx', sheet_name="Lines")
    
    # read all transformers
    trafo = pd.read_excel('GridData/SteadyStateData.xlsx', sheet_name='Transfo')
    trafoTap = pd.read_excel('GridData/SteadyStateData.xlsx', sheet_name='Trfo')
    
    
    #%% Artere data file
    
    filedata = filedata = '$TOLAC 0.01 ;\n$TOLREAC 0.01 ;\n$NBITMA 50 ;\n$MISBLOC 0 ;\n$MISADJ 1 ;\n$PLIM 1 ;\n$DIVDET 0 ;'
    filedata = filedata + '\nSLACK 681; \nFNOM 50. ;\n\n'
    
    dfs = [bus, gens,cons , svcs, lines, trafo, trafoTap]
    for df in dfs: 
        df['end'] = ';'
        filedata = filedata+df.to_string(header = False, index = False)
        filedata = filedata + '\n\n'
    
    with open('ArtereData.txt', 'w') as file: file.write(filedata)
    
    
    #%% run artere
    
    
    acmd = 'ArtereData.txt\n\nDF\nLF.txt\nE\n'
    with open('acmd.txt','w')  as file: 
        file.write(acmd)
        file.close()

        
    subprocess.run(['artere.exe','-tacmd.txt'])
    
        
    D = bus['P'].sum()
    G = gens['P'].sum()
    I = cons['P'].sum()
    L = G+I-D
    LP = L/(G+I)
    print('Pre Load flow solution:')
    print('Demand:        ', "%.2f"%D, 'MW')
    print('Generation:    ', "%.2f"%G, 'MW')
    print('Intconnectors: ', "%.2f"%I, 'MW, pos import')
    print('Total losses:  ', "%.2f"%L, 'MW')
    print('Total losses:  ', "%.2f"%LP, '%')
        
    Generation.append((G+I)/1000)
    Interconnectors.append(I)
    Demand.append(D/1000)
    Losses.append(LP*100)
    
    
    # Copy LF solution file
    # os.popen('copy artere\LF.txt LFSol\LF'+str(date)+'_'+str(electrification)+'_'+str(t)+'.txt')
       
    shutil.copy('LF.txt', 'LFData/LF_'+date+'_'+electrification+'_'+str(time)+'.txt')

    #%% read load flow solution
    # copy load flow solution to string
    file = 'LF.txt'
    
    lflow = ''
    bus = ''
    gens = ''
    
    with open(file,'r') as file:
        for line in file:
            if 'LFRESV' in line:lflow = lflow+line
            if 'BUS' in line: bus = bus+line
            if 'GENER' in line: gens = gens + line
    
    data = bus
    bus = pd.DataFrame([x.split(' ') for x in data.split('\n')], 
                      columns = ['type', 'bus', 'vnom', 'p', 'q', 'bshunt', 'qshunt', 'end']
                      ).drop('end', axis = 1)
    bus.index = bus['bus']
    
    data = lflow
    lflow = pd.DataFrame([x.split(' ') for x in data.split('\n')], 
                      columns = ['type', 'bus', 'vmag', 'phase','end']
                      ).drop('end', axis = 1)
    lflow.index = lflow['bus']
    
    data = gens
    gens = pd.DataFrame([x.split(' ') for x in data.split('\n')], 
                      columns = ['type', 'name', 'bus', 'mbus', 'p', 'q', 'vimp','snom',
                                 'qmin','qmax','br','end']
                      ).drop('end', axis = 1)
    gens.index = gens['bus']
    
    # copy voltages and magnitudes
    bus['vmag'] = lflow['vmag'].astype('float64')
    bus['phase'] = lflow['phase'].astype('float64')
    bus['vnom'] = bus['vnom'].astype('float64').round()
    
    
    # boxplot of voltage magnitudes per voltage level
 #   fig = plt.figure(None,(15*cm,10*cm))
  #  ax = sns.boxplot(data=bus, x='vnom', y='vmag', fliersize = 3, color = palette[0])
  #  ax.invert_xaxis()
  #  ax.set_xlabel('Voltage level in kV')
  #  ax.set_ylabel(r'$V_0$ in p.u.')
  #  ax.set_ylim([0.899,1.101])
  #  plt.savefig('Scenarios\Plots\Voltages\S'+str(electrification)+'_'+str(time)+'.png', dpi = 300,bbox_inches='tight')
    
    # print min and max voltages
    Vmin.append(bus['vmag'].min())
    Vmax.append(bus['vmag'].max())
    Generation_LF.append(gens['p'].astype('float64').sum()/1000)
    Losses_LF.append((gens['p'].astype('float64').sum()-D)/(gens['p'].astype('float64').sum())*100)
    print('Maximum voltage:',  bus['vmag'].max(), 'p.u.')
    print('minimum voltage:',  bus['vmag'].min(), 'p.u.')

#%% 
t = [i+1 for i in range(tmax)]

fig = plt.figure(None,(35*cm,20*cm))
ax = fig.subplots(5,1, sharex = True)

ax[0] = sns.barplot(ax=ax[0],x=t,y=Vmax, color=palette[1],linewidth=0)
ax[0] = sns.barplot(ax=ax[0],x=t,y=Vmin, color = '0.9', linewidth=0)

ax[0].set_axisbelow(False)

ax[1]=sns.barplot(ax = ax[1], x=t, y=Generation_LF,color=palette[1],linewidth=0)
ax[1]=sns.barplot(ax = ax[1], x=t, y=Generation,color=palette[0],linewidth=0)


ax[2]=sns.barplot(ax=ax[2],x=t, y=Demand,color=palette[0],linewidth=0)
ax[3]=sns.barplot(ax=ax[3],x=t, y=Interconnectors,color=palette[0],linewidth=0)

ax[4]=sns.barplot(ax=ax[4],x=t, y=Losses_LF,color=palette[1],linewidth=0)
ax[4]=sns.barplot(ax=ax[4],x=t, y=Losses,color=palette[0],linewidth=0)
    
ax[0].set_ylabel(r'$V$ in p.u.')
ax[1].set_ylabel(r'$P_g$ in GW')
ax[2].set_ylabel(r'$P_d$ in GW')
ax[3].set_ylabel(r'$P_\mathrm{int}$ in MW')
ax[4].set_ylabel(r'Losses in \%')
fig.align_ylabels(ax[:])

ax[-1].set_xlabel('Timestamp')

ax[0].set_ylim([0.899,1.101])
ax[1].set_ylim([0.99*np.min(Generation),1.01*np.max(Generation_LF)])
ax[2].set_ylim([0.99*np.min(Demand),1.01*np.max(Demand)])
ax[4].set_ylim([0.99*np.min(Losses),1.01*np.max(Losses_LF)])

from matplotlib.lines import Line2D
custom_lines = [Line2D([0], [0], color=palette[0], lw=4),
                Line2D([0], [0], color=palette[1], lw=4)]

ax[0].legend(custom_lines, ['DC-OPF', 'Newton-Raphson'], loc = 'upper center', bbox_to_anchor=(0.5,1.5), ncol=2)

#plt.savefig('Scenarios\Plots\Overviews\S'+str(electrification)+'.png', dpi = 300,bbox_inches='tight')
#plt.savefig('Scenarios\Plots\Overviews\S'+str(electrification)+'.pdf', dpi = 300,bbox_inches='tight')