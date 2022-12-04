import pytricia
from ipaddress import ip_network
import matplotlib.pyplot as plt

# from tqdm import tqdm

print("Reading & processing datasets...", end="")
with open("parsed_data/rrc01.20220801.1600_parse.txt") as infile:
    routes = [tuple(route.rstrip().split()) for route in infile if route.rstrip()]

with open("parsed_data/arin") as infile:
    arin_whois = [ip.rstrip() for ip in infile if ip.rstrip()]

with open("parsed_data/afrinic") as infile:
    afrinic_whois = [ip.rstrip() for ip in infile if ip.rstrip()]

with open("parsed_data/apnic") as infile:
    apnic_whois = [ip.rstrip() for ip in infile if ip.rstrip()]

with open("parsed_data/ripe") as infile:
    ripe_whois = [ip.rstrip() for ip in infile if ip.rstrip()]

with open("parsed_data/responsive-addresses.txt") as infile:
    responsive_ips = [ip.rstrip() for ip in infile if ip.rstrip()]
print("Done.")


print("Building prefix tree from RRC route data...", end="")
prefix_dict = {}
rrc_pyt = pytricia.PyTricia(128)
routes_ipv6 = [route for route in routes if ip_network(route[0]).version == 6]
hsps = {}
# iterate over ipv6 routes and build pytricia tree for non-hsp routes
for prefix in routes_ipv6:
    prefix_dict[ip_network(prefix[0])] = prefix[1]
    if ip_network(prefix[0]).prefixlen <= 48:  # > /48 is HSP
        rrc_pyt[prefix[0]] = prefix[1].split("/")  # larger routes go to tree
    else:
        hsps[prefix[0]] = prefix[1].split("/")  # hsp routes go to dict
print("Done.")

print("Computing longest prefix match for HSPs using route data...", end="")
# iterate over hsp routes and check if they are contained in the tree
lpm = {}  # store the longest prefix match for an hsp
for hsp in hsps.keys():
    if hsp in rrc_pyt:
        lpm[ip_network(hsp)] = ip_network(rrc_pyt.get_key(hsp))
    else:
        raise ValueError("HSP not found in tree.")
print("Done.")

print("Building prefix tree from WHOIS data...", end="")
whois_records = arin_whois + afrinic_whois + apnic_whois + ripe_whois
whois_assignment = {}  # store the whois record for each hsp
whois_pyt = pytricia.PyTricia(128)
# iterate over whois records and try to match them with the hsp prefixes
for idx, whois in enumerate(whois_records):
    whois_pyt[whois] = idx
print("Done.")

# TODO: Check the max prefixlen of whois records

print("Computing longest prefix match for HSPs using WHOIS data...", end="")
for hsp in hsps.keys():
    if hsp in whois_pyt:
        whois_assignment[ip_network(hsp)] = ip_network(whois_pyt.get_key(hsp))
    else:
        raise ValueError("HSP not found in tree.")
print("Done.")

print("Getting the location of each HSP...", end="")
# Assigning a location to each HSP
rir_map = {
    "arin": "North America",
    "afrinic": "Africa",
    "apnic": "Asia Pacific",
    "ripe": "Europe & Middle East",
    "err": "Error",
}
hsp_location = {}
hsp_location_error = 0
for hsp, whois in whois_assignment.items():
    if str(whois) in arin_whois:
        hsp_location[hsp] = rir_map["arin"]
    elif str(whois) in afrinic_whois:
        hsp_location[hsp] = rir_map["afrinic"]
    elif str(whois) in apnic_whois:
        hsp_location[hsp] = rir_map["apnic"]
    elif str(whois) in ripe_whois:
        hsp_location[hsp] = rir_map["ripe"]
    else:
        hsp_location_error += 1
        hsp_location[hsp] = rir_map["err"]
print("Done.")
print(f"Number of HSPs with unknown location - {hsp_location_error}")

print("Plotting CDFs of HSPs and LPMs...", end="")
# Plot CDFs of HSP and LPM prefix lengths
hsp_prefixlen = [hsp.prefixlen for hsp in lpm.keys()]
lpm_prefixlen = [lpm[hsp].prefixlen for hsp in lpm.keys()]
range = range(0, 129)
plt.hist(
    hsp_prefixlen,
    bins=range,
    density=True,
    cumulative=True,
    histtype="step",
    label="HSP",
)
plt.hist(
    lpm_prefixlen,
    bins=range,
    density=True,
    cumulative=True,
    histtype="step",
    label="LPM",
)
plt.legend(loc="lower right")
plt.xlabel("Prefix length")
plt.ylabel("CDF")
plt.title("CDF of HSP and LPM prefix lengths")
# plt.show()
print("Done.")

print("Finding active IP addresses for each HSP/LPM...", end="")
# reverse the lpm dict
lpm_reverse = {}
for hsp, lpm in lpm.items():
    if lpm in lpm_reverse:
        lpm_reverse[lpm].append(hsp)
    else:
        lpm_reverse[lpm] = [hsp]

active_ips = {}
lpm_pyt = pytricia.PyTricia(128)
for hsp, lpm in lpm.items():
    lpm_pyt[lpm] = hsp

for ip in responsive_ips:
    if ip in lpm_pyt:
        lpm = lpm_pyt.get_key(ip)
        if lpm not in active_ips:
            active_ips[lpm] = []
        active_ips[lpm].append(ip)
    else:
        raise ValueError("IP not found in tree.")
print("Done.")

with open("sample.txt", "w") as outfile:
    for key, value in whois_assignment.items():
        outfile.write(f"{key} {value}\n")
