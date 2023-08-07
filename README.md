# Team1-WebServer

## Webserver URL
http://team1.bioapp721023.biosci.gatech.edu/  
_*Currently access is limited to Georgia Tech networks_

## Overview
Our webserver takes in E.coli paired-end Illumina reads and performs genome assembly, gene prediction, and comparative genomics analyses.

### Input
* Zip file of one or more E. coli Illumina read-pairs

### Output
* Pre- and Post-Assembly evaluation of read-pairs as HTML pages
* GFF, FNA, and FAA files of predicted genes
* ANI clustermap of submitted sequences and our internal E. coli isolate database
* Phylogenetic tree of submitted sequences and internal database against an NCBI reference genome

## Webserver Functions

### Genome Assembly
    Pre-Assembly QC & Trimming | Tool: FastP
      - Perform quality trimming, adapter trimming, and base correction of raw Illumina paired-end reads
      
    Assembly | Tool: SPAdes
      - Assembles your trimmed reads into contigs of the bacterial genome
      
    Post-Assembly QC | Tool: Quast
    
    Quality Assessment | Tool: MultiQC
      - Aggregates quality control metrics across all the uploaded samples into Pre-Assembly and Post-Assembly HTML pages

### Gene Prediction
    Gene Prediction | Tool: Prodigal
      - Predicts genes from assembled contigs and output GFF, FNA, and FAA files for the user's downstream needs

### Comparative Genomics
     Whole Genome Analysis | Tool: ANIclustermap
      - Creates an all-against-all Average Nucleotide Identity clustermap of the user's assembled genomes with our internal database of 50 E. coli isolates
      
     SNP Analysis | Tools: Parsnp & Figtree
      - Creates a phylogenetic tree of the user's assembled genomes and our internal database against an NCBI E. coli reference genome

## Webserver Architecture
### Front-End Server | Tool: NGINX
* A high-performance reverse proxy server designed for optimal load-balancing in high-traffic situations

### Application Server | Tool: Gunicorn
* A necessary intermediary between the front-end and Python-based back-end servers using WSGI protocol

### Back-End Server | Tool: Django
* A Python-based web application framework designed to run our bioinformatics pipeline while being easy for intro-level developers

### Running the Webserver for the Developer
Make sure that both front-end and back-end servers are running so that the domain always works.  

To run NGINX:  
`sudo systemctl start nginx`  

To run Gunicorn/Django:  
`gunicorn -c gunicorn_config.py webserver.wsgi`  
