# How to install and run the code
- Install python on a machine 
- Have both main.py and sample.yml in same directory
- Execute python main.py sample.yml
- Output gets displayeed to screen and also saves to monitor.log which is saved in the same folder

# Changes made to the script

### Import necessary packages for implementing additional changes

```python
import json         # To parse json objects
import logging      # To log data 
import asyncio      #  To run asynchronous code
import aiohttp      # To make asynchronous HTTP requests
from aiohttp import ClientError, ClientTimeout      
# Exception for request-related issues and to set custom timeouts for requests
```

## Make the code to run asynchronously to run on large number of nodes simultaneously

Python using a sequential execution can only monitor for 30 endpoints which are down in 15 secs interval. Making wach http request asynchronously we can run on thousands of endpoints in ~500ms only. 

- Correct the parsing of yml files. Earlier default values were not available and error while passing json
- Add the timeout to be less than 500ms ( It was not there)
- Asynchronously checnk for the start of different endpoint

### Function to perform health checks
``` python
async def check_health(endpoint, session, timeout=2.5):
    url = endpoint['url']                         # Always present  
    method = endpoint.get('method', 'GET')        # Default to GET if not present
    headers = endpoint.get('headers', {})         # Default to empty headers
    body = endpoint.get('body')                   # Optional
    
    json_body = json.loads(body) if isinstance(body, str) else body     # Convert the body to json object if it is available
    
    try:
        # response = requests.request(method, url, headers=headers, json=body, timeout =0.5)  # Check for respose time < 500 !
        async with session.request(method, url, headers=headers, json=json_body, timeout=timeout) as response:
            
            if 200 <= response.status < 300:
                return "UP"
            else:
                return "DOWN"
    except asyncio.TimeoutError:
        return "DOWN"
    except Exception as e:
        return "DOWN"
```

## Make the monitoring function to make use of asynchronus health checks

- Run asynchronously on all the endpoints  
- Define the logging configuration
- Log as info the availability with timestamp
- Remove  the port number from domain as well
- Als taking timeout into account of sleep time, let's say if we can relax to larger timeouts which becomes significant comparable to frequency at which we monitor

### Main function to monitor endpoints
```python
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
                availability = round(100 * stats["up"] / stats["total"])
                logging.info(f"{domain} has {availability}% availability percentage")

        
        elapsed = time.time() - start_time
        if elapsed < 15:
            await asyncio.sleep(15 - elapsed)

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

```

## Other Considerations
Above code changes make the execution of the monitoring scripts meet the given requirements. But we can modify this to meet other requirements which can help improve the application which is monitored.

We can log for each of the URL if we need to check for individual endpoint status at some point of time in history.
Following this format `<URL> - <status> - <timestamp>` and saving them to a database or CSV, we can aggregate using other functions or read using visualisation tool and aggregating there. We can run it asynchronously for a large number 


```python
def monitor_endpoints(file_path):              
    config = load_config(file_path)
    domain_stats = defaultdict(lambda: {"up": 0, "total": 0})

    with open("availability_log.csv", mode='a', newline='') as file:
        writer = csv.writer(file)

        while True:
            for endpoint in config:
                domain = endpoint["url"].split("//")[-1].split("/")[0].split(":")[0]  
                result = check_health(endpoint)

                domain_stats[domain]["total"] += 1
                if result == "UP":
                    domain_stats[domain]["up"] += 1
                
                writer.writerow([endpoint["url"], result, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]) 
            for domain, stats in domain_stats.items():
                availability = round(100 * stats["up"] / stats["total"])
                print(f"{domain} has {availability}% availability percentage")     

            print("---")
            time.sleep(15)
```



