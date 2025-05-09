import yaml
import requests
import time
from collections import defaultdict

# import logging, csv

import json
import logging
import aiohttp
import asyncio
from aiohttp import ClientError, ClientTimeout


# Function to load configuration from the YAML file
def load_config(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)         ## Exception handling for file errors DONE
    except Exception as e:
        print(f"Error loading configuration file '{file_path}': {e}")
        sys.exit(1)
    
# Function to perform health checks
async def check_health(endpoint, session, timeout=0.5):
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("monitor.log"),
            logging.StreamHandler()
        ]
    )

    url = endpoint['url']                         # Always present  !
    method = endpoint.get('method', 'GET')        # Default to GET if not present !
    headers = endpoint.get('headers', {})         # Default to empty headers !
    body = endpoint.get('body')                   # Optional, can be None !
    # raw_body = endpoint.get('body')
    json_body = json.loads(body) if isinstance(body, str) else body
    # print (method, url , headers, body)

    try:
        
        # response = requests.request(method, url, headers=headers, json=body, timeout =0.5)  # Check for respose time < 500 !
        async with session.request(method, url, headers=headers, json=json_body, timeout=timeout) as response:
         
            if 200 <= response.status < 300:
                return "UP"
            else:
                return "DOWN"
    except asyncio.TimeoutError:
        # logging.error(f"Timeout reached for {url}")
        return "DOWN"
    except Exception as e:
        # logging.error(f"Error occurred while checking {url}: {str(e)}")
        return "DOWN"




async def monitor_endpoints(file_path):              
    config = load_config(file_path)
    domain_stats = defaultdict(lambda: {"up": 0, "total": 0})

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("monitor.log"),
            logging.StreamHandler()
        ]
    )

    while True:
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for endpoint in config:
                tasks.append(check_health(endpoint, session))   

            results = await asyncio.gather(*tasks)

            for idx, result in enumerate(results):
                domain = config[idx]["url"].split("//")[-1].split("/")[0].split(":")[0]  # Extract domain (without port)
                domain_stats[domain]["total"] += 1
                
                if result == "UP":
                    domain_stats[domain]["up"] += 1

            # Log cumulative availability percentages
            for domain, stats in domain_stats.items():
                # print (domain, stats)
                availability = round(100 * stats["up"] / stats["total"])
                logging.info(f"{domain} has {availability}% availability percentage")

        # logging.info("---")
        elapsed = time.time() - start_time
        if elapsed < 15:
            await asyncio.sleep(15 - elapsed)
    

# Entry point of the program
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python monitor.py <config_file_path>")
        sys.exit(1)

    config_file = sys.argv[1]
    try:
        asyncio.run(monitor_endpoints(config_file))
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")



# # Main function to monitor endpoints.
def monitor_endpoints(file_path):              
#     config = load_config(file_path)
#     domain_stats = defaultdict(lambda: {"up": 0, "total": 0})

#     with open("availability_log.csv", mode='a', newline='') as file:
#         writer = csv.writer(file)

#         while True:
#             for endpoint in config:
#                 domain = endpoint["url"].split("//")[-1].split("/")[0].split(":")[0]  # Split for ports as well (Done)
#                 result = check_health(endpoint)

#                 domain_stats[domain]["total"] += 1
#                 if result == "UP":
#                     domain_stats[domain]["up"] += 1
                
#                 writer.writerow([endpoint["url"], result, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])  ## Writing to CSV this way can help easily understand hisotrical events. We can aggregate using other function or this csv can be read using visualisation tool and aggregating there.  

#             # Log cumulative availability percentages
#             for domain, stats in domain_stats.items():
#                 availability = round(100 * stats["up"] / stats["total"])
#                 print(f"{domain} has {availability}% availability percentage")          ## Save the log to a file or DB

#             print("---")
#             time.sleep(15)

    pass