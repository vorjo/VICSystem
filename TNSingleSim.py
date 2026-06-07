# -*- coding: utf-8 -*-
"""
Created on Thu May 12 10:43:13 2022

@author: vorwerkj
"""

import pyramses
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

t_step = 0.5

#os.remove(".trace")

    #% Conduct Simulation
ram = pyramses.sim(r"C:\Users\vorjo\OneDrive - Danmarks Tekniske Universitet\Documents\ramses\URAMSES\URAMSES\URAMSES\Release_intel_w64")
# ram = pyramses.sim(r"C:\Users\vorwerkj\Documents_local\pyRamses\URAMSES\URAMSES-3.40c\Release_intel_w64")

case = pyramses.cfg("cmd.txt")

# store results
case.addTrj("out.trj")
case.addOut('output.trace')

# # # execute first 0s
ram.execSim(case,0)

# Load step 
#ram.addDisturb(t_step, 'CHGPRM INJ L0 P0 -500 0.1')

# Loose one generator, producing 500 MW
#ram.addDisturb(t_step, 'BREAKER SYNC_MACH SM35G1 0')

# Fault Bus works fine
#ram.addDisturb(t_step, 'FAULT BUS 193 0 5')
#ram.addDisturb(t_step+0.05, 'CLEAR BUS 193')

# run simulation
Thorizon = 20
try:
     ret = ram.contSim(Thorizon) # Run simulation
     ram.endSim()
except:
    print(ram.getLastErr())
    
#%% Extract Results & set Plot Parameters
plt.style.use("ggplot")
sns.set_style('darkgrid', {'axes.facecolor':'0.9'})
cm = 1/2.54
sns.set_context("paper", font_scale = 1.2, rc={"grid.linewidth": 0.6})
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

#%% Overview plots
ext = pyramses.extractor(case.getTrj())

plot_gens = False
plot_WTs = False
plot_PVs = False
plot_V = False



#%% Generators
# generator names and time
gens = ram.getAllCompNames("SYNC")
# gens.remove('SM774G1')
cons = list(filter(lambda gen: 'Int' in gen , gens))
gens = [i for i in gens if i not in cons]
time =  ext.getSync(gens[0]).S.time
gen_plot =  gens
# extract generator data
td_gen = {
    'P': pd.DataFrame(np.transpose([ext.getSync(x).P.value for x in gens]),columns = gens, index = time),
    'Q': pd.DataFrame(np.transpose([ext.getSync(x).Q.value for x in gens]),columns = gens, index = time),
    'w': pd.DataFrame(np.transpose([ext.getSync(x).S.value*50 for x in gens]),columns = gens, index = time),
    'wcoi': pd.DataFrame(np.transpose([ext.getSync(x).SC.value*50 for x in gens]),columns = gens, index = time),
    'VF': pd.DataFrame(np.transpose([ext.getSync(x).FV.value for x in gens]),columns = gens, index = time),
    'ET': pd.DataFrame(np.transpose([ext.getSync(x).ET.value for x in gens]),columns = gens, index = time),
    'MT': pd.DataFrame(np.transpose([ext.getSync(x).T.value for x in gens]),columns = gens, index = time),
    'A': pd.DataFrame(np.transpose([ext.getSync(x).A.value for x in gens]),columns = gens, index = time),
    }

td_gen['dP'] = td_gen['P']-td_gen['P'].loc[0]
td_gen['dQ'] = td_gen['Q']-td_gen['Q'].loc[0]

# Combine in Plot
fig = plt.figure(None, (13*cm,15*cm))
ax = fig.subplots(4,1, sharex = True)
td_gen['dP'].plot(ax = ax[0], ylabel = 'DP in MW', legend = True)
td_gen['dQ'].plot(ax = ax[1], ylabel = 'dQ in Mvar', legend = False)
td_gen['w'].plot(ax = ax[2], ylabel = r'$f $ in Hz', legend = False)
td_gen['wcoi'].plot(ax = ax[3], ylabel = r'$ \Delta f_\mathrm{COI} $ in Hz', xlabel = 'time in s', legend = False)
ax[0].set_title('Generator Overview')
fig.align_ylabels(ax[:])
# ax[0].set_ylim([-80,300])
# ax[1].set_ylim([-300,300])
# ax[2].set_ylim([47.95,50.05])
plt.savefig('Generators.png', dpi = 300, bbox_inches='tight')

# gen_plot=['SM35G', 'HG199G']
if plot_gens:
    for gen in gen_plot:
        fig = plt.figure(None,(13*cm,15*cm))
        ax = fig.subplots(6,1, sharex = True)
        td_gen['dP'][gen].plot(ax = ax[0], ylabel = 'dP in MW', legend = False)
        td_gen['dQ'][gen].plot(ax = ax[1], ylabel = 'dQ in Mvar', legend = False)
        td_gen['VF'][gen].plot(ax = ax[2], ylabel = 'Vf in pu', legend = False)
        td_gen['w'][gen].plot(ax = ax[3], ylabel = 'f in Hz', legend = False)
        td_gen['MT'][gen].plot(ax = ax[4], ylabel = 'Tm in pu', legend = False)
        td_gen['A'][gen].plot(ax = ax[5], ylabel = 'Angle', legend = False)
        ax[0].set_title(gen)
        # ax[0].set_xlim([0.5,2])


#%% Interconnectors


# extract interconnector data
td_con = {
    'P': pd.DataFrame(np.transpose([ext.getSync(x).P.value for x in cons]),columns = cons, index = time),
    'Q': pd.DataFrame(np.transpose([ext.getSync(x).Q.value for x in cons]),columns = cons, index = time),
    'w': pd.DataFrame(np.transpose([ext.getSync(x).S.value*50 for x in cons]),columns = cons, index = time),
    'wcoi': pd.DataFrame(np.transpose([ext.getSync(x).SC.value*50 for x in cons]),columns = cons, index = time),
    'VF': pd.DataFrame(np.transpose([ext.getSync(x).FV.value for x in cons]),columns = cons, index = time),
    'ET': pd.DataFrame(np.transpose([ext.getSync(x).ET.value for x in cons]),columns = cons, index = time),
    'MT': pd.DataFrame(np.transpose([ext.getSync(x).T.value for x in cons]),columns = cons, index = time),
    'A': pd.DataFrame(np.transpose([ext.getSync(x).A.value for x in cons]),columns = cons, index = time),
    }

td_con['dP'] = td_con['P']-td_con['P'].loc[0]
td_con['dQ'] = td_con['Q']-td_con['Q'].loc[0]

# # Combine in Plot
# fig = plt.figure(None, (13*cm,15*cm))
# ax = fig.subplots(3,1, sharex = True)
# td_con['dP'].plot(ax = ax[0], ylabel = 'DP in MW', legend = True)
# td_con['dQ'].plot(ax = ax[1], ylabel = 'dQ in Mvar', legend = False)
# td_con['w'].plot(ax = ax[2], ylabel = r'$f $ in Hz', legend = False)

# # ax[0].set_xlim([0.5,2])
# # td_gen['wcoi'].plot(ax = ax[3], ylabel = r'$ \Delta f $ in Hz', xlabel = 'time in s', legend = False)
# ax[0].set_title('AC Interconnectors Overview')
# plt.savefig('Interconnector.png', dpi = 300, bbox_inches='tight')

#%%  Plot overall reserve

fig = plt.figure(None,(13*cm,15*cm))
ax = fig.subplots(3,1, sharex = True)


td_gen['dP'].sum(axis =1).plot(ax = ax[0], ylabel = 'dP in MW', legend = False)
td_con['dP'].sum(axis =1).plot(ax = ax[0], ylabel = 'dP in MW', legend = False)

td_gen['dQ'].sum(axis =1).plot(ax = ax[1], ylabel = 'dQ in MW', legend = False)
td_con['dQ'].sum(axis =1).plot(ax = ax[1], ylabel = 'dQ in MW', legend = False)

td_gen['w'].plot(ax = ax[2], ylabel = r'$f $ in Hz', legend = False)
# td_con['w'].plot(ax = ax[2], ylabel = r'$f $ in Hz', legend = False)

ax[0].set_title('Reserve Activation')
ax[0].legend(['Generators','Interconnectors'])

fig.align_ylabels(ax[:])
# ax[0].set_xlim([0,20])
# ax[0].set_ylim([-20,650])
# ax[1].set_ylim([-20,650])
# ax[0].set_xlim([0,100])
plt.savefig('Reserve.png', dpi = 300,bbox_inches='tight')

#%% Inertia Estimation Interconnectors
tH = t_step + 0.1
dP = td_con['dP'][t_step:tH].iloc[-1]
df = td_con['w'][t_step:tH].iloc[-1]-50
H_con = 0.5*dP/df
print('KE supplied by interconnectors: \n' + str(H_con))

dP = td_gen['dP'][t_step:tH].iloc[-1]
df = td_gen['w'][t_step:tH].iloc[-1]-50
H_gen = 0.5*dP/df
print('KE supplied by generators: \n' + str(H_gen))

print('\nTotal KE from \ninterconenctors: '+str(H_con.sum())+'MWs\ngenerators: '+str(H_gen.sum())+'MWs')

#%% Voltages

# # # nodes
# nodes = ram.getAllCompNames("BUS")

# # # extract generator data

# td_nodes = {
#       'V': pd.DataFrame(np.transpose([ext.getBus(x).mag.value for x in nodes]),columns = nodes, index = time),
#       'phase': pd.DataFrame(np.transpose([ext.getBus(x).pha.value for x in nodes]),columns = nodes, index = time),
#       }
# # # Combine in Plot
# if plot_V:
#       fig = plt.figure(None,(13*cm,15*cm))
#       ax = fig.subplots(2,1, sharex = True)
#       td_nodes['V'].plot(ax = ax[0], ylabel = 'V in p.u.', legend = False)
#       td_nodes['phase'].plot(ax = ax[1], ylabel = r'$\theta$ in $^\circ$', xlabel = 'time in s', legend = False)
#       ax[0].set_title('Nodal Voltages')
     
# fig.align_ylabels(ax[:])
# # ax[0].set_ylim([0.82,1.08])
# # ax[1].set_ylim([-82,5])
# # ax[0].set_xlim([0,100])
# plt.savefig('Voltages.png', dpi = 300,bbox_inches='tight')
# # #%% Loads

injs = ram.getAllCompNames("INJ")
# loads = list(filter(lambda x: 'L_' in x, injs))

# loads = {
#     'P': pd.DataFrame(np.transpose([ext.getInj(x).P.value for x in loads]), columns = loads, index = time),
#     'Q': pd.DataFrame(np.transpose([ext.getInj(x).Q.value for x in loads]), columns = loads, index = time),
#     }

# fig = plt.figure(None,(13*cm,15*cm))
# ax = fig.subplots(2,1,sharex=True)
# loads['P'].plot(ax=ax[0], ylabel='P in MW', legend=False)
# loads['Q'].plot(ax=ax[1], ylabel='Q in Mvar', xlabel = 'time in s', legend=False)
# ax[0].set_title('Loads')
# plt.savefig('Loads.png', dpi = 300,bbox_inches='tight')

#%% Wind generators

wts = list(filter(lambda x: 'WT' in x, injs))
wt4 ={
        'P': pd.DataFrame(np.transpose([ext.getInj(x).Pe.value for x in wts]), columns = wts, index = time),
        'Q': pd.DataFrame(np.transpose([ext.getInj(x).Qgen.value for x in wts]), columns = wts, index = time),
        'f': pd.DataFrame(np.transpose([ext.getInj(x).Freq.value*50 for x in wts]), columns = wts, index = time),
        'vt': pd.DataFrame(np.transpose([ext.getInj(x).vt.value for x in wts]), columns = wts, index = time),
        'vref': pd.DataFrame(np.transpose([ext.getInj(x).vref.value for x in wts]), columns = wts, index = time),
        'Pref': pd.DataFrame(np.transpose([ext.getInj(x).Pref.value for x in wts]), columns = wts, index = time),
        }

wt4['dP'] = wt4['P']-wt4['P'].loc[0]
wt4['dQ'] = wt4['Q']-wt4['Q'].loc[0]


fig = plt.figure(None,(13*cm,15*cm))
ax = fig.subplots(4,1,sharex=True)
wt4['P'].plot(ax=ax[0], ylabel='P in pu', legend=False)
wt4['Q'].plot(ax=ax[1], ylabel='Q in pu', legend=False) 
wt4['f'].plot(ax=ax[2], ylabel='f in Hz', legend=False)
wt4['vt'].plot(ax=ax[3], ylabel='v in pu', xlabel = 'time in s', legend=False)
ax[0].set_title('WT4')

fig.align_ylabels(ax[:])
# ax[0].set_ylim([0,1.01])
# ax[1].set_ylim([-0.6,0.6])
# ax[2].set_ylim([47.95,50.05])
# ax[3].set_ylim([0.89,1.01])
# ax[0].set_xlim([0,100])
plt.savefig('WindFarms.png', dpi = 300,bbox_inches='tight')

  # ax[0].legend(col=6, loc = 'upper')
if plot_WTs:
      for wt in wts:
          fig = plt.figure(None,(13*cm,15*cm))
          ax = fig.subplots(6,1,sharex=True)
          wt4['P'][wt].plot(ax=ax[0], ylabel='P in pu', legend=True)
          wt4['Q'][wt].plot(ax=ax[1], ylabel='Q in pu', legend=False) 
          wt4['f'][wt].plot(ax=ax[2], ylabel='f in Hz', legend=False)
          wt4['vt'][wt].plot(ax=ax[3], ylabel='vt i pu', legend=False)
          wt4['vref'][wt].plot(ax=ax[4], ylabel='vref i pu', legend=False)
          wt4['Pref'][wt].plot(ax=ax[5], ylabel='Pref i pu', legend=False)
          ax[0].set_title(wt)
        
#%% PVs
    
pvs = list(filter(lambda x: 'PV' in x, injs))

if pvs !=[]:
    pv ={
          'P': pd.DataFrame(np.transpose([ext.getInj(x).Pe.value for x in pvs]), columns = pvs, index = time),
          'Q': pd.DataFrame(np.transpose([ext.getInj(x).Qgen.value for x in pvs]), columns = pvs, index = time),
          'f': pd.DataFrame(np.transpose([ext.getInj(x).Freq.value*50 for x in pvs]), columns = pvs, index = time),
          'vt': pd.DataFrame(np.transpose([ext.getInj(x).vt.value for x in pvs]), columns = pvs, index = time),
          'vref': pd.DataFrame(np.transpose([ext.getInj(x).vref.value for x in pvs]), columns = pvs, index = time),
          'Pref': pd.DataFrame(np.transpose([ext.getInj(x).Pref.value for x in pvs]), columns = pvs, index = time),
          }
    
    fig = plt.figure(None,(13*cm,15*cm))
    ax = fig.subplots(4,1,sharex=True)
    pv['P'].plot(ax=ax[0], ylabel='P in pu', legend=True)
    pv['Q'].plot(ax=ax[1], ylabel='Q in pu', legend=False) 
    pv['f'].plot(ax=ax[2], ylabel='f in Hz', legend=False)
    pv['vt'].plot(ax=ax[3], ylabel='v in pu', xlabel = 'time in s', legend=False)
    ax[0].set_title('PVs')
    
    # ax[0].legend(col=6, loc = 'upper')
    if plot_PVs:
        for wt in pvs:
            fig = plt.figure(None,(13*cm,15*cm))
            ax = fig.subplots(6,1,sharex=True)
            pv['P'][wt].plot(ax=ax[0], ylabel='P in pu', legend=True)
            pv['Q'][wt].plot(ax=ax[1], ylabel='Q in pu', legend=False) 
            pv['f'][wt].plot(ax=ax[2], ylabel='f in Hz', legend=False)
            pv['vt'][wt].plot(ax=ax[3], ylabel='vt i pu', legend=False)
            pv['vref'][wt].plot(ax=ax[4], ylabel='vref i pu', legend=False)
            pv['Pref'][wt].plot(ax=ax[5], ylabel='Pref i pu', legend=False)
            ax[0].set_title(pvs)
          
    

# %% SVCs

# injs = ram.getAllCompNames("INJ")
# svcs  = list(filter(lambda x: 'SVC' in x, injs))

# td_svc = {
#     'B': pd.DataFrame(np.transpose([ext.getInj(x).B.value for x in svcs]),columns = svcs, index = time),
#     'dB': pd.DataFrame(np.transpose([ext.getInj(x).dB.value for x in svcs]),columns = svcs, index = time),
#     'ix': pd.DataFrame(np.transpose([ext.getInj(x).ix.value for x in svcs]),columns = svcs, index = time),
#     'iy': pd.DataFrame(np.transpose([ext.getInj(x).iy.value for x in svcs]),columns = svcs, index = time),
#     'vx': pd.DataFrame(np.transpose([ext.getInj(x).vx.value for x in svcs]),columns = svcs, index = time),
#     'vy': pd.DataFrame(np.transpose([ext.getInj(x).vy.value for x in svcs]),columns = svcs, index = time),
#     'vt': pd.DataFrame(np.transpose([ext.getInj(x).vt.value for x in svcs]),columns = svcs, index = time),
#     }

# td_svc['P'] = td_svc['vx']*td_svc['ix'] + td_svc['vy']*td_svc['iy']
# td_svc['Q'] = -td_svc['vx']*td_svc['iy'] + td_svc['vy']*td_svc['ix']

# # Combine in Plot
# fig = plt.figure(None,(13*cm,15*cm))
# ax = fig.subplots(5,1, sharex = True)
# td_svc['B'].plot(ax = ax[0], ylabel = 'B', legend = False)
# td_svc['dB'].plot(ax = ax[1], ylabel = 'dB', legend = False)

# td_svc['P'].plot(ax = ax[2], ylabel = 'P', legend = False)
# td_svc['Q'].plot(ax = ax[3], ylabel = 'Q', legend = False)
# td_svc['vt'].plot(ax = ax[4], ylabel = 'vt', legend = False)



