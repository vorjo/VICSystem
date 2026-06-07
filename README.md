# Victorian Transmission System Dynamic Model
This repository contains the dynamic simulation files for the Victorian transmission system (as part of Australia). 
The system is modeled in STEPSS. More information on the solver is available here: https://stepss.sps-lab.org/
You can find more information on the development and application of the test case in: 
  - J. Vorwerk: Integration of Fast Demand Response into Renewable Power Systems, PhD Thesis, https://doi.org/10.3929/ethz-b-000643071
  - Johanna Vorwerk, Isam Saedi, Pierluigi Mancarella, Gabriela Hug: Electrifying thermal loads vs. installing batteries: A case study on fast frequency resource potentials of the Victorian power system, Electric Power Systems Research, Volume 235, 2024, 110622, https://doi.org/10.1016/j.epsr.2024.110622.


The repository contains the following:
- pyRdat_dyn.dat contains the dynamic model parameters for one operating point
- pyRdat_ss contains the static model parameters for the same operating point
- TNSingleSim is an example file running and evaluating a time-domain simulation including a loss of one large hydro-generator


In addition, the repository includes the option to automatically generate the TN static and dynamic files based on a selected operating point. To change the operating point and generate your own static and dynamic files, proceed as follows: 
1. Open the file TNLoadflow.py and select the power factor, the time range, date, and electrification level for which you want to obtain the load flow files. Then run the file. It will create one load flow solution per scenario and store them in a folder LFData. Once the loop is done, a figure is generated that compares the DC OPF outputs (with which the scenarios were generated) to the full power flow solution.
2. Open the file DynamicData.py. Again, select date, time, and electrification. The code will then locate the load-flow solution of interest and transform it into the static and dynamic files needed for simulation. You can then proceed to run dynamic simulations with these files.

The electrification level can be set to 0, 50%, and 100%. It represents how much gas-based residential heating you wish to electrify in your simulation. For more information, consult the linked publications. 

Feel free to contact me in case of questions or problems! 



   


