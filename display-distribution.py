import subprocess
import sys, getopt
import re

# Dictionnary to store the total size by ip node
size_by_ip_dict = {}

# Print size in a human readable way
def human_readable_size(size):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(size) < 1024.0:
            return "%3.1f%s%s" % (size, unit, ' B')
        size /= 1024.0
    return "%.1f%s%s" % (size, 'Y', ' B') #Should never happen

# Sum the given block_size to the ip entry in the size_by_ip_dict
def update_size_by_ip_dict(ip, block_size):
    if ip not in size_by_ip_dict.keys(): 
        size_by_ip_dict[ip] = block_size
    else:
        size_by_ip_dict[ip] += block_size

def main(argv):
    path = argv
    #path = sys.argv[1]

    # Call the hdfs fsck command
    out = subprocess.Popen(['hdfs', 'fsck', path, '-files' ,'-blocks', '-locations'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout,stderr = out.communicate()
    lines = stdout.decode("utf-8").split("\n")
    # Filter the lines corresponding to a HDFS block information
    hdfs_block_lines = [line for line in lines if "DatanodeInfoWithStorage" in line]

    # Regex to get the length and replication factor of a HDFS block
    regex_len_rep = r'.*len=(\d*).*repl=(\d*).*'

    for hdfs_block_line in hdfs_block_lines:
        match_object_len_rep = re.match(regex_len_rep, hdfs_block_line)
        block_size = int(match_object_len_rep.group(1))
        replication_factor = int(match_object_len_rep.group(2))
        # Regex to get all the ips on which a HDFS block is present
        regex_ips = r'.*' + '.*DatanodeInfoWithStorage\[([\w.]*)' * replication_factor
        match_object_ips = re.match(regex_ips, hdfs_block_line)
        for i in range(0, replication_factor): 
            ip = match_object_ips.group(i + 1)
            update_size_by_ip_dict(ip, block_size)

    total_size = 0
    # Calculate the total size
    for ip, size in size_by_ip_dict.items():
        total_size += size

    print("Total size = ", human_readable_size(total_size))
    print("Data by node")
    sorted_size_by_ip_list = sorted(size_by_ip_dict.items(), key=lambda x: x[1])
    # Print the size by node sorted by size
    for ip, size in sorted_size_by_ip_list:
        print(ip, ":", human_readable_size(size), "(", "%.2f" % (size / total_size * 100), "%)")

if __name__ == "__main__":
   # Source:
   # https://medium.com/@robinjeanr/simple-script-to-display-the-data-distribution-on-hdfs-files-4120724fa602
   #main(sys.argv[1:])
   main("/project/data_clean")