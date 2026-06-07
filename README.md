# VICSystem
This repository contains the dynamic simulation files for the Victorian transmission system (as part of Australia). 
The system is modeled in STEPSS. More information on the solver is available here: https://stepss.sps-lab.org/
You can find more information on the development and application of the test case in: 
  - J. Vorwerk: Integration of Fast Demand Response into Renewable Power Systems, PhD Thesis, https://doi.org/10.3929/ethz-b-000643071
  - Johanna Vorwerk, Isam Saedi, Pierluigi Mancarella, Gabriela Hug: Electrifying thermal loads vs. installing batteries: A case study on fast frequency resource potentials of the Victorian power system, Electric Power Systems Research, Volume 235, 2024, 110622, https://doi.org/10.1016/j.epsr.2024.110622.


The repository contains the following:
- pyRdat_dyn.dat contains the dynamic model parameters for one operating point
- pyRdat_ss contains the static model parameters for the same operating point
- TNSingleSim is an example file running and evaluating a time-domain simulation including a loss of one large hydro-generator


In addition, the repository includes the option to automatically generate the TN static and dynamic files based on a selected operating point. 
For that 


