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
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import smtplib
import os
#Use command below. Tool specific output is redirected the stderr by default to remove the clutter from stdout.
#python pipeline.py 1> pipeline.txt 2> pipeline.log

#to run skesa uncomment lines at the end

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


def run_fastp(ids, job_id, raw_dir):
    '''
    Pre Assembly QC using FastP.
    Uses the Raw FQ files from the location specified above and then outputs the results in `pre_assembly_qc` folder.
    Runs MultiQC to create cummalative plots in the `multiqc` folder under the name `pre_assembly_qc.html`.
    '''
    output_dir = pathlib.Path(f"jobs/{job_id}/pre_assembly_qc")
    subprocess.run(['mkdir','-p',  output_dir / 'fastp_output'], stdout=2, stderr=subprocess.STDOUT)
    cpu = TrackCPU()
    cpu.start()
    time = []
    memory = []
    start = timer()
    for i in ids:
        p = subprocess.Popen(["fastp", "-i", raw_dir / f"{i}_1.fq.gz", "-I", raw_dir / f"{i}_2.fq.gz", "-o", output_dir / "fastp_output" / f"{i}_1.R1.fq.gz", "-O", output_dir / "fastp_output" / f"{i}_2.R2.fq.gz","-5", "-3", "-c", "--thread", "6", "-M", "30", "--average_qual", "30", "-j", output_dir / f"{i}_fastp.json"], stdout=2, stderr=subprocess.STDOUT) #"-h", output_dir / f"{i}.html"
        process = os.wait4(p.pid, os.WUNTRACED | os.WCONTINUED)
        time.append(process[2][0] + process[2][1])
        memory.append(process[2][3] + process[2][4])
    cpu_usage = cpu.stop()
    subprocess.run(["multiqc", output_dir / "", "-n", "pre_assembly_qc.html", '--outdir', f'jobs/{job_id}/multiqc', '-f'], stdout=2, stderr=subprocess.STDOUT)
    subprocess.run(['cp', f'jobs/{job_id}/multiqc/pre_assembly_qc.html', f'pipeline/templates/{job_id}_pre_assembly_qc.html'])
    end = timer()
    print(f"Fastp Runtime: {round((end - start)/60, 2)} minutes, CPU Usage {cpu_usage} %, Time (User+System): {humanfriendly.format_timespan(np.mean(time))}, Memory (Shared+Unshared): {humanfriendly.format_size(np.mean(memory))}")
    return 1

def run_spades(ids, job_id, raw_dir):
    '''
    Genome Assembly using Spades.
    Uses the genomes filtered and trimmed by Fastp from `pre_assembly_qc` folder and generates assemblies in the `spades_results` folder.
    '''
    start = timer()
    output_dir = pathlib.Path(f"jobs/{job_id}/spades_results")
    fastp_output_dir = pathlib.Path(f"jobs/{job_id}/pre_assembly_qc/fastp_output")
    subprocess.run(['mkdir','-p',  output_dir])
    cpu = TrackCPU()
    cpu.start()
    time = []
    memory = []
    start = timer()
    for i in ids:
        output = output_dir / f"{i}"
        p = subprocess.Popen(["spades.py", "-1", fastp_output_dir / f"{i}_1.R1.fq.gz", "-2", fastp_output_dir / f"{i}_2.R2.fq.gz", "-o", output, "-t", "8", "--cov-cutoff", "auto", '--careful'], stdout=2, stderr=subprocess.STDOUT)
        process = os.wait4(p.pid, os.WUNTRACED | os.WCONTINUED)
        time.append(process[2][0] + process[2][1])
        memory.append(process[2][3] + process[2][4])
    end = timer()
    cpu_usage = cpu.stop()
    print(f"Spades Runtime: {round((end - start)/60, 2)} minutes, CPU Usage {cpu_usage} %, Time (User+System): {humanfriendly.format_timespan(np.mean(time))}, Memory (Shared+Unshared): {humanfriendly.format_size(np.mean(memory))}")
    return 1


def run_quast_spades(ids, job_id, raw_dir):
    '''
    Post Spades Genome Assembly QC using Quast.
    Uses the assemblies created by spades from `spades_results` folder and generates quast reports in the `quast_results/spades` folder.
    Also runs MultiQC to create cummalative plots in the `multiqc` folder under the name `spades_post_assembly_qc.html`.
    '''
    output_dir = pathlib.Path(f"jobs/{job_id}/quast_results/")
    spades_output_dir = pathlib.Path(f"jobs/{job_id}/spades_results")
    subprocess.run(['mkdir', '-p', output_dir / 'genomes'])
    start = timer()
    for i in ids:
        subprocess.run(['cp', f'{spades_output_dir}/{i}/contigs.fasta', output_dir / f'genomes/{i}_contigs.fasta'], stdout=2, stderr=subprocess.STDOUT)
    files = ' '.join(glob.glob(str(output_dir / 'genomes/*.fasta')))
    cpu = TrackCPU()
    cpu.start()
    p = subprocess.Popen(f'quast.py {files} -o {output_dir} -t 6', shell=True, stdout=2, stderr=subprocess.STDOUT)
    process = os.wait4(p.pid, os.WUNTRACED | os.WCONTINUED)
    time = process[2][0] + process[2][1]
    memory = process[2][3] + process[2][4]
    cpu_usage = cpu.stop()
    subprocess.run(["multiqc", output_dir / "", "-n", "spades_post_assembly_qc.html", '--outdir', f'jobs/{job_id}/multiqc', '-f'], stdout=2, stderr=subprocess.STDOUT)
    subprocess.run(['cp', f'jobs/{job_id}/multiqc/spades_post_assembly_qc.html', f'pipeline/templates/{job_id}_spades_post_assembly_qc.html'])
    end = timer()
    print(f"Quast Spades Runtime: {round((end - start)/60, 2)} minutes, CPU Usage {cpu_usage} %, Time (User+System): {humanfriendly.format_timespan(time)}, Memory (Shared+Unshared): {humanfriendly.format_size(memory)}")
    return 1

def run_prodigal(ids, job_id, raw_dir):
    '''
    Genome Prediction using Prodigal.
    Uses the assembled genomes by Spades from `spades_results` folder and generates GFF, FNA, and FAA files in the `prodigal_results` folder.
    '''
    start = timer()
    output_dir = pathlib.Path(f"jobs/{job_id}/prodigal_results")
    spades_output_dir = pathlib.Path(f"jobs/{job_id}/spades_results")
    subprocess.run(['mkdir','-p',  output_dir])
    cpu = TrackCPU()
    cpu.start()
    time = []
    memory = []
    start = timer()
    for i in ids:
        output = output_dir / f"{i}"
        p=subprocess.Popen(['prodigal', '-f', 'gff', '-i', spades_output_dir / f'{i}/contigs.fasta', '-o', f'{output}.gff', '-a', f'{output}.faa', '-d', f'{output}.fna'], stdout=2, stderr=subprocess.STDOUT)
        process = os.wait4(p.pid, os.WUNTRACED | os.WCONTINUED)
        time.append(process[2][0] + process[2][1])
        memory.append(process[2][3] + process[2][4])
    end = timer()
    cpu_usage = cpu.stop()
    print(f"Prodigal Runtime: {round((end - start)/60, 2)} minutes, CPU Usage {cpu_usage} %, Time (User+System): {humanfriendly.format_timespan(np.mean(time))}, Memory (Shared+Unshared): {humanfriendly.format_size(np.mean(memory))}")
    return 1

def zip_output(job_id):
    '''
    Zip all outputs to be sent by email
    '''
    subprocess.run(['zip', '-j', '-r', f'jobs/{job_id}/job_results.zip', f'jobs/{job_id}/multiqc/spades_post_assembly_qc.html', f'jobs/{job_id}/multiqc/pre_assembly_qc.html', f'jobs/{job_id}/job_log.log', f'jobs/{job_id}/job_summary.txt', 
                    f'jobs/{job_id}/prodigal_results/', f'jobs/{job_id}/ANI_results/ANIclustermap.png', f"jobs/{job_id}/parsnp_results/phylogenic_tree_img.png", f"jobs/{job_id}/parsnp_results/parsnp.tree"])

def save_status(job_status, job_id):
    with open(f'jobs/{job_id}/job_status.json', 'w') as f:
        json.dump(job_status, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser( prog = 'Genome Assembly', description = 'Genome Assembly Pipeline using SPADES')
    parser.add_argument('-j', '--job_id', help='Job ID', required = True)
    parser.add_argument('-d', '--directory', help='Directory containing gzipped pair ended genomes', required = True)
    parser.add_argument('-t', '--threads', help='Number of Threads', default=4, type=int)
    parser.add_argument('-e', '--email_id', help='Email ID')
    args = parser.parse_args()
    raw_fqs = glob.glob(f'{args.directory}/*.gz') # Location of the RAW fastq files
    ids = [x.split("/")[-1].split('_')[0] for x in raw_fqs]
    job_status = {"fastp": "Started", "spades": "Pending", "quast": "Pending", "prodigal": "Pending", "ANIclustermap": "Pending", "parsnp": "Pending"}
    save_status(job_status, args.job_id)
    run_fastp(ids, args.job_id, pathlib.Path(args.directory))
    job_status = {"fastp": "Completed", "spades": "Started", "quast": "Pending", "prodigal": "Pending", "ANIclustermap": "Pending", "parsnp": "Pending"}
    save_status(job_status, args.job_id)
    run_spades(ids, args.job_id, pathlib.Path(args.directory))
    job_status = {"fastp": "Completed", "spades": "Completed", "quast": "Started", "prodigal": "Pending", "ANIclustermap": "Pending", "parsnp": "Pending"}
    save_status(job_status, args.job_id)
    run_quast_spades(ids, args.job_id, pathlib.Path(args.directory))
    job_status = {"fastp": "Completed", "spades": "Completed", "quast": "Completed", "prodigal": "Pending", "ANIclustermap": "Pending", "parsnp": "Pending"}
    save_status(job_status, args.job_id)
    run_prodigal(ids, args.job_id, pathlib.Path(args.directory)) #Prodigal
    job_status = {"fastp": "Completed", "spades": "Completed", "quast": "Completed", "prodigal": "Completed", "ANIclustermap": "Pending", "parsnp": "Pending"}
    save_status(job_status, args.job_id)
    process = subprocess.Popen(f"conda run -n CompGenWeb python pipeline2.py -j {args.job_id} -d {pathlib.Path('/home/team1/webserver/DB')} -t {args.threads}".split(), stdout=2)
    process.wait()

    zip_output(args.job_id)
    if args.email_id:
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login('team1.webserver@gmail.com', 'wqchfqkllhclmxgo')
        email = MIMEMultipart()
        #msg.set_content("dsadasdasa")
        email['Subject'] = f"Predictive Webserver Team 1 results for job ID - {args.job_id}"
        email['From'] = 'team1.webserver@gmail.com'
        email['To'] = args.email_id
        body = "Your results are attached below"
        email.attach(MIMEText(body, 'plain'))
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f'jobs/{args.job_id}/job_results.zip', "rb").read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="job_results.zip"')
        email.attach(part)
        text = email.as_string()
        s.sendmail('team1.webserver@gmail.com', args.email_id, text)
        s.quit()
