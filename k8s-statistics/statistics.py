import os
import time
import re
import json
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
                # 因為CPU通常是最先需要處理的，所以優先判斷不存在
                if "cpu" in pod.spec.containers[0].resources.requests:
                    company_id = pod.metadata.labels.get('company_id')
                    project_id = pod.metadata.labels.get('project_id')
                    pod_name = str(pod.metadata.name)
                    if not company_id:
                        continue
                    if not project_id:
                        continue
                    cpuusage = pod.spec.containers[0].resources.requests.get('cpu')

                    regex = r"^\d*$"
                    if re.match(regex, cpuusage):
                        if company_id in company_dict.keys():
                            # company -> sum (確保sum會在每隻project下的第1位)
                            if "sum" in company_dict[company_id].keys():
                                print("DeBug108: sum[company_id] B4 summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                                company_dict[company_id]["sum"]["cpu"] = company_dict[company_id]["sum"].get("cpu", 0) + int(cpuusage)*1000
                                print("DeBug110: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                            else:
                                company_dict[company_id]["sum"] = dict()
                                print("DeBug113: sum[company_id] B4 summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                                company_dict[company_id]["sum"]["cpu"] = company_dict[company_id]["sum"].get("cpu", 0) + int(cpuusage)*1000
                                print("DeBug115: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                            if project_id in company_dict[company_id].keys():
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    print("DeBug119: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                                    company_dict[company_id][project_id]["sum"]["cpu"] = company_dict[company_id][project_id]["sum"].get("cpu", 0) + int(cpuusage)*1000
                                    print("DeBug121: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    print("DeBug124: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                                    company_dict[company_id][project_id]["sum"]["cpu"] = company_dict[company_id][project_id]["sum"].get("cpu", 0) + int(cpuusage)*1000
                                    print("DeBug126: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                                # company -> project -> 不同pod
                                # 因為CPU通常是最先需要處理的，所以優先判斷不存在，所以以not為優先判斷
                                if pod_name not in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["cpu"] = company_dict[company_id][project_id][pod_name].get("cpu", 0) + int(cpuusage)*1000
                                    company_dict[company_id][project_id][pod_name].get("cpu")
                                else:
                                    company_dict[company_id][project_id][pod_name]["cpu"] = company_dict[company_id][project_id][pod_name].get("cpu", 0) + int(cpuusage)*1000
                                    company_dict[company_id][project_id][pod_name].get("cpu")
                            else:
                                # 建立 project 所使用字典
                                company_dict[company_id][project_id] = dict()
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    print("DeBug141: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["cpu"]))
                                    company_dict[company_id][project_id]["sum"] = company_dict[company_id][project_id].get("sum", 0) + int(cpuusage)*1000
                                    print("DeBug143: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["cpu"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    print("DeBug146: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["cpu"]))
                                    company_dict[company_id][project_id]["sum"] = company_dict[company_id][project_id].get("sum", 0) + int(cpuusage)*1000
                                    print("DeBug148: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["cpu"]))
                                # company -> project -> 不同pod
                                # 因為CPU通常是最先需要處理的，所以優先判斷不存在，所以以not為優先判斷
                                if pod_name not in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["cpu"] = company_dict[company_id][project_id][pod_name].get("cpu", 0) + int(cpuusage)*1000
                                    company_dict[company_id][project_id][pod_name].get("cpu")
                                else:
                                    company_dict[company_id][project_id][pod_name]["cpu"] = company_dict[company_id][project_id][pod_name].get("cpu", 0) + int(cpuusage)*1000
                                    company_dict[company_id][project_id][pod_name].get("cpu")
                        else:
                            company_dict[company_id] = dict()
                            company_dict[company_id]["sum"] = dict()
                            company_dict[company_id][project_id] = dict()
                            company_dict[company_id][project_id]["sum"] = dict()
                            # company -> sum
                            print("DeBug164: sum[company_id] B4 summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                            company_dict[company_id]["sum"]["cpu"] = company_dict[company_id]["sum"].get("cpu", 0) + int(cpuusage)*1000
                            print("DeBug166: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                            # company -> project -> sum
                            company_dict[company_id][project_id]["sum"]["cpu"] = company_dict[company_id][project_id]["sum"].get("cpu", 0) + int(cpuusage)*1000
                            # company -> project -> 不同pod
                            # 因為CPU通常是最先需要處理的，所以優先判斷不存在，所以以not為優先判斷(效能稍微++)
                            if pod_name not in company_dict[company_id][project_id].keys():
                                company_dict[company_id][project_id][pod_name] = dict()
                                company_dict[company_id][project_id][pod_name]["cpu"] = company_dict[company_id][project_id][pod_name].get("cpu", 0) + int(cpuusage)*1000
                                company_dict[company_id][project_id][pod_name].get("cpu")
                            else:
                                company_dict[company_id][project_id][pod_name]["cpu"] = company_dict[company_id][project_id][pod_name].get("cpu", 0) + int(cpuusage)*1000
                                company_dict[company_id][project_id][pod_name].get("cpu")

                    regex = r"^\d*m$"
                    if re.match(regex, cpuusage):
                        if company_id in company_dict.keys():
                            # company -> sum (確保sum會在每隻project下的第1位)
                            if "sum" in company_dict[company_id].keys():
                                print("DeBug184: sum[company_id] B4 summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                                company_dict[company_id]["sum"]["cpu"] = company_dict[company_id]["sum"].get("cpu", 0) + int(cpuusage.replace('m', ''))
                                print("DeBug186: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                            else:
                                company_dict[company_id]["sum"] = dict()
                                # print("DeBug189: sum B4 summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                                # print(company_id, company_dict[company_id]["sum"].get("cpu", 0), int(cpuusage.replace('m', '')))
                                company_dict[company_id]["sum"]["cpu"] = company_dict[company_id]["sum"].get("cpu", 0) + int(cpuusage.replace('m', ''))
                                print("DeBug191: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                            if project_id in company_dict[company_id].keys():
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    print("DeBug195: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["cpu"]))
                                    company_dict[company_id][project_id]["sum"]["cpu"] = company_dict[company_id][project_id]["sum"].get("cpu", 0) + int(cpuusage.replace('m', ''))
                                    print("DeBug197: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["cpu"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    # print("DeBug200: sum B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["cpu"]))
                                    company_dict[company_id][project_id]["sum"]["cpu"] = company_dict[company_id][project_id]["sum"].get("cpu", 0) + int(cpuusage.replace('m', ''))
                                    print("DeBug202: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["cpu"]))
                                # company -> project -> 不同pod
                                if pod_name not in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["cpu"] = company_dict[company_id][project_id][pod_name].get("cpu", 0) + int(cpuusage.replace('m', ''))
                                    company_dict[company_id][project_id][pod_name].get("cpu")
                                else:
                                    company_dict[company_id][project_id][pod_name]["cpu"] = company_dict[company_id][project_id][pod_name].get("cpu", 0) + int(cpuusage.replace('m', ''))
                                    company_dict[company_id][project_id][pod_name].get("cpu")
                            else:
                                # 建立 project 所使用字典
                                company_dict[company_id][project_id] = dict()
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    print("DeBug216: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["cpu"]))
                                    company_dict[company_id][project_id]["sum"]["cpu"] = company_dict[company_id][project_id]["sum"].get("cpu", 0) + int(cpuusage.replace('m', ''))
                                    print("DeBug218: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["cpu"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    # print("DeBug221: sum B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["cpu"]))
                                    company_dict[company_id][project_id]["sum"]["cpu"] = company_dict[company_id][project_id]["sum"].get("cpu", 0) + int(cpuusage.replace('m', ''))
                                    print("DeBug223: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["cpu"]))
                                # company -> project -> 不同pod
                                # 因為CPU通常是最先需要處理的，所以優先判斷不存在，所以以not為優先判斷
                                if pod_name not in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["cpu"] = company_dict[company_id][project_id][pod_name].get("cpu", 0) + int(cpuusage.replace('m', ''))
                                    company_dict[company_id][project_id][pod_name].get("cpu")
                                else:
                                    company_dict[company_id][project_id][pod_name]["cpu"] = company_dict[company_id][project_id][pod_name].get("cpu", 0) + int(cpuusage.replace('m', ''))
                                    company_dict[company_id][project_id][pod_name].get("cpu")
                        else:
                            company_dict[company_id] = dict()
                            company_dict[company_id]["sum"] = dict()
                            company_dict[company_id][project_id] = dict()
                            company_dict[company_id][project_id]["sum"] = dict()
                            # company -> sum (確保sum會在每隻project下的第1位)
                            # print("DeBug239: sum B4 summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                            company_dict[company_id]["sum"]["cpu"] = company_dict[company_id]["sum"].get("cpu", 0) + int(cpuusage.replace('m', ''))
                            print("DeBug242: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["cpu"]))
                            # company -> project -> sum (確保sum會在每隻project下的第1位)
                            # print("DeBug243: sum B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["cpu"]))
                            company_dict[company_id][project_id]["sum"]["cpu"] = company_dict[company_id][project_id]["sum"].get("cpu", 0) + int(cpuusage.replace('m', ''))
                            print("DeBug246: sum[company_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["cpu"]))
                            # company -> project -> 不同pod
                            # 因為CPU通常是最先需要處理的，所以優先判斷不存在，所以以not為優先判斷(效能稍微++)
                            if pod_name not in company_dict[company_id][project_id].keys():
                                company_dict[company_id][project_id][pod_name] = dict()
                                company_dict[company_id][project_id][pod_name]["cpu"] = company_dict[company_id][project_id][pod_name].get("cpu", 0) + int(cpuusage.replace('m', ''))
                                company_dict[company_id][project_id][pod_name].get("cpu")
                            else:
                                company_dict[company_id][project_id][pod_name]["cpu"] = company_dict[company_id][project_id][pod_name].get("cpu", 0) + int(cpuusage.replace('m', ''))
                                company_dict[company_id][project_id][pod_name].get("cpu")

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
                        if company_id in company_dict.keys():
                            # company -> sum (確保sum會在每隻project下的第1位)
                            if "sum" in company_dict[company_id].keys():
                                # print("DeBug184: sum[company_id] B4 summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                                company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage)
                                print("DeBug186: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            else:
                                company_dict[company_id]["sum"] = dict()
                                company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage)
                                print("DeBug191: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            if project_id in company_dict[company_id].keys():
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    # print("DeBug195: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage)
                                    print("DeBug197: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage)
                                    print("DeBug202: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                # company -> project -> 不同pod
                                if pod_name not in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage)
                                    company_dict[company_id][project_id][pod_name].get("mem")
                                else:
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage)
                                    company_dict[company_id][project_id][pod_name].get("mem")
                            else:
                                # 建立 project 所使用字典
                                company_dict[company_id][project_id] = dict()
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    print("DeBug216: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage)
                                    print("DeBug218: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage)
                                    print("DeBug223: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                # company -> project -> 不同pod
                                if pod_name in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage)
                                    company_dict[company_id][project_id][pod_name].get("mem")
                                else:
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage)
                                    company_dict[company_id][project_id][pod_name].get("mem")
                        else:
                            company_dict[company_id] = dict()
                            company_dict[company_id]["sum"] = dict()
                            company_dict[company_id][project_id] = dict()
                            company_dict[company_id][project_id]["sum"] = dict()
                            company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage)
                            print("DeBug242: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            # company -> project -> sum (確保sum會在每隻project下的第1位)
                            company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage)
                            print("DeBug246: sum[company_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                            # company -> project -> 不同pod
                            if pod_name in company_dict[company_id][project_id].keys():
                                company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage)
                                company_dict[company_id][project_id][pod_name].get("mem")
                            else:
                                company_dict[company_id][project_id][pod_name] = dict()
                                company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage)
                                company_dict[company_id][project_id][pod_name].get("mem")

                    regex = r"^\d+e\d*$"
                    # int(str(str(num) + str(0)*int(enum)))
                    if re.match(regex, memusage):
                        num = (memusage.split("e")[0])
                        enum = (memusage.split("e")[1])
                        # memsum = memsum + int(str(str(num) + str(0)*int(enum)))

                        if company_id in company_dict.keys():
                            # company -> sum (確保sum會在每隻project下的第1位)
                            if "sum" in company_dict[company_id].keys():
                                # print("DeBug184: sum[company_id] B4 summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                                company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                                print("DeBug186: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            else:
                                company_dict[company_id]["sum"] = dict()
                                company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                                print("DeBug191: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            if project_id in company_dict[company_id].keys():
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    # print("DeBug195: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                                    print("DeBug197: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                                    print("DeBug202: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                # company -> project -> 不同pod
                                if pod_name not in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                                    company_dict[company_id][project_id][pod_name].get("mem")
                                else:
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                                    company_dict[company_id][project_id][pod_name].get("mem")
                            else:
                                # 建立 project 所使用字典
                                company_dict[company_id][project_id] = dict()
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    print("DeBug216: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                                    print("DeBug218: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                                    print("DeBug223: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                # company -> project -> 不同pod
                                if pod_name in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                                    company_dict[company_id][project_id][pod_name].get("mem")
                                else:
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                                    company_dict[company_id][project_id][pod_name].get("mem")
                        else:
                            company_dict[company_id] = dict()
                            company_dict[company_id]["sum"] = dict()
                            company_dict[company_id][project_id] = dict()
                            company_dict[company_id][project_id]["sum"] = dict()
                            company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                            print("DeBug242: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            # company -> project -> sum (確保sum會在每隻project下的第1位)
                            company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                            print("DeBug246: sum[company_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                            # company -> project -> 不同pod
                            if pod_name in company_dict[company_id][project_id].keys():
                                company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                                company_dict[company_id][project_id][pod_name].get("mem")
                            else:
                                company_dict[company_id][project_id][pod_name] = dict()
                                company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(str(str(num) + str(0)*int(enum)))
                                company_dict[company_id][project_id][pod_name].get("mem")

                    regex = r"^\d*M$"
                    # int(memusage.replace('M', ''))*1000*1000
                    if re.match(regex, memusage):
                        # memsum = memsum + int(memusage.replace('M', ''))*1000*1000
                        if company_id in company_dict.keys():
                            # company -> sum (確保sum會在每隻project下的第1位)
                            if "sum" in company_dict[company_id].keys():
                                # print("DeBug184: sum[company_id] B4 summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                                company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                                print("DeBug186: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            else:
                                company_dict[company_id]["sum"] = dict()
                                company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                                print("DeBug191: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            if project_id in company_dict[company_id].keys():
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    # print("DeBug195: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                                    print("DeBug197: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                                    print("DeBug202: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                # company -> project -> 不同pod
                                if pod_name not in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                                    company_dict[company_id][project_id][pod_name].get("mem")
                                else:
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                                    company_dict[company_id][project_id][pod_name].get("mem")
                            else:
                                # 建立 project 所使用字典
                                company_dict[company_id][project_id] = dict()
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    print("DeBug216: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                                    print("DeBug218: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                                    print("DeBug223: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                # company -> project -> 不同pod
                                if pod_name in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                                    company_dict[company_id][project_id][pod_name].get("mem")
                                else:
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                                    company_dict[company_id][project_id][pod_name].get("mem")
                        else:
                            company_dict[company_id] = dict()
                            company_dict[company_id]["sum"] = dict()
                            company_dict[company_id][project_id] = dict()
                            company_dict[company_id][project_id]["sum"] = dict()
                            company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                            print("DeBug242: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            # company -> project -> sum (確保sum會在每隻project下的第1位)
                            company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                            print("DeBug246: sum[company_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                            # company -> project -> 不同pod
                            if pod_name in company_dict[company_id][project_id].keys():
                                company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                                company_dict[company_id][project_id][pod_name].get("mem")
                            else:
                                company_dict[company_id][project_id][pod_name] = dict()
                                company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('M', ''))*1000*1000
                                company_dict[company_id][project_id][pod_name].get("mem")

                    regex = r"^\d+m$"
                    if re.match(regex, memusage):
                        # memsum = memsum + int(memusage.replace('000m', ''))
                        if company_id in company_dict.keys():
                            # company -> sum (確保sum會在每隻project下的第1位)
                            if "sum" in company_dict[company_id].keys():
                                print("DeBug184: sum[company_id] B4 summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                                company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage.replace('000m', ''))
                                print("DeBug186: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            else:
                                company_dict[company_id]["sum"] = dict()
                                company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage.replace('000m', ''))
                                print("DeBug191: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            if project_id in company_dict[company_id].keys():
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    print("DeBug195: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('000m', ''))
                                    print("DeBug197: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('000m', ''))
                                    print("DeBug202: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                # company -> project -> 不同pod
                                if pod_name not in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('000m', ''))
                                    company_dict[company_id][project_id][pod_name].get("mem")
                                else:
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('000m', ''))
                                    company_dict[company_id][project_id][pod_name].get("mem")
                            else:
                                # 建立 project 所使用字典
                                company_dict[company_id][project_id] = dict()
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    print("DeBug216: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('000m', ''))
                                    print("DeBug218: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('000m', ''))
                                    print("DeBug223: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                # company -> project -> 不同pod
                                if pod_name in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('000m', ''))
                                    company_dict[company_id][project_id][pod_name].get("mem")
                                else:
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('000m', ''))
                                    company_dict[company_id][project_id][pod_name].get("mem")
                        else:
                            company_dict[company_id] = dict()
                            company_dict[company_id]["sum"] = dict()
                            company_dict[company_id][project_id] = dict()
                            company_dict[company_id][project_id]["sum"] = dict()
                            company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage.replace('000m', ''))
                            print("DeBug242: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            # company -> project -> sum (確保sum會在每隻project下的第1位)
                            company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('000m', ''))
                            print("DeBug246: sum[company_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                            # company -> project -> 不同pod
                            if pod_name in company_dict[company_id][project_id].keys():
                                company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('000m', ''))
                                company_dict[company_id][project_id][pod_name].get("mem")
                            else:
                                company_dict[company_id][project_id][pod_name] = dict()
                                company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('000m', ''))
                                company_dict[company_id][project_id][pod_name].get("mem")

                    regex = r"^\d+Mi$"
                    if re.match(regex, memusage):
                        # memsum = memsum + int(memusage.replace('Mi', ''))*1024*1024
                        if company_id in company_dict.keys():
                            # company -> sum (確保sum會在每隻project下的第1位)
                            if "sum" in company_dict[company_id].keys():
                                # print("DeBug184: sum[company_id] B4 summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                                company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                                print("DeBug186: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            else:
                                company_dict[company_id]["sum"] = dict()
                                company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                                print("DeBug191: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            if project_id in company_dict[company_id].keys():
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    # print("DeBug195: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                                    print("DeBug197: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                                    print("DeBug202: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                # company -> project -> 不同pod
                                if pod_name not in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                                    company_dict[company_id][project_id][pod_name].get("mem")
                                else:
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                                    company_dict[company_id][project_id][pod_name].get("mem")
                            else:
                                # 建立 project 所使用字典
                                company_dict[company_id][project_id] = dict()
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    print("DeBug216: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                                    print("DeBug218: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                                    print("DeBug223: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                # company -> project -> 不同pod
                                if pod_name in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                                    company_dict[company_id][project_id][pod_name].get("mem")
                                else:
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                                    company_dict[company_id][project_id][pod_name].get("mem")
                        else:
                            company_dict[company_id] = dict()
                            company_dict[company_id]["sum"] = dict()
                            company_dict[company_id][project_id] = dict()
                            company_dict[company_id][project_id]["sum"] = dict()
                            company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                            print("DeBug242: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            # company -> project -> sum (確保sum會在每隻project下的第1位)
                            company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                            print("DeBug246: sum[company_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                            # company -> project -> 不同pod
                            if pod_name in company_dict[company_id][project_id].keys():
                                company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                                company_dict[company_id][project_id][pod_name].get("mem")
                            else:
                                company_dict[company_id][project_id][pod_name] = dict()
                                company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('Mi', ''))*1024*1024
                                company_dict[company_id][project_id][pod_name].get("mem")

                    regex = r"^\d+Gi$"
                    if re.match(regex, memusage):
                        # memsum = memsum + int(memusage.replace('Gi', ''))*1024*1024*1024
                        if company_id in company_dict.keys():
                            # company -> sum (確保sum會在每隻project下的第1位)
                            if "sum" in company_dict[company_id].keys():
                                # print("DeBug184: sum[company_id] B4 summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                                company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                                print("DeBug186: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            else:
                                company_dict[company_id]["sum"] = dict()
                                company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                                print("DeBug191: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            if project_id in company_dict[company_id].keys():
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    # print("DeBug195: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                                    print("DeBug197: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                                    print("DeBug202: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                # company -> project -> 不同pod
                                if pod_name not in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                                    company_dict[company_id][project_id][pod_name].get("mem")
                                else:
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                                    company_dict[company_id][project_id][pod_name].get("mem")
                            else:
                                # 建立 project 所使用字典
                                company_dict[company_id][project_id] = dict()
                                # company -> project -> sum (確保sum會在每隻project下的第1位)
                                if "sum" in company_dict[company_id][project_id].keys():
                                    print("DeBug216: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                                    print("DeBug218: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                else:
                                    company_dict[company_id][project_id]["sum"] = dict()
                                    company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                                    print("DeBug223: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                # company -> project -> 不同pod
                                if pod_name in company_dict[company_id][project_id].keys():
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                                    company_dict[company_id][project_id][pod_name].get("mem")
                                else:
                                    company_dict[company_id][project_id][pod_name] = dict()
                                    company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                                    company_dict[company_id][project_id][pod_name].get("mem")
                        else:
                            company_dict[company_id] = dict()
                            company_dict[company_id]["sum"] = dict()
                            company_dict[company_id][project_id] = dict()
                            company_dict[company_id][project_id]["sum"] = dict()
                            company_dict[company_id]["sum"]["mem"] = company_dict[company_id]["sum"].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                            print("DeBug242: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            # company -> project -> sum (確保sum會在每隻project下的第1位)
                            company_dict[company_id][project_id]["sum"]["mem"] = company_dict[company_id][project_id]["sum"].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                            print("DeBug246: sum[company_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                            # company -> project -> 不同pod
                            if pod_name in company_dict[company_id][project_id].keys():
                                company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                                company_dict[company_id][project_id][pod_name].get("mem")
                            else:
                                company_dict[company_id][project_id][pod_name] = dict()
                                company_dict[company_id][project_id][pod_name]["mem"] = company_dict[company_id][project_id][pod_name].get("mem", 0) + int(memusage.replace('Gi', ''))*1024*1024*1024
                                company_dict[company_id][project_id][pod_name].get("mem")

                if "nvidia.com/gpu" in pod.spec.containers[0].resources.requests:
                    company_id = pod.metadata.labels.get('company_id')
                    project_id = pod.metadata.labels.get('project_id')

                    gpuusage = pod.spec.containers[0].resources.requests.get('nvidia.com/gpu')
                    if company_id in company_dict.keys():
                        # company -> sum (確保sum會在每隻project下的第1位)
                        if "sum" in company_dict[company_id].keys():
                            # print("DeBug184: sum[company_id] B4 summay -> " + str(company_dict[company_id]["sum"]["mem"]))
                            company_dict[company_id]["sum"]["gpu"] = company_dict[company_id]["sum"].get("gpu", 0) + int(gpuusage)
                            print("DeBug186: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["gpu"]))
                        else:
                            company_dict[company_id]["sum"] = dict()
                            company_dict[company_id]["sum"]["gpu"] = company_dict[company_id]["sum"].get("gpu", 0) + int(gpuusage)
                            print("DeBug191: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["gpu"]))
                        if project_id in company_dict[company_id].keys():
                            # company -> project -> sum (確保sum會在每隻project下的第1位)
                            if "sum" in company_dict[company_id][project_id].keys():
                                # print("DeBug195: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["mem"]))
                                company_dict[company_id][project_id]["sum"]["gpu"] = company_dict[company_id][project_id]["sum"].get("gpu", 0) + int(gpuusage)
                                print("DeBug197: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["gpu"]))
                            else:
                                company_dict[company_id][project_id]["sum"] = dict()
                                company_dict[company_id][project_id]["sum"]["gpu"] = company_dict[company_id][project_id]["sum"].get("gpu", 0) + int(gpuusage)
                                print("DeBug202: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["gpu"]))
                            # company -> project -> 不同pod
                            if pod_name not in company_dict[company_id][project_id].keys():
                                company_dict[company_id][project_id][pod_name] = dict()
                                company_dict[company_id][project_id][pod_name]["gpu"] = company_dict[company_id][project_id][pod_name].get("gpu", 0) + int(gpuusage)
                                company_dict[company_id][project_id][pod_name].get("gpu")
                            else:
                                company_dict[company_id][project_id][pod_name]["gpu"] = company_dict[company_id][project_id][pod_name].get("gpu", 0) + int(gpuusage)
                                company_dict[company_id][project_id][pod_name].get("gpu")
                        else:
                            # 建立 project 所使用字典
                            company_dict[company_id][project_id] = dict()
                            # company -> project -> sum (確保sum會在每隻project下的第1位)
                            if "sum" in company_dict[company_id][project_id].keys():
                                print("DeBug216: sum[company_id][project_id] B4 summay -> " + str(company_dict[company_id][project_id]["sum"]["gpu"]))
                                company_dict[company_id][project_id]["sum"]["gpu"] = company_dict[company_id][project_id]["sum"].get("gpu", 0) + int(gpuusage)
                                print("DeBug218: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["gpu"]))
                            else:
                                company_dict[company_id][project_id]["sum"] = dict()
                                company_dict[company_id][project_id]["sum"]["gpu"] = company_dict[company_id][project_id]["sum"].get("gpu", 0) + int(gpuusage)
                                print("DeBug223: sum[company_id][project_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["gpu"]))
                            # company -> project -> 不同pod
                            if pod_name in company_dict[company_id][project_id].keys():
                                company_dict[company_id][project_id][pod_name]["gpu"] = company_dict[company_id][project_id][pod_name].get("gpu", 0) + int(gpuusage)
                                company_dict[company_id][project_id][pod_name].get("gpu")
                            else:
                                company_dict[company_id][project_id][pod_name] = dict()
                                company_dict[company_id][project_id][pod_name]["gpu"] = company_dict[company_id][project_id][pod_name].get("gpu", 0) + int(gpuusage)
                                company_dict[company_id][project_id][pod_name].get("gpu")
                    else:
                        company_dict[company_id] = dict()
                        company_dict[company_id]["sum"] = dict()
                        company_dict[company_id][project_id] = dict()
                        company_dict[company_id][project_id]["sum"] = dict()
                        company_dict[company_id]["sum"]["gpu"] = company_dict[company_id]["sum"].get("gpu", 0) + int(gpuusage)
                        print("DeBug242: sum[company_id] AFT summay -> " + str(company_dict[company_id]["sum"]["gpu"]))
                        company_dict[company_id][project_id]["sum"]["gpu"] = company_dict[company_id][project_id]["sum"].get("gpu", 0) + int(gpuusage)
                        print("DeBug246: sum[company_id] AFT summay -> " + str(company_dict[company_id][project_id]["sum"]["gpu"]))
                        # company -> project -> 不同pod
                        if pod_name in company_dict[company_id][project_id].keys():
                            company_dict[company_id][project_id][pod_name]["gpu"] = company_dict[company_id][project_id][pod_name].get("gpu", 0) + int(gpuusage)
                            company_dict[company_id][project_id][pod_name].get("gpu")
                        else:
                            company_dict[company_id][project_id][pod_name] = dict()
                            company_dict[company_id][project_id][pod_name]["gpu"] = company_dict[company_id][project_id][pod_name].get("gpu", 0) + int(gpuusage)
                            company_dict[company_id][project_id][pod_name].get("gpu")
                print("<RAW Dict>")
                print(str(json.dumps(company_dict, indent=4)) + "\n")

while True:

    if mode == "node":
        get_node_statistics()
    else:
        get_pod_statistics()

    time.sleep(interval)
