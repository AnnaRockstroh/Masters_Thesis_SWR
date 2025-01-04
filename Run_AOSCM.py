import sys
sys.path.append("/home/an0104ro/ece-scm-coupling")

from pathlib import Path
import pandas as pd

from AOSCMcoupling import Experiment
from AOSCMcoupling import compute_nstrtini
from AOSCMcoupling import reduce_output
from AOSCMcoupling import AOSCM
from AOSCMcoupling import render_config_xml
from AOSCMcoupling import SchwarzCoupling
from AOSCMcoupling import Context 

if __name__ == "__main__":

    context = Context(
                    platform="cosmos",
                    model_version=4,
                    model_dir="/home/an0104ro/aoscm",
                    output_dir="/home/an0104ro/experiments_reanalysis/output",
                    template_dir="/home/an0104ro/ece-scm-coupling/templates", 
                    data_dir="/home/an0104ro/initial_data/AoM_Reanalysis/"
                )

    target_date = pd.Timestamp("2023-05-28 00:00:00")
    target_latitudes = [79.0,80.0, 81.0]
    target_longitudes = [1.0, 2.5, 4.0, 5.5, 7.0]
    lon_lats = [(lon, lat) for lon in target_longitudes for lat in target_latitudes]

    exp_id = 'R' # Some letter
    schemes = [0] #0 = parallel, 1 = atmo-first, 2 = ocean-first
    SWR_cases = [False, True]
    max_iter = 30

    start_date = target_date 
    simulation_time = pd.Timedelta(2, "days")

    forcing_file_start_date = target_date 
    forcing_file_freq = pd.Timedelta(1, "hours")

    for SWR in SWR_cases: 
        for scheme in schemes: 
            
            if scheme == 0 and SWR == False:
                exp_id = exp_id + 'PP'
            elif scheme == 1 and SWR == False: 
                exp_id = exp_id + 'AF'
            elif scheme == 2 and SWR == False: 
                exp_id = exp_id + 'OF'
            else: 
                exp_id = exp_id + 'SW'
    
            for target_longitude, target_latitude in lon_lats:

                # output dir
                current_folder = Path.cwd()
                output_path = current_folder / f"output_control_experiment_30_iter" 
                output_dir = output_path / f"lon_{target_longitude}_lat_{target_latitude}"
                if SWR == True: 
                    output_dir = output_dir / "SWR"
                output_dir.mkdir(parents = True, exist_ok = True)
                context.output_dir = output_dir
                
                # start initialisation oifs
                ifs_nstrtini = compute_nstrtini(start_date, forcing_file_start_date, int(forcing_file_freq.seconds/3600))

                # input files
                nemo_input_file = context.data_dir / f"CMEMS_init/nemo_restart_{target_longitude}_{target_latitude}_{start_date.date()}.nc"
                si3_input_file = context.data_dir / f"CMEMS_init/si3_restart_{target_longitude}_{target_latitude}_{start_date.date()}.nc"
                rstos_file = context.data_dir / f"rstos_data/rstos_{target_longitude}_{target_latitude}_{start_date.date()}.nc"
                rstas_file = context.data_dir / f"rstas_data/rstas_{target_longitude}_{target_latitude}_{start_date.date()}.nc"
                ifs_input_file = context.data_dir / f"SCM_data/scm_era5_{target_latitude}N_{target_longitude}E_20230528.nc"
                
                # create context file
                experiment = Experiment(
                    dt_cpl=3600,
                    dt_ifs=720, 
                    dt_nemo=1800, 
                    ifs_levels = 137,
                    ifs_leocwa=False,
                    exp_id=exp_id,
                    with_ice=True,
                    nem_input_file=nemo_input_file,
                    ifs_input_file= ifs_input_file,
                    oasis_rstas= rstas_file,
                    oasis_rstos=rstos_file,
                    ice_input_file= si3_input_file,
                    run_start_date=start_date,
                    run_end_date=start_date + simulation_time,
                    ifs_nstrtini=ifs_nstrtini,
                    cpl_scheme = scheme, 
                )

                aoscm = AOSCM(context)

                if SWR == False: 
                    render_config_xml(context, experiment)
                    aoscm = AOSCM(context)
                    aoscm.run_coupled_model()
                elif SWR == True and scheme == 0:
                    reduce_output(
                        context.output_dir / experiment.exp_id, keep_debug_output=True)
                    schwarz = SchwarzCoupling(experiment, context)
                    schwarz.run(max_iter) 

