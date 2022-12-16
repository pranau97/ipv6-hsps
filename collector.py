import pybgpstream

# create a new bgpstream instance and a reusable bgprecord instance
stream = pybgpstream.BGPStream(
    from_time="2022-08-01 16:00:00",
    until_time="2022-08-01 16:00:00",
    collectors=["rrc01"],
    record_type="ribs",
    filter="prefix exact 2001:4489:70a:104::/124",
)

for rec in stream.records():
    for elem in rec:
        print(elem)
