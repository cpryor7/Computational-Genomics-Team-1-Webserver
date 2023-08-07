from django.shortcuts import render
import random
import subprocess
from django.http import FileResponse, HttpResponse
import glob
from django.contrib import messages
import json
from django.shortcuts import render
import os
from django.views.decorators.csrf import csrf_exempt


JOB_NAME_LENGTH = 8
# Create your views here.
@csrf_exempt 
def landpage(request):
    return render(request, 'index.html', {})
@csrf_exempt 
def submitpage(request, job_id = None):
    return render(request, 'result.html', {'job_id': job_id})
@csrf_exempt 
def jobpage(request, job_id = None):
    return render(request, 'job.html', {'job_id': job_id})
@csrf_exempt 
def get_data(request):
    job_name = str(random.randrange(10 ** (JOB_NAME_LENGTH-1), 10 ** JOB_NAME_LENGTH))
    subprocess.run(['mkdir', '-p', f'jobs/{job_name}/'])
    flag = 0
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        zip_file = str(job_name)+".zip"
        with open(f'jobs/{job_name}/{request.FILES["zip_file"].name}', 'wb') as fp:
            fp.write(request.FILES['zip_file'].read())
        subprocess.run(['unzip', f'jobs/{job_name}/{request.FILES["zip_file"].name}', '-d', f'jobs/{job_name}/'])
        subprocess.run(['rm', f'jobs/{job_name}/{request.FILES["zip_file"].name}'])
        with open(f'jobs/{job_name}/job_summary.txt', 'w') as fp1:
            with open(f'jobs/{job_name}/job_log.log', 'w') as fp2:
                subprocess.Popen(['python', 'pipeline.py', '-j', job_name, '-d', f'jobs/{job_name}/{request.FILES["zip_file"].name[:-4]}/', '-e', request.POST['email_id']], stdout=fp1, stderr=fp2)

    return submitpage(request, job_name)#render(request, 'result.html', {'job_id': job_name})
@csrf_exempt 
def get_results(request):
    valid_ids = [int(x.split('/')[-1]) for x in glob.glob('jobs/*')]
    print(valid_ids, int(request.POST['job_id']))
    if request.method == 'POST':
        if int(request.POST['job_id']) not in valid_ids:
            messages.info(request, f"Input job ID - '{request.POST['job_id']}' is invalid.")
            return render(request, 'job.html', {'job_id': request.POST['job_id'], 'valid': False})
        else:
            with open(f"jobs/{request.POST['job_id']}/job_status.json", 'r') as f:
                job_status = json.loads(f.read())
            return render(request, 'job.html', {'job_id': request.POST['job_id'], 'status': job_status})
@csrf_exempt 
def show_output(request):
    result = request.GET.get('result', None)
    job_id = request.GET.get('job_id', None)
    if result == "fastp":
        return render(request, f'{job_id}_pre_assembly_qc.html')
    elif result == "spades":
        return render(request, f'{job_id}_spades_post_assembly_qc.html')
    elif result == "anicluster":
        return render(request, f'ANIclustermap.png')
