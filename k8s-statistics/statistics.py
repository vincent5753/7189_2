import os, time, resource, re
from kubernetes import client, config

mode = os.environ.get("mode", "node")
interval = int(os.environ.get("interval", 10))
print("[INFO][INIT]: Running in " + mode + " mode")
print("[INFO][INIT]: " + str(interval) + " seconds time interval")
print("")

config.load_incluster_config()

def get_node_statistics():

    v1 = client.CoreV1Api()
    ret = v1.list_node(watch=False)

    allocatable = dict()
    capacity = dict()

    for node in ret.items:
        for resources in ["cpu", "ephemeral-storage", "hugepages-1Gi", "hugepages-2Mi", "memory", "pods", "nvidia.com/gpu"]:
          if resources in node.status.capacity.keys():
              if resources == "cpu":
                  allocatable[resources] = allocatable.get("cpu", 0) + int(node.status.allocatable["cpu"])
                  capacity[resources] = capacity.get("cpu", 0) + int(node.status.capacity["cpu"])
              if resources == "ephemeral-storage":
                  allocatable[resources] = allocatable.get("ephemeral-storage", 0) + int(node.status.allocatable["ephemeral-storage"])
                  capacity[resources] = capacity.get("ephemeral-storage", 0) + int(node.status.capacity["ephemeral-storage"].replace("Ki",""))
              if resources == "hugepages-1Gi":
                  allocatable[resources] = allocatable.get("hugepages-1Gi", 0) + int(node.status.allocatable["hugepages-1Gi"])
                  capacity[resources] = capacity.get("hugepages-1Gi", 0) + int(node.status.capacity["hugepages-1Gi"])
              if resources == "hugepages-2Mi":
                  allocatable[resources] = allocatable.get("hugepages-2Mi", 0) + int(node.status.allocatable["hugepages-2Mi"])
                  capacity[resources] = capacity.get("hugepages-2Mi", 0) + int(node.status.capacity["hugepages-2Mi"])
              if resources == "memory":
                  allocatable[resources] = allocatable.get("memory", 0) + int(node.status.allocatable["memory"].replace("Ki",""))
                  capacity[resources] = capacity.get("memory", 0) + int(node.status.capacity["memory"].replace("Ki",""))
              if resources == "pods":
                  allocatable[resources] = allocatable.get("pods", 0) + int(node.status.allocatable["pods"])
                  capacity[resources] = capacity.get("pods", 0) + int(node.status.capacity["pods"])
              if resources == "nvidia.com/gpu":
                  allocatable[resources] = allocatable.get("nvidia.com/gpu", 0) + int(node.status.allocatable["nvidia.com/gpu"])
                  capacity[resources] = capacity.get("nvidia.com/gpu", 0) + int(node.status.capacity["nvidia.com/gpu"])  
          else:
              pass

    print("<allocatable>")
    print(allocatable)
    print("")
    print("<capacity>")
    print(capacity)
    print("")

def get_pod_statistics():
    print("pod")

    with open("excludeapp.list", "r") as f:
        excludeapp = f.read().splitlines()
        print(excludeapp)

    class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False)

    company_dict = dict()
    cpusum=0
    memsum=0
    gpusum=0


    for pod in ret.items:
        if pod.metadata.labels.get('app'):
            if pod.metadata.labels.get('app') in excludeapp:
                break
        print(str(pod.status.pod_ip)+" " + str(pod.metadata.namespace) + " " +str(pod.metadata.name) + " " + bcolors.OKBLUE + str(pod.metadata.labels) + bcolors.ENDC)
        print(str(pod.metadata.name))
        print(str(pod.spec.containers[0].resources.requests))

        if pod.spec.containers[0].resources.requests is None:
            print(bcolors.FAIL +"None" + bcolors.ENDC)
            break
        else:
            print(bcolors.OKGREEN + str(pod.spec.containers[0].resources.requests) + bcolors.ENDC)
            if "cpu" in pod.spec.containers[0].resources.requests:
                company_id = pod.metadata.labels.get('company_id')
                print(bcolors.OKCYAN + "cpu" + bcolors.ENDC)
                cpuusage=pod.spec.containers[0].resources.requests.get('cpu')
                print(bcolors.WARNING + cpuusage + bcolors.ENDC)

                regex = r"^\d*$"
                if re.match(regex,cpuusage):
                    cpuusum = cpusum + int(cpuusage)*1000
                    print("CPU整數")
                    if company_id in company_dict.keys():
                        company_dict[company_id]["cpu"] = company_dict[company_id].get("cpu") + int(cpuusage)*1000
                        company_dict[company_id].get("cpu")
                        print(int(cpuusage)*1000)
                    else:
                        print(int(cpuusage)*1000)
                        company_dict[company_id] = {
                            "cpu": int(cpuusage)*1000
                        }
                    print(company_dict)

                regex = r"^\d*m$"
                if re.match(regex,cpuusage):
                    cpusum = cpusum + int(cpuusage.replace('m',''))
                    print("CPU m")
                    if company_id in company_dict.keys():
                        company_dict[company_id]["cpu"] = company_dict[company_id].get("cpu", 0) + int(cpuusage.replace('m',''))
                        company_dict[company_id].get("cpu", 0)
                        print(int(cpuusage.replace('m','')))
                    else:
                        company_dict[company_id] = {
                            "cpu": int(cpuusage.replace('m',''))
                        }
                        print(int(cpuusage.replace('m','')))
                    print(company_dict)

            if "memory" in pod.spec.containers[0].resources.requests:
                company_id = pod.metadata.labels.get('company_id')
                print(bcolors.OKCYAN + "memory" + bcolors.ENDC)
                memusage=pod.spec.containers[0].resources.requests.get('memory')
                print(bcolors.WARNING + memusage + bcolors.ENDC)
                print(str(bcolors.OKBLUE + str(pod.metadata.labels) + bcolors.ENDC))

                regex = r"^\d*$"
                if re.match(regex,memusage):
                    print(bcolors.FAIL + "Byte" + bcolors.ENDC)
                    print("Byte: " + memusage )
                    memsum=memsum+int(memusage)
                    if company_id in company_dict.keys():
                        company_dict[company_id]["mem"] = company_dict[company_id].get("mem", 0) + int(memusage)
                        company_dict[company_id].get("mem", 0)
                    else:
                        company_dict[company_id] = {
                        "mem": int(memusage)
                        }
                    print(company_dict)

                regex = r"^\d+e\d*$"
                if re.match(regex,memusage):
                    print(bcolors.FAIL + "e" + bcolors.ENDC)
                    num=(memusage.split("e")[0])
                    enum=(memusage.split("e")[1])

                    print("Byte: " + str(str(num)+str(0)*int(enum)))
                    memsum=memsum+int(str(str(num)+str(0)*int(enum)))
                    if company_id in company_dict.keys():
                        company_dict[company_id]["mem"] = company_dict[company_id].get("mem", 0) + int(str(str(num)+str(0)*int(enum)))
                        company_dict[company_id].get("mem", 0)
                    else:
                        company_dict[company_id] = {
                            "mem": int(str(str(num)+str(0)*int(enum)))
                        }
                    print(company_dict)

                regex = r"^\d*M$"
                if re.match(regex,memusage):
                    print(bcolors.FAIL + "M" + bcolors.ENDC)
                    print(memusage)
                    print("Byte: " + str(int(memusage.replace('M',''))*1000*1000))
                    memsum=memsum+int(memusage.replace('M',''))*1000*1000
                    if company_id in company_dict.keys():
                        company_dict[company_id]["mem"] = company_dict[company_id].get("mem", 0) + int(memusage.replace('M',''))*1000*1000
                        company_dict[company_id].get("mem", 0)
                    else:
                        company_dict[company_id] = {
                        "mem": int(memusage.replace('M',''))*1000*1000
                        }
                    print(company_dict)

                regex = r"^\d+m$"
                if re.match(regex,memusage):
                    print(bcolors.FAIL + "m" + bcolors.ENDC)
                    print("Byte: " + str(int(memusage.replace('000m',''))))
                    memsum=memsum+int(memusage.replace('000m',''))
                    if company_id in company_dict.keys():
                        company_dict[company_id]["mem"] = company_dict[company_id].get("mem", 0) + int(memusage.replace('000m',''))
                        print(company_dict[company_id].get("mem", 0))
                    else:
                        company_dict[company_id] = {
                            "mem": int(memusage.replace('000m',''))
                        }
                    print(company_dict)

                regex = r"^\d+Mi$"
                if re.match(regex,memusage):
                    print(bcolors.FAIL + "Mi" + bcolors.ENDC)
                    print("Byte: " + str(int(memusage.replace('Mi',''))*1024*1024))
                    memsum=memsum+int(memusage.replace('Mi',''))*1024*1024
                    if company_id in company_dict.keys():
                        company_dict[company_id]["mem"] = company_dict[company_id].get("mem", 0) + int(memusage.replace('Mi',''))*1024*1024
                        company_dict[company_id].get("mem", 0)
                    else:
                        company_dict[company_id] = {
                            "mem": int(memusage.replace('Mi',''))*1024*1024
                        }
                    print(company_dict)

                regex = r"^\d+Gi$"
                if re.match(regex,memusage):
                    print(bcolors.FAIL + "Gi" + bcolors.ENDC)
                    print("Byte: " + str(int(memusage.replace('Gi',''))*1024*1024*1024))
                    memsum=memsum+int(memusage.replace('Gi',''))*1024*1024*1024
                    if company_id in company_dict.keys():
                        company_dict[company_id]["mem"] = company_dict[company_id].get("mem", 0) + int(memusage.replace('Gi',''))*1024*1024*1024
                    else:
                        company_dict[company_id] = {
                            "mem": int(memusage.replace('Gi',''))*1024*1024*1024
                        }
                    print(company_dict)
                print("")

            if "nvidia.com/gpu" in pod.spec.containers[0].resources.requests:
                company_id = pod.metadata.labels.get('company_id')
                print(bcolors.OKCYAN + "gpu" + bcolors.ENDC)
                gpuusage=pod.spec.containers[0].resources.requests.get('nvidia.com/gpu')
                gpusum = gpusum + int(gpuusage)
                print(bcolors.WARNING + gpuusage + bcolors.ENDC)
                if company_id in company_dict.keys():
                    company_dict[company_id]["gpu"] = company_dict[company_id].get("gpu", 0) + int(gpuusage)
                    company_dict[company_id].get("gpu", 0)
                    print(int(gpuusage))
                else:
                    company_dict[company_id] = {
                        "gpu": int(gpuusage)
                    }
                    print(int(gpuusage))
                print(company_dict)
                print("")

    print("<Summary>")
    print("CPU usage in m: " + str(cpusum) + "m")
    print("CPU usage in number: "+ str(cpusum/1000))
    print("")

    print("Memory usage in byte:"+str(memsum))
    print("Memory usage in GiB:"+str(memsum/1024/1024/1024))
    print("")

    print("GPU usage in number: "+str(gpusum))
    print("")

    print("<Companies>")
    print(company_dict.keys())
    print("")

    print("<Detailed usage>")
    for key in company_dict.keys():
        print("CPU usage for: " + str(key) +" in m")
        print(str(company_dict[key].get("cpu", 0))+"m")
        print("")
        print("CPU usage for: " + str(key) +" in number")
        print(int(company_dict[key].get("cpu", 0))/1000)
        print("")

        print("Memory used for " + str(key) +" in bytes")
        print(company_dict[key].get("mem", 0))
        print("")
        print("Memory used for " + str(key) +" in GiBs")
        print(int(company_dict[key].get("mem", 0))/1024/1024/1024)
        print("")

        print("GPU usage for: " + str(key))
        print(str(company_dict[key].get("gpu", 0)))
        print("")
        print("")

while True:

    if mode == "node":
        get_node_statistics()
    else:
        get_pod_statistics()

    time.sleep(interval)
