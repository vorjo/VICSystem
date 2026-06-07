# -*- coding: utf-8 -*-
"""
@author: vorwerkj
"""

import pandas as pd

# select LF solution file
time = 24   # available times: 48 times a day
date = '12_22' # available days:    days = ['5_15','7_17','8_9','10_21','12_22']
electrification = '0_0'   # keep at 0, no added thermal load

file = 'LFData/LF_'+date+'_'+electrification+'_'+str(time)+'.txt'

#%% read load flow solution
# copy load flow solution to string
lflow = ''
trfo = ''
branch = ''
gens = ''
bus = ''
svc = ''
with open(file,'r') as file:
    for line in file:
        if 'LFRESV' in line:lflow = lflow+line
        if 'LINE' in line: branch = branch+line
        if 'TRANSFO' in line: trfo = trfo+line
        if 'TRFO' in line: trfo = trfo+line
        if 'GENER' in line: gens = gens + line
        if 'BUS' in line: bus = bus+line
        if 'SVC' in line: svc = svc+line

# copy unchanged data to file
filedata = trfo + branch + lflow

#%% convert data required later to data frames
data = bus
bus = pd.DataFrame([x.split(' ') for x in data.split('\n')], 
                  columns = ['type', 'bus', 'vnom', 'p', 'q', 'bshunt', 'qshunt', 'end']
                  ).drop('end', axis = 1)
bus.index = bus['bus']

data = gens
gens = pd.DataFrame([x.split(' ') for x in data.split('\n')], 
                  columns = ['type', 'name', 'bus', 'mbus', 'p', 'q', 'vimp','snom',
                             'qmin','qmax','br','end']
                  ).drop('end', axis = 1)
gens.index = gens['bus']

data = svc
svc = pd.DataFrame([x.split(' ') for x in data.split('\n')], 
                  columns = ['type', 'name', 'bus', 'mbus', 'v0', 'q', 'snom','bmax',
                             'bmin','g','br','end']
                  ).drop('end', axis = 1)
svc.index = svc['bus']

# print('Generation: '+ str(gens['p'].astype('float64').sum())+'MW')
# print('Load:       '+ str(bus['p'].astype('float64').sum())+'MW')
# print('Losses:     '+ str(gens['p'].astype('float64').sum()-bus['p'].astype('float64').sum())+'MW')
# print('Losses:     '+ str((gens['p'].astype('float64').sum()-bus['p'].astype('float64').sum())/gens['p'].astype('float64').sum())+'%')

D = bus['p'].astype('float64').sum()
G = gens['p'].astype('float64').sum()
L = G-D
LP = L/(G)
print('Demand:        ', "%.2f"%D, 'MW')
print('Generation:    ', "%.2f"%G, 'MW')
print('Total losses:  ', "%.2f"%L, 'MW')
print('Total losses:  ', "%.2f"%LP, '%')
    

#%% split bus data into load and bus data for ramses, same parameters for all loads
bus['p'] = bus['p'].astype('float64')
loads = bus.loc[bus['p']>0].copy()
loads['p'] = -loads['p'].astype('float64')
loads['q'] = -loads['q'].astype('float64')
loads['type'] = 'INJEC LOAD'
loads['name'] = 'L_'+loads['bus']
loads['fp'] = 0
loads['fq'] = 0
loads['dp'] = 0
loads['a1'] = 1
loads['alpha1'] = 1.5
loads['a2'] = 0
loads['alpha2'] = 0
loads['alpha3'] = 0
loads['dq'] = 0
loads['b1'] = 1
loads['beta1'] = 2.25
loads['b2'] = 0
loads['beta2'] = 0
loads['beta3'] = 0
loads['end'] = ';'

loads = loads.filter(['type','name','bus','fp','fq','p','q','dp','a1','alpha1','a2','alpha2','alpha3',
                      'dq','b1','beta1','b2','beta2','beta3','end'], axis =1)

bus['end'] = ';'
bus = bus.filter(['type','bus','vnom','end'], axis = 1)
bus = bus.dropna()
    
#%% SVCs
svc['name'] = 'svc_'+svc['bus']
svc[['p','fp','fq','dp','a2','alpha2','alpha3','dq','b2','beta2','beta3']] = 0
svc[['a1','b1']] = 1
svc[['alpha1','beta1']] = 2
svc['end'] = ';'

svc = svc.filter(['type','name','bus','fp','fq','p','q','dp','a1','alpha1','a2','alpha2','alpha3',
                      'dq','b1','beta1','b2','beta2','beta3','end'], axis =1)
svc = svc.dropna()
svc['type'] = 'INJEC LOAD'

# add to file
filedata = bus.to_string(header = False, index = False) +'\n\n' + loads.to_string(header = False, index = False)+'\n\n' + svc.to_string(header = False, index = False)+'\n\n' + trfo + branch + lflow
with open('pyRamses/pyRdat_ss.dat', 'w') as file:
    file.write(filedata)
    
#%% read dynamic data

# generators and renewables
wind = pd.read_excel('GridData/DynData.xlsx', sheet_name = 'Wind')
pv = pd.read_excel('GridData/DynData.xlsx', sheet_name = 'PV')
sm = pd.read_excel('GridData/DynData.xlsx', sheet_name = 'SM')
consAC = pd.read_excel('GridData/DynData.xlsx', sheet_name = 'Int_AC')
consDC = pd.read_excel('GridData/DynData.xlsx', sheet_name = 'Int_DC')

# exciter models
exc = { 
       'st1a' : pd.read_excel('GridData/Exciters.xlsx', sheet_name = 'ST1A', index_col=0),
       'entsoe' : pd.read_excel('GridData/Exciters.xlsx', sheet_name = 'ENTSOE', index_col=0)
       }

# governors
tor = {
       'tgov1d' : pd.read_excel('GridData/Governors.xlsx', sheet_name = 'TGOV1D', index_col=(0)),
       'hygov' : pd.read_excel('GridData/Governors.xlsx', sheet_name = 'Hydro', index_col=(0)),
       'intgov' : pd.read_excel('GridData/Governors.xlsx', sheet_name = 'Int', index_col=(0))
       }


#%% synchronous machines incl. hydro generators
sm.index = sm['Node'].map(str)
sm['P'] = gens['p'].astype('float64')
sm['Q'] = gens['q'].astype('float64')

# delte the gens that are not producing
sm = sm.loc[sm['P']>1e-3].copy()


# compute active power of twp machines at same bus
sm.index = sm['Name']
sm.loc['SM35G1','P'] = 500
sm.loc['SM35G2','P'] = sm.loc['SM35G2','P']-500
sm.loc['SM35G1','Q'] = sm.loc['SM35G1','Q']/4
sm.loc['SM35G2','Q'] = sm.loc['SM35G2','Q']*3/4

if sm.loc['SM35G2','P']<10: print('Too little generation at bus 35G.')

gendata = '$TOLAC 0.01 ; \n$TOLREAC 0.01 ;\n$NBITMA 50 ;\n$MISBLOC 0 ;\n$MISADJ 1 ;\n$PLIM 1 ;\n$DIVDET 0 ;\nSLACK 681; \nFNOM 50. ;\n\nINJEC PQ L0 682 0 0 0 0 0.01;\n\n\n\n'

for row in sm.index:
    # add generator data to string
    gendata = gendata + sm.loc[row].to_string(header = False, index = False).replace('\n',' ') + '\n'
    
    # add exciter model
    if sm.loc[row]['Snom']>300: gendata = gendata +'\t' + exc['entsoe'].to_string(header = True, index = False).replace('\n',' ')+'\n'
    else: gendata = gendata +'\t'+ exc['st1a'].to_string(header = True, index = False).replace('\n',' ')+'\n'
    
    # add governor model
    
    if 'HG' in sm.loc[row]['Name']: gendata = gendata +'\t'+ tor['hygov'].to_string(header = True, index = False).replace('\n',' ')+';\n\n'        
    else: gendata = gendata +'\t'+ tor['tgov1d'].to_string(header = True, index = False).replace('\n',' ')+';\n\n'

#%% Interconnectors

# AC connectors
# update operation point
consAC.index = consAC['Node'].map(str)
consAC['P'] = gens['p'].astype('float64')
consAC['Q'] = gens['q'].astype('float64')


# copy tp generator data and add constant excitation and governor models
for row in consAC.index:
    # add generator data to string
    gendata = gendata + consAC.loc[row].to_string(header = False, index = False).replace('\n',' ') + '\n'
    
    # add exciter model
    gendata = gendata +'\t EXC CONSTANT\n'
    # gendata = gendata +'\t'+ exc['st1a'].to_string(header = True, index = False).replace('\n',' ')+'\n'
    # add governor model
    gendata = gendata +'\t'+ tor['intgov'].to_string(header = True, index = False).replace('\n',' ')+';\n\n'


# DC connectors
# update operation point
consDC.index = consDC['Node'].map(str)
consDC['P'] = gens['p'].astype('float64')
consDC['Q'] = gens['q'].astype('float64')


# copy to generator data
#gendata = gendata + consDC.to_string(header = False, index = False)+'\n\n'


gendata = gendata.replace('XT', '\n\t XT')


#%% renewable generators

# wind
# copy steady state solution from gens dataframe (artere solution)
wind.index = wind['Node'].map(str)
wind['P'] = gens['p'].astype('float64')
wind['Q'] = gens['q'].astype('float64')
# delete the wind generators that are not producing
wind = wind.loc[wind['P']>1e-3].copy()

# pv
# copy steady state solution from gens dataframe (artere solution)
pv.index = pv['Node'].map(str)
pv['P'] = gens['p'].astype('float64')
pv['Q'] = gens['q'].astype('float64')
# delte the PVs that are not producing
pv = pv.loc[pv['P']>1e-3].copy()

if pv.empty: print('No PVs active.')
else: gendata = gendata + pv.to_string(header = False, index = False)+'\n\n'

if wind.empty: print('No wind generators active.')
else: gendata = gendata + wind.to_string(header = False, index = False)+'\n\n'


with open('pyRamses/pyRdat_dyn.dat', 'w') as file:
    file.write(gendata)
    
    #%% Total load and generation after distribution

D = -loads['p'].sum()
G = sm['P'].sum()+pv['P'].sum()+wind['P'].sum()+consAC['P'].sum()+consDC['P'].sum()
L = G-D
LP = L/(G)
print('Demand:        ', "%.2f"%D, 'MW')
print('Generation:    ', "%.2f"%G, 'MW')
print('Total losses:  ', "%.2f"%L, 'MW')
print('Total losses:  ', "%.2f"%LP, '%')
    
