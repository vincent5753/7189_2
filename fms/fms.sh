#!/bin/bash

# --------------------------------------------------
# Need install xmlstarlet, xmllint and jq

# Debian based
# apt-get install -y xmlstarlet libxml2-utils jq

# RHEL based
# yum install -y xmlstarlet
# --------------------------------------------------

# ===== Configs =====
username="admin"
passwd="admin"
ip=10.0.0.170
port=30080

space_name="test21"
space_description="test21"
project_name="kafka-drools-test"
project_repo="https://github.com/kanic1111/cc-limit-approval-app-step1"

# ===== Base params =====
base_url="http://$ip:$port/business-central/rest"
# test_url="http://10.0.0.170:30080/business-central/rest"

red=$'\e[1;31m'
grn=$'\e[1;32m'
yel=$'\e[1;33m'
blu=$'\e[1;36m'
end=$'\e[0m'

sample_container="<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><container-spec-details> <container-id>evaluation_1.0.0-SNAPSHOT</container-id> <container-name>evaluation</container-name> <release-id> <artifact-id>evaluation</artifact-id> <group-id>evaluation</group-id> <version>1.0.0-SNAPSHOT</version> </release-id> <configs> <entry> <key>RULE</key> <value xsi:type=\"ruleConfig\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"> <scannerStatus>STOPPED</scannerStatus> </value> </entry> <entry> <key>PROCESS</key> <value xsi:type=\"processConfig\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"> <runtimeStrategy>SINGLETON</runtimeStrategy> <kbase></kbase> <ksession></ksession> <mergeMode>MERGE_COLLECTIONS</mergeMode> </value> </entry> </configs> <status>STARTED</status> </container-spec-details>"

# ===== Request Function =====
function baseRequest {  # $response
    if [ $# -ge 3 ]
    then
        method=$(echo "$1" | tr '[:lower:]' '[:upper:]')
        content_type=$(echo "$2" | tr '[:upper:]' '[:lower:]')
        path=$3
        if [ $# -eq 4 ]
        then
            data=$4
            response=$(curl -u $username:$passwd -X "$method" --silent -H "content-type: application/$content_type" -H "Accept: application/$content_type" "$base_url$path" -d "$data")
        else
            response=$(curl -u $username:$passwd -X "$method" --silent -H "Accept: application/$content_type" "$base_url$path")
        fi
    fi
}

function waitJob {  # $job_status
    if [ $# -ge 1 ]
    then
        job_id=$1
        # echo "$job_id"
        while true
        do
            baseRequest GET JSON "/jobs/$job_id"
            job_status=$(echo "$response" | jq -r ".status")
            if [ "$job_status" == "ACCEPTED" ] || [ "$job_status" == "APPROVED" ]  # On Process
            then
                sleep 1
            else
                break
            fi
        done
    fi
}

# ===== Add Space =====
# Check space exist or not
echo -e -n "${blu}Create Space${end}\t\t\t"
space_create_flag=true
baseRequest GET JSON "/spaces"  # Only json
space_count=$(echo "$response" | jq length)
if [ "$space_count" != 0 ]
then
    for ((space_index=0; space_index<"$space_count"; space_index++))
    do
        if [ "$(echo "$response" | jq -r ".[$space_index].name")" == "$space_name" ]
        then
            space_create_flag=false
        fi
    done
fi

if $space_create_flag
then
    # Create space
    baseRequest POST JSON "/spaces" "{\"name\": \"$space_name\", \"description\": \"$space_description\", \"owner\": \"$username\", \"defaultGroupId\": \"com.$space_name\"}"
    waitJob "$(echo "$response" | jq -r ".jobId")"
    if [ "$job_status" != "SUCCESS" ]
    then
        echo "${red}Failed${end}"
        exit 1
    else
        echo "${grn}Success${end}"
    fi
else
    echo "${yel}Exist${end}"
fi

# ===== Add Project =====
# Check projects exist or not
echo -e -n "${blu}Import Project${end}\t\t\t"
project_import_flag=true
baseRequest GET JSON "/spaces/$space_name/projects"
if [ -n "$response" ]
then
    project_count=$(echo "$response" | jq length)
    if [ "$project_count" != 0 ]
    then
        for ((project_index=0; project_index<"$project_count"; project_index++))
        do
            if [ "$(echo "$response" | jq -r ".[$project_index].name")" == "$project_name" ]
            then
                project_import_flag=false
            fi
        done
    fi
fi

if $project_import_flag
then
    # Import project
    baseRequest POST JSON "/spaces/$space_name/git/clone" "{\"name\": \"$project_name\", \"description\": \"def\", \"userName\": \"$username\", \"password\": \"$passwd\", \"gitURL\": \"$project_repo\"}"
    waitJob "$(echo "$response" | jq -r ".jobId")"
    if [ "$job_status" != "SUCCESS" ]
    then
        echo "${red}Failed${end}"
        exit 1
    else
        echo "${grn}Success${end}"
    fi
else
    echo "${yel}Exist${end}"
fi

# ===== Deploy =====
# ----- Build project -----
echo -e -n "${blu}Compile Project${end}\t\t\t"
baseRequest POST JSON "/spaces/$space_name/projects/$project_name/maven/compile"
waitJob "$(echo "$response" | jq -r ".jobId")"
if [ "$job_status" != "SUCCESS" ]
then
    echo "${red}Failed${end}"
    exit 1
else
    echo "${grn}Success${end}"
fi

# ----- Test project -----
echo -e -n "${blu}Test Project${end}\t\t\t"
baseRequest POST JSON "/spaces/$space_name/projects/$project_name/maven/test"
waitJob "$(echo "$response" | jq -r ".jobId")"
if [ "$job_status" != "SUCCESS" ]
then
    echo "${red}Failed${end}"
    exit 1
else
    echo "${grn}Success${end}"
fi

# ----- Install/Deploy project (either install or deploy) -----
echo -e -n "${blu}Install/Deploy Project${end}\t\t"
baseRequest POST JSON "/spaces/$space_name/projects/$project_name/maven/install"  
# baseRequest POST JSON "/spaces/$space_name/projects/$project_name/maven/deploy"
waitJob "$(echo "$response" | jq -r ".jobId")"
if [ "$job_status" != "SUCCESS" ]
then
    echo "${red}Failed${end}"
    exit 1
else
    echo "${grn}Success${end}"
    # artifactID:kafka-drools-test, groupId:com.myspace, version:1.0.0-SNAPSHOT
    for row in $(echo "$response" | jq -r ".detailedResult[0]" | tr "," "\n")
    do
        value=$(echo "$row" | cut -d ":" -f 2 )
        if [ "$(echo "$row" | cut -d ":" -f 1 )" == "artifactID" ]
        then
            artifact_id=$value
        elif [ "$(echo "$row" | cut -d ":" -f 1 )" == "groupId" ]
        then
            group_id=$value
        elif [ "$(echo "$row" | cut -d ":" -f 1 )" == "version" ]
        then
            version=$value
        fi
    done
fi

# ===== Get Server ID =====
baseRequest GET XML "/controller/management/servers"

# ----- Deploy to server-----
echo "${blu}Deploy to server${end}"
container_spec=$(echo "$sample_container" | xmlstarlet ed --update "/container-spec-details/container-id" --value "$group_id:$artifact_id:$version" | xmlstarlet ed --update "/container-spec-details/container-name" --value "$artifact_id")
container_spec=$(echo "$container_spec" | xmlstarlet ed --update "/container-spec-details/release-id/artifact-id" --value "$artifact_id" | xmlstarlet ed --update "/container-spec-details/release-id/group-id" --value "$group_id" | xmlstarlet ed --update "/container-spec-details/release-id/version" --value "$version")
# echo "$container_spec" | xmllint --format - > "container_spec.xml"
for server_id in $(echo "$response" | xmllint --format --xpath '/server-template-list/server-template/server-id/text()' - 2>/dev/null)
do
    echo -e -n "$server_id\t"
    baseRequest PUT XML "/controller/management/servers/$server_id/containers/$group_id:$artifact_id:$version" "$container_spec"
    echo "${grn}Done${end}"
done

# ----- Start (not required) -----
# baseRequest POST XML "/controller/management/servers/{serverTemplateId}/containers/{containerId}/status/started"

# ++++++++++ ++++++++++ Split line ++++++++++ ++++++++++

# ===== Get Server ID =====
# baseRequest GET XML "/controller/management/servers"
# server_list=$(echo "$response" | xmllint --format --xpath '/server-template-list/server-template/server-id/text()' - 2>/dev/null)

# ===== Server Container sync =====
# for server_id in $server_list
# do
#     echo "${yel}$server_id${end}"

#     baseRequest GET XML "/controller/management/servers/$server_id/containers"
#     container_spec_list=$response

#     if [ -n "$(echo "$container_spec_list" | xmllint --format --xpath '/container-spec-list/container-spec' - 2>/dev/null)" ]
#     then
#         # Sync to another KIE Server
#         for another_server_id in $server_list
#         do
#             if [ "$another_server_id" != "$server_id" ]
#             then
#                 # Get another server's container
#                 echo "- ${blu}$another_server_id${end}"
#                 baseRequest GET XML "/controller/management/servers/$another_server_id/containers"
#                 for index in $(seq 1 "$(echo "$container_spec_list" | xmlstarlet sel -t -c "count(/container-spec-list/container-spec)" -)")
#                 do
#                     # Get container spec and id
#                     container_spec=$(echo "$container_spec_list" | xmlstarlet sel -t -c "/container-spec-list/container-spec[$index]" -)
#                     container_spec_details=$(echo "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>$container_spec" | xmlstarlet ed --delete "/container-spec/server-template-key" | sed -e 's/container-spec/container-spec-details/g')
#                     container_id=$(echo "$container_spec_details" | xmllint --format --xpath '/container-spec-details/container-id/text()' -)

#                     # Check another server
#                     sync_container_flags=true
#                     for compare_container_id in $(echo "$response" | xmllint --format --xpath '/container-spec-list/container-spec/container-id/text()' - 2>/dev/null)
#                     do
#                         if [ "$container_id" == "$compare_container_id" ]
#                         then
#                             sync_container_flags=false
#                         fi
#                     done

#                     # Sync to another server
#                     if $sync_container_flags
#                     then
#                         echo "  - ${red}$container_id${end}"
#                         baseRequest PUT XML "/controller/management/servers/$another_server_id/containers/$container_id" "$(echo "$container_spec_details" | tr --delete '\n' | tr -s ' ')"
#                         # waitJob "$(echo "$response" | jq -r ".jobId")"
#                     else
#                         echo "  - ${grn}$container_id${end}"
#                     fi
#                 done
#             fi
#         done
#     fi
# done
