#!/bin/bash

# Check if parameter is empty
if [ -z "$MY_NODE_NAME" ]
then
    echo "[ERROR][INIT] NODE_NAME Variable not found, exiting..."
    exit
else
    echo "[INFO][INIT] Runnig on Node: $MY_NODE_NAME"
fi

if [ -z "$ING_NAMESPACE" ]
then
    echo "[INFO][INIT] ING_NAMESPACE Variable not found, will fetch Ingress info from all namespace."
else
    echo "[INFO][INIT] Specifying Namespace of Ingress in $ING_NAMESPACE namespace."
fi

if [ -z "$SVC_NAMESPACE" ]
then
    echo "[INFO][INIT] SVC_NAMESPACE Variable not found, will fetch Services info from all namespace."
else
    echo "[INFO][INIT] Specifying Namespace of Services in $SVC_NAMESPACE namespace."
fi


# Get SA TOKEN
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)

# Set API Request Interval
if [ -z "$interval" ]
then
    echo "[INFO][INIT] Interval variable not found, setting to default interval."
    interval=10
else
    echo "[INFO][INIT] Interval: $interval seconds"
fi

# Define D4 YAML Template
cat <<EOL > YAML.Part1
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health {
           lameduck 5s
        }
        ready
EOL

cat <<EOL > YAML.Part3
        kubernetes cluster.local in-addr.arpa ip6.arpa {
           pods insecure
           fallthrough in-addr.arpa ip6.arpa
           ttl 5
        }
        prometheus :9153
        forward . /etc/resolv.conf
        cache 30
        loop
        reload
        loadbalance
    }
EOL

GetNodeCount (){
  curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/nodes | jq -c '.items | length'
}

GetINGCount (){
  curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/apis/networking.k8s.io/v1/ingresses | jq -c '.items | length'
}

GetINGCount_Spaced (){
  curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/apis/networking.k8s.io/v1/namespaces/$ING_NAMESPACE/ingresses | jq -c '.items | length'
}

GetSvcCount (){
  curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/services | jq -c '.items | length'
}

GetSvcCount_Spaced (){
  curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/namespaces/$SVC_NAMESPACE/services | jq -c '.items | length'
}


# CHK if Current Node is Master
NodeCount=$(GetNodeCount)
echo "[INIT][INFO] Find $NodeCount Nodes!"

for i in $(seq 1 $NodeCount)
do
  current=$(($i - 1 ))
  # Get NodeName
  NodeName=$(curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/nodes | jq -r -c ".items["$current"].metadata.name")
  # Check if current node is Master
  if [ "$NodeName" = "$MY_NODE_NAME" ]
  then
    result=$(curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/nodes | jq -c ".items["$current"].metadata.labels.\"node-role.kubernetes.io/master\"")
    if [ "$result" != "null" ]
    then
      echo "[INIT][INFO] Running on Master Node!"
      echo "[INIT][INFO] NodeName: $NodeName"
      IsMaster=1
    else
      echo "[INIT][INFO] Running on Worker Node."
      echo "[INIT][INFO] NodeName: $NodeName"
      IsMaster=0
    fi
  else
    :
  fi
done

Gen_YAML_JSON (){
  for i in $(seq 1 $INGCount)
  do
    current=$(($i - 1 ))
    # Get Ingress Host
    if [ -z "$ING_NAMESPACE" ]
    then
      IngHosts=$(curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/apis/networking.k8s.io/v1/ingresses | jq -c ".items["$current"].spec.rules[0].host" | sed 's/"//g')
    else
      IngHosts=$(curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/apis/networking.k8s.io/v1/namespaces/$ING_NAMESPACE/ingresses | jq -c ".items["$current"].spec.rules[0].host" | sed 's/"//g')
    fi

    echo "[INFO][STATUS] IngHost: $IngHosts"
    YamlAppend="        rewrite name $IngHosts $LBName.$LBNamespace.svc.cluster.local"

    if grep -q "$YamlAppend" "YAML.Part2"
    then
      echo "[INFO][CM] Got Same DNS Record, skipping..."
    else
      echo "[INFO][CM] Writing CM $IngHosts -> $LBName.$LBNamespace.svc.cluster.local"
      echo "        rewrite name $IngHosts $LBName.$LBNamespace.svc.cluster.local" >> YAML.Part2
    fi
  done
  cat YAML.Part1 YAML.Part2 YAML.Part3 > Apply.yaml

  echo ""
  echo "<<<<< Start of YAML File >>>>>"
  cat Apply.yaml
  echo "<<<<< End of YAML File >>>>>"
  echo ""
  echo "<<<<< Start JSON File >>>>>"
  yq -o=json Apply.yaml > Apply.json
  cat Apply.json
  echo "<<<<< End of JSON File >>>>>"

  rm YAML.Part2
}

Update_CM(){
  curl -X PATCH https://kubernetes.default.svc:443/api/v1/namespaces/kube-system/configmaps/coredns  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/strategic-merge-patch+json" --data-binary @Apply.json --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
}

Update_Hosts(){
  cat /sync/hosts | grep -v "#Domain Add" > /sync/hosts.1
  rm /sync/hosts.2
  for i in $(seq 1 $INGCount)
  do
    current=$(($i - 1 ))
    # Get IngHost
      if [ -z "$ING_NAMESPACE" ]
      then
        IngHosts=$(curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/apis/networking.k8s.io/v1/ingresses | jq -c ".items["$current"].spec.rules[0].host" | sed 's/"//g')
      else
        IngHosts=$(curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/apis/networking.k8s.io/v1/namespaces/$ING_NAMESPACE/ingresses | jq -c ".items["$current"].spec.rules[0].host" | sed 's/"//g')
      fi

      HostsAppend="$LBIP    $IngHosts    #Domain Added by DS"
      if grep -q "$HostsAppend" "/sync/hosts.2"
      then
        echo "[INFO][Hosts] Got Same Hosts Record, skipping..."
      else
        echo "[INFO][Hosts] Redirecting $IngHosts to $LBIP, writing hosts..."
        echo "$HostsAppend" >> /sync/hosts.2
      fi
  done
  cat /sync/hosts.1 /sync/hosts.2 > /sync/hosts
}

FindLB (){
  for i in $(seq 1 $SvcCount)
  do
    current=$(($i - 1 ))

      # D4 Fetch from all namespace
      # Get SvcName
      SvcName=$(curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/services | jq -r -c ".items["$current"].metadata.name")
      # Get SvcNamespace
      SvcNamespace=$(curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/services | jq -r -c ".items["$current"].metadata.namespace")
      # Get SvcType
      SvcType=$(curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/services | jq -c ".items["$current"].spec.type" | sed 's/"//g')
      echo "[INFO][STATUS] SvcName:$SvcName   SvcNamespace:$SvcNamespace   SvcType:$SvcType"

    if [ -z "$SVC_NAMESPACE" ]
    then
      if [ "$SvcType" = "LoadBalancer" ]
      then
        LBName=$SvcName
        LBNamespace=$SvcNamespace
        LBIP=$(curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/services | jq -c ".items["$current"].spec.loadBalancerIP" | sed 's/"//g')
        echo "[INFO][STATUS] Found LB $LBName at $LBIP in $LBNamespace namespace !"
      else
        :
      fi
   else
      if [ "$SvcType" = "LoadBalancer" ]
      then
        LBName=$SvcName
        LBNamespace=$SvcNamespace
        if [ "$SVC_NAMESPACE" = "$SvcNamespace"]
        then
          LBIP=$(curl -s --insecure -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/services | jq -c ".items[0].status.loadBalancer.ingress[0].ip" | sed 's/"//g')
          echo "[INFO][STATUS] Found LB $LBName at $LBIP in $LBNamespace namespace !"
        fi
      else
        :
      fi
   fi

  done
}

while true
do
  echo "[INFO][TIME] $(date '+%y/%m/%d %X')"

  if [ -z "$ING_NAMESPACE" ]
  then
    INGCount=$(GetINGCount)
  else
    INGCount=$(GetINGCount_Spaced)
  fi

  #echo "<Debug> INGCount: $INGCount"

  if [ -z "$SVC_NAMESPACE" ]
  then
    SvcCount=$(GetSvcCount)
  else
    SvcCount=$(GetSvcCount_Spaced)
  fi

  if [ "$INGCount" = "0" ]
  then
    echo "[INFO][STATUS] No Ingress found!"
  else
    echo "[INFO][STATUS] Found $INGCount Ingress Services!"

    if [ "$IsMaster" = "1" ]
    then
      echo "[INFO][STATUS] Running on Master Node, update both ComfigMap and hosts."
      FindLB
      Gen_YAML_JSON
      Update_CM
      echo ""
      echo "[INFO][STATUS] ConfigMap Updated!"
      Update_Hosts
      echo ""
      echo "[INFO][STATUS] Hosts Updated!"
    else
      echo "[INFO][STATUS] Running on Worker Node, update hosts only."
      FindLB
      Update_Hosts
      echo ""
      echo "[INFO][STATUS] Hosts Updated!"

    fi
  fi
  sleep $interval
done
