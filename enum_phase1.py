#!/usr/bin/env python3

import subprocess
import argparse

# Function to run the command
def run_command(command):
    print(f"Running command: {command}")
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print("Output:")
            print(result.stdout)
        else:
            print(f"Error:\n{result.stderr}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def flags():
	# Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="""enum_phase.py is a wrapper that combines tools as amass, subfinder, assterfinder, anew and httpx to perform a subdomain enumeration. 
    												Do not forget to put your datasources.yaml of amass and provider-config.yaml of subfinder in the same directory as the script.""")
	# Add an argument of input file
    parser.add_argument("-i", "--input-file", required=True, help="Input file to process.")
    # Add working directory
    parser.add_argument("-d", "--directory", required=True, help="Input the directory to work, can be relative or absolute.")
    # Define the $HOME directory
    home_dir = run_command('echo $HOME')
    # Specify datasource.yaml file location
    parser.add_argument("-a", "--amass-file", default=f'{home_dir}/.config/amass/datasources.yaml', required=False, help="Input the directory where the amass datasource.yaml file is located")
    # Specify the provider-config.yaml file location
    parser.add_argument("-s", "--subfinder-file", default=f'{home_dir}/.config/subfinder/provider-config.yaml', required=False, help="Input the directory where the subfinder provider-config.yaml file is located.")
	# Parse the command-line arguments
    args = parser.parse_args()
	# Access the values of the parsed arguments
    input_file = args.input_file
    directory = args.directory
    amass_file = args.amass_file
    subfinder_file = args.subfinder_file
    return input_file, directory, amass_file, subfinder_file

# Function to download latest resolvers
def download_resolvers(workdir):
      run_command(f'wget -P {workdir} https://raw.githubusercontent.com/trickest/resolvers/main/resolvers.txt')

# Function to run amass and parse result into amass_parsed.txt
def run_amass(domains, workdir, amass_loc):
    run_command(f"amass enum -df {domains} -config {amass_loc} -rf {workdir}/resolvers.txt --passive -o {workdir}/amass_raw.txt")
    run_command(f"cat {workdir}/amass_raw.txt | grep 'cname' | sort -u > {workdir} amass_cnames.txt")
    run_command(f"cat {workdir}/amass_raw.txt | grep '(IPAddress)' | cut -d '>' -f3 | cut -d ' ' -f2 | sort -u > amass_ipaddress.txt")
    run_command(f"cat {workdir}/amass_raw.txt | grep '/' | cut -d '-' -f1 | grep '/' | cut -d ' ' -f1 | sort -u > amass_netblock.txt")
    run_command(f"cat {workdir}/amass_raw.txt | grep ASN | sort -u > amass_asn.txt")
    run_command(f'cat {workdir}/amass_raw.txt | grep "(FQDN)" | cut -d " " -f 1 | sort -u > {workdir}/amass_subdomains.txt')

# Function to run amass and parse result into amass_parsed.txt
def run_subfinder(domains, workdir, subfinder_loc):
	run_command(f"subfinder -dL {domains} -pc {subfinder_loc}/provider-config.yaml -o {workdir}/subfinder.txt")

# Function to organize, sort and delete repeated subdoamins
def organize(workdir):
	run_command(f"cat {workdir}/subfinder.txt {workdir}/amass_subdomains.txt | sort -u | anew {workdir}/subdomains.txt")

# Function to notify on discord the new subdomains and post the new ones through notify.
def alive_subs(workdir):
    run_command(f"httpx -l {workdir}/subdomains.txt -sc -cl -title -td -o {workdir}/live_subdomains.txt -fc 400 | anew {workdir}/live_subdomains.txt | notify --silent")

# Function that calls all other functions to run all commands and then organize them. 
def run_sub_recon(domains, workdir, amass_file, subfinder_file):
    download_resolvers(workdir)
    run_amass(domains, workdir, amass_file)
    run_subfinder(domains, workdir, subfinder_file)
    organize(workdir)


# Main function that gets the two required flags, runs de subdoamins recon and then check for alive subdomains
if __name__ == "__main__":
    input_file, directory, amass, subfinder = flags()
    run_sub_recon(input_file, directory, amass, subfinder)
    alive_subs(directory)
