#!/bin/bash
#
# Course: McKesson Deep Azure
# Project: Azure Batch
# Student: Martin Bertrand
#
# X12toXML_admin_create.bash
#
################################################################################

# Configuration options.  These can be changed to reflect your preferences
az='/home/mbert/tools/azure-cli/az'

rg='mbertrg17'
location='canadaeast'
sa='mbertsa17'

ba='mbertbatch17'
job="X12toXMLJob"
pool="X12toXMLPool"

adminvm='mbertadmin17'
user='mbert'
passwd='7e8f_f+FF=j3888'

###########################################################
###########################################################
# NO changes beyond this point
###########################################################
###########################################################

# External files configuration
configfile="X12toXML_admin_config.py"
prereq="edi_handler.py gen_parser.py state_machine.py x12_parser.py x12_schema.xml requirements.txt X12toXML_admin.py helpers.py"
uploadfiles="$prereq $configfile"

###########################################################
# Startup verifications

# Arguments
if [ $# -ne 0 ]
then
    echo "ERROR: this argument takes no argument."
    exit 1
fi

# Prereq files
for F in  $prereq
do
    if [ ! -f $F ]
    then
        echo "ERROR: missing pre-requisite file $F, aborting."
        exit 1
    fi
done

###########################################################
echo "Resource group: $rg..."
rgcounter=0
while [ $rgcounter -lt 2 ]
do
    if [ $($az group list | grep -ci $rg) -eq 0 ]
    then
        $az group create --name $rg --location $location
    else
        echo "RG $rg created."
        echo "------------------------------------------------------------"
        rgcounter=2
    fi
    (( rgcounter = rgcounter + 1 ))
done

###########################################################
echo "Storage account: $sa..."
sacounter=0
while [ $sacounter -lt 2 ]
do
    if [ $($az storage account list | grep -ci $sa) -eq 0 ]
    then
        $az storage account create \
            --name $sa \
            --resource-group $rg \
            --access-tier Hot \
            --kind BlobStorage \
            --location $location \
            --sku Standard_LRS
    else
        echo "Storage account $sa created."

        sakey=$($az storage account keys list --account-name $sa --resource-group $rg | grep value | head -1 | cut -d'"' -f4)
        echo -e "\nStorage account key: $sakey"

        echo "------------------------------------------------------------"
        sacounter=2
    fi
    (( sacounter = sacounter + 1 ))
done

###########################################################
echo "Administration VM..."
vmcounter=0
while [ $vmcounter -lt 2 ]
do
    if [ $($az vm list | grep -ci $adminvm) -eq 0 ]
    then
        $az vm create \
            --name $adminvm \
            --resource-group $rg \
            --image UbuntuLTS \
            --admin-password $passwd \
            --admin-username $user \
            --generate-ssh-keys \
            --public-ip-address ${adminvm}pubip \
            --os-disk-name ${adminvm}disk \
            --storage-sku Standard_LRS

    else
        echo "VM $adminvm created."
        vmcounter=2
    fi
    (( vmcounter = vmcounter + 1 ))
done

# Collect connection data
a1publicip=$($az network public-ip show --name ${adminvm}pubip --resource-group $rg | grep ipAddress | cut -d'"' -f4)
echo -e "\nVM $adminvm public IP: $a1publicip"

echo "To connect to $adminvm: sshpass -p \"$passwd\" ssh -o StrictHostKeyChecking=no $user@$a1publicip "
echo "------------------------------------------------------------"

###########################################################
echo "Create batch account..."
bacounter=0
while [ $bacounter -lt 2 ]
do
    if [ $($az batch account list | grep -ci $ba) -eq 0 ]
    then
        $az batch account create \
            --location $location \
            --name $ba \
            --resource-group $rg \
            --storage-account $sa
    else
        echo "Batch account $ba created."
        bacounter=2
    fi
    (( bacounter = bacounter + 1 ))
done

batchkey=$($az batch account keys list --name $ba --resource-group $rg | grep primary | cut -d'"' -f4)
endpoint=$($az batch account show --name $ba --resource-group $rg | grep accountEndpoint | cut -d'"' -f4)
batchurl="https://$endpoint"

echo -e "\nBatch key: $batchkey"
echo "Batch account URL: $batchurl"

echo "------------------------------------------------------------"

###########################################################
echo "Create the configuration file..."
    >$configfile

    echo "_BATCH_ACCOUNT_NAME = '$ba'" >>$configfile
    echo "_BATCH_ACCOUNT_KEY = '$batchkey'" >>$configfile
    echo "_BATCH_ACCOUNT_URL = '$batchurl'" >>$configfile
    echo "_STORAGE_ACCOUNT_NAME = '$sa'" >>$configfile
    echo "_STORAGE_ACCOUNT_KEY = '$sakey'" >>$configfile
    echo "_POOL_ID = '$pool'" >>$configfile
    echo "_POOL_NODE_COUNT = 1" >>$configfile
    echo "_JOB_ID = '$job'" >>$configfile
echo "------------------------------------------------------------"

###########################################################
echo "Upload files to the administration VM..."

    echo "    Scripts..."
    sshpass -p "$passwd" ssh -o StrictHostKeyChecking=no mbert@$a1publicip 'mkdir scripts' 2>/dev/null
    for F in $uploadfiles
    do
        sshpass -p "$passwd" scp -C -o StrictHostKeyChecking=no $F $user@$a1publicip:scripts
    done

    echo "    Data files..."
    sshpass -p "$passwd" ssh -o StrictHostKeyChecking=no mbert@$a1publicip 'mkdir datafiles' 2>/dev/null
    sshpass -p "$passwd" scp -C -o StrictHostKeyChecking=no datafiles/* $user@$a1publicip:datafiles

echo "------------------------------------------------------------"

###########################################################
echo "Configure the administration vm..."

    echo -e "\n    Install Python and dependencies...\n"
    sshpass -p "$passwd" ssh -o StrictHostKeyChecking=no mbert@$a1publicip 'sudo apt-get update'
    sshpass -p "$passwd" ssh -o StrictHostKeyChecking=no mbert@$a1publicip 'sudo apt-get install -y build-essential libssl-dev libffi-dev python3 libpython3-dev python3-dev python3-pip'

    echo -e "\n    PIP install azure-batch and azure-storage\n"
    sshpass -p "$passwd" ssh -o StrictHostKeyChecking=no mbert@$a1publicip 'sudo pip3 install --upgrade pip'
    sshpass -p "$passwd" ssh -o StrictHostKeyChecking=no mbert@$a1publicip 'sudo pip3 install -r scripts/requirements.txt'

    sshpass -p "$passwd" ssh -o StrictHostKeyChecking=no mbert@$a1publicip 'sudo sync'

echo "------------------------------------------------------------"
