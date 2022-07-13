import os
import time
import re
from kubernetes import client, config

mode = os.environ.get("mode", "node")
interval = int(os.environ.get("interval", 10))
print("[INFO][INIT]: Running in " + mode + " mode")
print("[INFO][INIT]: " + str(interval) + " seconds time interval\n")

config.load_incluster_config()


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
                    capacity[resources] = capacity.get("ephemeral-storage", 0) + int(node.status.capacity["ephemeral-storage"].replace("Ki", ""))
                if resources == "hugepages-1Gi":
                    allocatable[resources] = allocatable.get("hugepages-1Gi", 0) + int(node.status.allocatable["hugepages-1Gi"])
                    capacity[resources] = capacity.get("hugepages-1Gi", 0) + int(node.status.capacity["hugepages-1Gi"])
                if resources == "hugepages-2Mi":
                    allocatable[resources] = allocatable.get("hugepages-2Mi", 0) + int(node.status.allocatable["hugepages-2Mi"])
                    capacity[resources] = capacity.get("hugepages-2Mi", 0) + int(node.status.capacity["hugepages-2Mi"])
                if resources == "memory":
                    allocatable[resources] = allocatable.get("memory", 0) + int(node.status.allocatable["memory"].replace("Ki", ""))
                    capacity[resources] = capacity.get("memory", 0) + int(node.status.capacity["memory"].replace("Ki", ""))
                if resources == "pods":
                    allocatable[resources] = allocatable.get("pods", 0) + int(node.status.allocatable["pods"])
                    capacity[resources] = capacity.get("pods", 0) + int(node.status.capacity["pods"])
                if resources == "nvidia.com/gpu":
                    allocatable[resources] = allocatable.get("nvidia.com/gpu", 0) + int(node.status.allocatable["nvidia.com/gpu"])
                    capacity[resources] = capacity.get("nvidia.com/gpu", 0) + int(node.status.capacity["nvidia.com/gpu"])
            else:
                pass

    print("<allocatable>")
    print(allocatable + "\n")
    print("<capacity>")
    print(capacity + "\n")


def get_pod_statistics():

    with open("excludeapp.list", "r") as f:
        excludeapp = f.read().splitlines()
        print("<excluded app list>")
        print(str(excludeapp) + "\n")

    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False)

    company_dict = dict()
    cpusum = 0
    memsum = 0
    gpusum = 0

    print("<RAW POD INFO>")
    for pod in ret.items:
        if pod.metadata.labels.get('app'):
            if pod.metadata.labels.get('app') in excludeapp:
                continue
            if pod.spec.containers[0].resources.requests is None:
                pass
            else:
                print("<POD INFO>")
                print(str(pod.status.pod_ip) + " " + str(pod.metadata.namespace) + " " + str(pod.metadata.name) + " " + bcolors.OKBLUE + str(pod.metadata.labels) + bcolors.ENDC)
                print("<Requested Resource>")
                print(bcolors.OKGREEN + str(pod.spec.containers[0].resources.requests) + bcolors.ENDC)
                if "cpu" in pod.spec.containers[0].resources.requests:
                    company_id = pod.metadata.labels.get('company_id')
                    project_id = pod.metadata.labels.get('project_id')
                    if not company_id:
                        continue
                    if not project_id:
                        continue
                    cpuusage = pod.spec.containers[0].resources.requests.get('cpu')

                    regex = r"^\d*$"
                    if re.match(regex, cpuusage):
                        cpuusum = cpusum + int(cpuusage)*1000
                        if company_id in company_dict.keys():
                            if project_id in company_dict[company_id].keys():
                                company_dict[company_id][project_id]["cpu"] = company_dict[company_id][project_id].get("cpu", 0) + int(cpuusage)*1000
                                company_dict[company_id][project_id].get("cpu")
                            else:
                                company_dict[company_id][project_id] = {}
                                company_dict[company_id][project_id]["cpu"] = company_dict[company_id][project_id].get("cpu", 0) + int(cpuusage)*1000
                                company_dict[company_id][project_id].get("cpu")
                        else:
                            company_dict[company_id] = {}
                            company_dict[company_id][project_id] = {}
                            company_dict[company_id][project_id]["cpu"] = company_dict[company_id][project_id].get("cpu", 0) + int(cpuusage)*1000

                    regex = r"^\d*m$"
                    if re.match(regex, cpuusage):
                        cpusum = cpusum + int(cpuusage.replace('m', ''))
                        if company_id in company_dict.keys():
                            if project_id in company_dict[company_id].keys():
                                company_dict[company_id][project_id]["cpu"] = company_dict[company_id][project_id].get("cpu", 0) + int(cpuusage.replace('m', ''))
                                company_dict[company_id][project_id].get("cpu", 0)
                            else:
                                company_dict[company_id][project_id] = {}
                                company_dict[company_id][project_id]["cpu"] = company_dict[company_id][project_id].get("cpu", 0) + int(cpuusage.replace('m', ''))
                                company_dict[company_id][project_id].get("cpu")
                        else:
                            company_dict[company_id] = {}
                            company_dict[company_id][project_id] = {}
                            company_dict[company_id][project_id]["cpu"] = company_dict[company_id][project_id].get("cpu", 0) + int(cpuusage.replace('m', ''))

                if "memory" in pod.spec.containers[0].resources.requests:
                    company_id = pod.metadata.labels.get('company_id')
                    project_id = pod.metadata.labels.get('project_id')
                    if not company_id:
                        continue
                    if not project_id:
                        continue

                    memusage = pod.spec.containers[0].resources.requests.get('memory')

                    regex = r"^\d*$"
                    if re.match(regex, memusage):
                        memsum = memsum + int(memusage)
                        if company_id in company_dict.keys():
                            if project_id in company_dict[company_id].keys():
                                company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(memusage)
                                company_dict[company_id][project_id].get("mem", 0)
                            else:
                                company_dict[company_id][project_id] = {}
                                company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(memusage)
                                company_dict[company_id][project_id].get("mem", 0)
                        else:
                            company_dict[company_id] = {}
                            company_dict[company_id][project_id] = {}
                            company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(memusage)
                            company_dict[company_id][project_id].get("mem", 0)

                    regex = r"^\d+e\d*$"
                    if re.match(regex, memusage):
                        num = (memusage.split("e")[0])
                        enum = (memusage.split("e")[1])
                        memsum = memsum + int(str(str(num) + str(0)*int(enum)))
                        if company_id in company_dict.keys():
                            if project_id in company_dict[company_id].keys():
                                company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                                company_dict[company_id][project_id].get("mem", 0)
                            else:
                                company_dict[company_id][project_id] = {}
                                company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                                company_dict[company_id][project_id].get("mem", 0)
                        else:
                            company_dict[company_id] = {}
                            company_dict[company_id][project_id] = {}
                            company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                            company_dict[company_id][project_id].get("mem", 0)

                    regex = r"^\d*M$"
                    if re.match(regex, memusage):
                        memsum = memsum + int(memusage.replace('M', ''))*1000*1000
                        if company_id in company_dict.keys():
                            if project_id in company_dict[company_id].keys():
                                company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                                company_dict[company_id][project_id].get("mem", 0)
                            else:
                                company_dict[company_id][project_id] = {}
                                company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                                company_dict[company_id][project_id].get("mem", 0)
                        else:
                            company_dict[company_id] = {}
                            company_dict[company_id][project_id] = {}
                            company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                            company_dict[company_id][project_id].get("mem", 0)

                    regex = r"^\d+m$"
                    if re.match(regex, memusage):
                        memsum = memsum + int(memusage.replace('000m', ''))
                        if company_id in company_dict.keys():
                            if project_id in company_dict[company_id].keys():
                                company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(memusage.replace('000m', ''))
                            else:
                                company_dict[company_id][project_id] = {}
                                company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(memusage.replace('000m', ''))
                                company_dict[company_id][project_id].get("mem", 0)
                        else:
                            company_dict[company_id] = {}
                            company_dict[company_id][project_id] = {}
                            company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(memusage.replace('000m', ''))
                            company_dict[company_id][project_id].get("mem", 0)

                    regex = r"^\d+Mi$"
                    if re.match(regex, memusage):
                        memsum = memsum+int(memusage.replace('Mi', ''))*1024*1024
                        if company_id in company_dict.keys():
                            if project_id in company_dict[company_id].keys():
                                company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                                company_dict[company_id][project_id].get("mem", 0)
                            else:
                                company_dict[company_id][project_id] = {}
                                company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                                company_dict[company_id][project_id].get("mem", 0)
                        else:
                            company_dict[company_id] = {}
                            company_dict[company_id][project_id] = {}
                            company_dict[company_id]["mem"] = company_dict[company_id].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                            company_dict[company_id].get("mem", 0)

                    regex = r"^\d+Gi$"
                    if re.match(regex, memusage):
                        memsum = memsum + int(memusage.replace('Gi', ''))*1024*1024*1024
                        if company_id in company_dict.keys():
                            if project_id in company_dict[company_id].keys():
                                company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                                company_dict[company_id][project_id].get("mem", 0)
                            else:
                                company_dict[company_id][project_id] = {}
                                company_dict[company_id]["mem"] = company_dict[company_id].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                                company_dict[company_id].get("mem", 0)
                        else:
                            company_dict[company_id] = {}
                            company_dict[company_id][project_id] = {}
                            company_dict[company_id][project_id]["mem"] = company_dict[company_id][project_id].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                            company_dict[company_id][project_id].get("mem", 0)

                if "nvidia.com/gpu" in pod.spec.containers[0].resources.requests:
                    company_id = pod.metadata.labels.get('company_id')
                    project_id = pod.metadata.labels.get('project_id')
                    if not company_id:
                        continue
                    if not project_id:
                        continue

                    gpuusage = pod.spec.containers[0].resources.requests.get('nvidia.com/gpu')
                    gpusum = gpusum + int(gpuusage)

                    if company_id in company_dict.keys():
                        if project_id in company_dict[company_id].keys():
                            company_dict[company_id][project_id]["gpu"] = company_dict[company_id][project_id].get("gpu", 0) + int(gpuusage)
                            company_dict[company_id][project_id].get("gpu", 0)
                        else:
                            company_dict[company_id][project_id] = {}
                            company_dict[company_id][project_id]["gpu"] = company_dict[company_id][project_id].get("gpu", 0) + int(gpuusage)
                            company_dict[company_id][project_id].get("gpu", 0)
                    else:
                        company_dict[company_id] = {}
                        company_dict[company_id][project_id] = {}
                        company_dict[company_id][project_id]["gpu"] = company_dict[company_id][project_id].get("gpu", 0) + int(gpuusage)
                        company_dict[company_id][project_id].get("gpu", 0)
                print("<RAW Dict>")
                print(str(company_dict) + "\n")

    print("<<< Summary >>>")
    print("CPU usage in m: " + str(cpusum) + "m")
    print("CPU usage in number: " + str(cpusum/1000) + "\n")

    print("Memory usage in byte: " + str(memsum))
    print("Memory usage in GiB: " + str(memsum/1024/1024/1024) + "\n")

    print("GPU usage in number: " + str(gpusum) + "\n")

    print("<Companies>")
    print(str(company_dict.keys()) + "\n")

    print("<Detailed Usages>")
    for companies in company_dict.keys():

        cpu_in_cpn = 0
        mem_in_cpn = 0
        gpu_in_cpn = 0

        print("Company: " + companies)
        print(">RAW: " + str(company_dict[companies]) + "\n")

        for projects in company_dict[companies].keys():
            print(">> Company: " + companies + " Project: " + projects)
            cpu_in_cpn = company_dict[companies][projects].get("cpu", 0) + cpu_in_cpn
            mem_in_cpn = company_dict[companies][projects].get("mem", 0) + mem_in_cpn
            gpu_in_cpn = company_dict[companies][projects].get("gpu", 0) + gpu_in_cpn
            cpu_in_prj = company_dict[companies][projects].get("cpu", 0)
            mem_in_prj = company_dict[companies][projects].get("mem", 0)
            gpu_in_prj = company_dict[companies][projects].get("gpu", 0)
            print("CPU: " + str(cpu_in_prj) + "m MEM: " + str(mem_in_prj) + "(byte) GPU: " + str(gpu_in_prj))
        print(">>>Overall CPU: " + str(cpu_in_cpn) + "m MEM: " + str(mem_in_cpn) + "(byte) GPU: " + str(gpu_in_cpn) + "\n\n")
    print("<Raw Dict>")
    print(str(company_dict) + "\n")

while True:

    if mode == "node":
        get_node_statistics()
    else:
        get_pod_statistics()

    time.sleep(interval)
