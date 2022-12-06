# add ::1 to a list of ipv6 networks
from ipaddress import ip_network

with open("parsed_data/rrc01.20220801.1600_parse.txt") as infile:
    routes = [tuple(route.rstrip().split()) for route in infile if route.rstrip()]

routes_ipv6 = [route for route in routes if ip_network(route[0]).version == 6]
address_list = []
for prefix in routes_ipv6:
    if ip_network(prefix[0]).prefixlen <= 48:  # > /48 is HSP
        pass
    else:
        try:
            address_list.append(
                ip_network(prefix[0])[1]
            )  # get the first address of the hsp
        except IndexError:
            print(f"IndexError: {prefix[0]}")
            address_list.append(ip_network(prefix[0]).network_address)

with open("results/ipv6_hsp_addresses.txt", "w") as outfile:
    for address in address_list:
        outfile.write(f"{str(address)}\n")
