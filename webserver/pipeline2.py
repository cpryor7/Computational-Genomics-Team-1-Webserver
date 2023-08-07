import glob
import subprocess
import pathlib
from timeit import default_timer as timer
import psutil
import numpy as np
import threading
import humanfriendly
import os
import argparse
import json

## Pipeline 2: Comp Genomics

#Use command below. Tool specific output is redirected the stderr by default to remove the clutter from stdout.
#python pipeline2.py 1> pipeline2.txt 2> pipeline2.log




# Information being used from python resource library for resource usage tracking.
# 0 ru_utime - time in user mode (float seconds)
# 1 ru_stime - time in system mode (float seconds)
# 3 ru_ixrss - shared memory size
# 4 ru_idrss - unshared memory size

class TrackCPU(threading.Thread):
    '''
    Utility for tracking CPU use by creating a new thread and storing CPU use of the current process in an array.
    Returns the average usage across all CPU cores.
    '''
    def run(self):
        self.running = True
        currentProcess = psutil.Process()
        self.cpu_usage = []
        while self.running:
            self.cpu_usage.append(currentProcess.cpu_percent())

    def stop(self):
        self.running = False
        return np.mean(self.cpu_usage)/ psutil.cpu_count()


def merge_folders(job_id): 
    '''
    Merge assemblies for user inputed isolates and original 50 in folder called ANI_merge
    '''
    contig_dir = pathlib.Path(f"/home/team1/webserver/DB") 
    spades_output_dir = pathlib.Path(f"jobs/{job_id}/spades_results") 
    subprocess.run(['cp', 'spades_output_dir/*.fasta', 'contig_dir']) 
    return 1


def run_ANI(job_id, DB_dir):
    '''
    Run ANI Cluster Map
    '''
    print("running")
    start = timer()
    output_dir = pathlib.Path(f"jobs/{job_id}/ANI_results")
    subprocess.run(['mkdir','-p', output_dir])
    cpu = TrackCPU()
    cpu.start()
    time = []
    memory = []
    p=subprocess.Popen(['ANIclustermap', '-i', DB_dir , '-o', output_dir , '--fig_width' , "20", '--fig_height', "15", '--annotation', '-t', "10"], stdout=2, stderr=subprocess.STDOUT)
    process = os.wait4(p.pid, os.WUNTRACED | os.WCONTINUED)
    time.append(process[2][0] + process[2][1])
    memory.append(process[2][3] + process[2][4])
    end = timer()
    cpu_usage = cpu.stop()
    print(f"ANIclustermap Runtime: {round((end - start)/60, 2)} minutes, CPU Usage {cpu_usage} %, Time (User+System): {humanfriendly.format_timespan(np.mean(time))}, Memory (Shared+Unshared): {humanfriendly.format_size(np.mean(memory))}")
    return 1

def run_parsnp(job_id, DB_dir):
    '''
    Comparative genomics SNP analysis with Parsnp.
    Run parsnp with assemblies files as input and a reference GenBank file
    '''
    start = timer()
    output_dir = pathlib.Path(f"jobs/{job_id}/parsnp_results")
    subprocess.run(['mkdir','-p', output_dir])
    cpu = TrackCPU()
    cpu.start()
    time = []
    memory = []
    p = subprocess.Popen(['parsnp','-g','sequence.gbk','-d', DB_dir,'-c','-o',output_dir])
    p = subprocess.Popen(['figtree', '-graphic', 'PNG', '-width', '500', '-height', '500', output_dir / 'parsnp.tree', output_dir / 'phylogenic_tree_img.png'])
    process = os.wait4(p.pid, os.WUNTRACED | os.WCONTINUED)
    time.append(process[2][0] + process[2][1])
    memory.append(process[2][3] + process[2][4])
    end = timer()
    cpu_usage = cpu.stop()
    print(f"Parsnp Runtime: {round((end - start)/60, 2)} minutes, CPU Usage {cpu_usage} %, Time (User+System): {humanfriendly.format_timespan(np.mean(time))}, Memory (Shared+Unshared): {humanfriendly.format_size(np.mean(memory))}")
    return 1


def save_status(job_status, job_id):
    with open(f'jobs/{job_id}/job_status.json', 'w') as f:
        json.dump(job_status, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser( prog = 'Comparative Genomics', description = 'Comparative genomics pipeline using ANIclustermap and Parsnp')
    parser.add_argument('-j', '--job_id', help='Job ID', required = True)
    parser.add_argument('-d', '--directory', help='Directory containing genomes database', required = True)
    parser.add_argument('-t', '--threads', help='Number of Threads', default=4, type=int)
    args = parser.parse_args()
    
    #job_status = {"ANIclustermap": "Started", "Parsnp": "Pending"}
    #save_status(job_status, args.job_id)
    run_ANI(args.job_id, pathlib.Path(args.directory))
    job_status = {"fastp": "Completed", "spades": "Completed", "quast": "Completed", "prodigal": "Completed", "ANIclustermap": "Completed", "parsnp": "Pending"}
    save_status(job_status, args.job_id)
    run_parsnp(args.job_id, pathlib.Path(args.directory))
    job_status = {"fastp": "Completed", "spades": "Completed", "quast": "Completed", "prodigal": "Completed", "ANIclustermap": "Completed", "parsnp": "Completed"}
    save_status(job_status, args.job_id)