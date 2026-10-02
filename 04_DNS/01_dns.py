import argparse
import dns.resolver

parser = argparse.ArgumentParser(description="DNS record lookup")
parser.add_argument("--hostname", required=True, help="Hostname to query")
args = parser.parse_args()

hostname = args.hostname

for type in ["A", "MX", "CNAME", "NS","AAAA", "NSEC", "PTR", "SOA"]:
    try:
        result = dns.resolver.resolve(hostname, type)
        # Printing record
        print(f" ====== {type} =======")
        for val in result:
            print(f'{type} Record : {val.to_text()} (TTL: {result.rrset.ttl})')
    except:
        continue