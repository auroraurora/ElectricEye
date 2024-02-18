#This file is part of ElectricEye.
#SPDX-License-Identifier: Apache-2.0

#Licensed to the Apache Software Foundation (ASF) under one
#or more contributor license agreements.  See the NOTICE file
#distributed with this work for additional information
#regarding copyright ownership.  The ASF licenses this file
#to you under the Apache License, Version 2.0 (the
#"License"); you may not use this file except in compliance
#with the License.  You may obtain a copy of the License at

#http://www.apache.org/licenses/LICENSE-2.0

#Unless required by applicable law or agreed to in writing,
#software distributed under the License is distributed on an
#"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#KIND, either express or implied.  See the License for the
#specific language governing permissions and limitations
#under the License.

from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.recoveryservices import RecoveryServicesClient
from azure.mgmt.recoveryservicesbackup import RecoveryServicesBackupClient
import datetime
import base64
import json
from check_register import CheckRegister

registry = CheckRegister()

def get_all_azure_vms(cache: dict, azureCredential, azSubId: str):
    """
    Returns a list of all Azure VMs in a Subscription
    """
    azComputeClient = ComputeManagementClient(azureCredential,azSubId)

    response = cache.get("get_all_azure_vms")
    if response:
        return response
    
    vmList = [vm for vm in azComputeClient.virtual_machines.list_all()]
    if not vmList or vmList is None:
        vmList = []

    cache["get_all_azure_vms"] = vmList
    return cache["get_all_azure_vms"]

def get_all_azure_vnets(cache: dict, azureCredential, azSubId: str):
    """
    Returns a list of all Azure Virtual Networks in a Subscription
    """
    azNetworkClient = NetworkManagementClient(azureCredential,azSubId)

    response = cache.get("get_all_azure_vnets")
    if response:
        return response
    
    vnetList = [vnet for vnet in azNetworkClient.virtual_networks.list_all()]
    if not vnetList or vnetList is None:
        vnetList = []

    cache["get_all_azure_vnets"] = vnetList
    return cache["get_all_azure_vnets"]

def get_all_azure_rgs(cache: dict, azureCredential, azSubId: str):
    """
    Returns a list of all Azure Resource Groups in a Subscription
    """
    azResourceClient = ResourceManagementClient(azureCredential, azSubId)

    response = cache.get("get_all_azure_rgs")
    if response:
        return response
    
    rgList = [rg for rg in azResourceClient.resource_groups.list()]
    if not rgList or rgList is None:
        rgList = []

    cache["get_all_azure_rgs"] = rgList
    return cache["get_all_azure_rgs"]

def process_resource_group_name(id: str):
    """
    Returns the Resource Group Name from an Azure VM Id
    """
    parts = id.split("/")
    rgIndex = parts.index("resourceGroups") + 1
    
    return parts[rgIndex]

@registry.register_check("azure.virtual_machines")
def azure_vm_bastion_host_exists_check(cache: dict, awsAccountId: str, awsRegion: str, awsPartition: str, azureCredential, azSubId: str) -> dict:
    """
    [Azure.VirtualMachines.1] An Azure Bastion Host should be deployed to provide secure RDP and SSH access to Azure Virtual Machines
    """
    azNetworkClient = NetworkManagementClient(azureCredential,azSubId)
    # ISO Time
    iso8601Time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for vnet in get_all_azure_vnets(cache, azureCredential, azSubId):
        # B64 encode all of the details for the Asset
        assetJson = json.dumps(vnet,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        rgName = process_resource_group_name(vnet.id)
        azRegion = vnet.location
        vnetName = vnet.name

        # Check if a Bastion Host exists in the Virtual Network
        bastionHostExists = False
        for bastionHost in azNetworkClient.bastion_hosts.list():
            for ipConfig in bastionHost.ip_configurations:
                if vnet.id in ipConfig.subnet.id:
                    bastionHostExists = True
                    break
        
        # this is a failing check
        if bastionHostExists is False:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{azSubId}/{azRegion}/{vnet.id}/az-vm-bastion-host-exists-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{azSubId}/{azRegion}/{vnet.id}/az-vm-bastion-host-exists-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "LOW"},
                "Confidence": 99,
                "Title": "[Azure.VirtualMachines.1] An Azure Bastion Host should be deployed to provide secure RDP and SSH access to Azure Virtual Machines",
                "Description": f"Virtual Network {vnetName} in Subscription {azSubId} in {azRegion} does not have an Azure Bastion Host deployed. Azure Bastion is a fully managed PaaS service that provides secure and seamless RDP and SSH access to your virtual machines directly through the Azure Portal. Azure Bastion is provisioned directly in your Virtual Network (VNet) and supports all VMs in your Virtual Network using SSL without any exposure through public IP addresses. Azure Bastion is provisioned directly in your Virtual Network (VNet) and supports all VMs in your Virtual Network using SSL without any exposure through public IP addresses. Azure Bastion is provisioned directly in your Virtual Network (VNet) and supports all VMs in your Virtual Network using SSL without any exposure through public IP addresses. Refer to the remediation instructions if this configuration is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "To deploy an Azure Bastion Host refer to the Azure Bastion documentation.",
                        "Url": "https://docs.microsoft.com/en-us/azure/bastion/bastion-create-host-portal"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "Azure",
                    "ProviderType": "CSP",
                    "ProviderAccountId": azSubId,
                    "AssetRegion": azRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Network",
                    "AssetService": "Azure Virtual Network",
                    "AssetComponent": "Virtual Network"
                },
                "Resources": [
                    {
                        "Type": "AzureVirtualNetwork",
                        "Id": vnet.id,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "SubscriptionId": azSubId,
                                "ResourceGroupName": rgName,
                                "Region": azRegion,
                                "Name": vnetName,
                                "Id": vnet.id
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.AC-4",
                        "NIST SP 800-53 Rev. 4 AC-17",
                        "NIST SP 800-53 Rev. 4 AC-20",
                        "NIST SP 800-53 Rev. 4 AC-21",
                        "AICPA TSC CC6.1",
                        "ISO 27001:2013 A.9.1.2",
                        "CIS Microsoft Azure Foundations Benchmark V2.0.0 7.1",
                        "MITRE ATT&CK T1590",
                        "MITRE ATT&CK T1592",
                        "MITRE ATT&CK T1595"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE"
            }
            yield finding
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{azSubId}/{azRegion}/{vnet.id}/az-vm-bastion-host-exists-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{azSubId}/{azRegion}/{vnet.id}/az-vm-bastion-host-exists-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[Azure.VirtualMachines.1] An Azure Bastion Host should be deployed to provide secure RDP and SSH access to Azure Virtual Machines",
                "Description": f"Virtual Network {vnetName} in Subscription {azSubId} in {azRegion} does have an Azure Bastion Host deployed.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "To deploy an Azure Bastion Host refer to the Azure Bastion documentation.",
                        "Url": "https://docs.microsoft.com/en-us/azure/bastion/bastion-create-host-portal"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "Azure",
                    "ProviderType": "CSP",
                    "ProviderAccountId": azSubId,
                    "AssetRegion": azRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Network",
                    "AssetService": "Azure Virtual Network",
                    "AssetComponent": "Virtual Network"
                },
                "Resources": [
                    {
                        "Type": "AzureVirtualNetwork",
                        "Id": vnet.id,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "SubscriptionId": azSubId,
                                "ResourceGroupName": rgName,
                                "Region": azRegion,
                                "Name": vnetName,
                                "Id": vnet.id
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.AC-4",
                        "NIST SP 800-53 Rev. 4 AC-17",
                        "NIST SP 800-53 Rev. 4 AC-20",
                        "NIST SP 800-53 Rev. 4 AC-21",
                        "AICPA TSC CC6.1",
                        "ISO 27001:2013 A.9.1.2",
                        "CIS Microsoft Azure Foundations Benchmark V2.0.0 7.1",
                        "MITRE ATT&CK T1590",
                        "MITRE ATT&CK T1592",
                        "MITRE ATT&CK T1595"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED"
            }
            yield finding

@registry.register_check("azure.virtual_machines")
def azure_vm_utilizing_managed_disks_check(cache: dict, awsAccountId: str, awsRegion: str, awsPartition: str, azureCredential, azSubId: str) -> dict:
    """
    [Azure.VirtualMachines.2] Azure Virtual Machines should utilize Managed Disks for storage
    """
    # ISO Time
    iso8601Time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for vm in get_all_azure_vms(cache, azureCredential, azSubId):
        # B64 encode all of the details for the Asset
        assetJson = json.dumps(vm,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        rgName = process_resource_group_name(vm.id)
        azRegion = vm.location
        vmName = vm.name

        # Check if the VM is using Managed Disks
        usingManagedDisks = all(
            disk.managed_disk is not None for disk in [vm.storage_profile.os_disk] + vm.storage_profile.data_disks
        )

        # this is a failing check
        if usingManagedDisks is False:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{azSubId}/{azRegion}/{vm.id}/az-vm-utilizing-managed-disks-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{azSubId}/{azRegion}/{vm.id}/az-vm-utilizing-managed-disks-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "LOW"},
                "Confidence": 99,
                "Title": "[Azure.VirtualMachines.2] Azure Virtual Machines should utilize Managed Disks for storage",
                "Description": f"Azure Virtual Machine instance {vmName} in Subscription {azSubId} in {azRegion} does not utilize Managed Disks for storage. Managed Disks are the new and recommended disk storage offering for use with Azure Virtual Machines for better reliability, availability, and security. Managed Disks provide better reliability for Availability Sets by ensuring that the disks of VMs in an Availability Set are sufficiently isolated from each other to avoid single points of failure. Managed Disks also provide better security by encrypting the disks by default. Refer to the remediation instructions if this configuration is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "To migrate your Azure Virtual Machine instance to Managed Disks refer to the Migrate to Managed Disks documentation.",
                        "Url": "https://docs.microsoft.com/en-us/azure/virtual-machines/windows/convert-unmanaged-to-managed-disks"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "Azure",
                    "ProviderType": "CSP",
                    "ProviderAccountId": azSubId,
                    "AssetRegion": azRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Compute",
                    "AssetService": "Azure Virtual Machine",
                    "AssetComponent": "Instance"
                },
                "Resources": [
                    {
                        "Type": "AzureVirtualMachineInstance",
                        "Id": vm.id,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "SubscriptionId": azSubId,
                                "ResourceGroupName": rgName,
                                "Region": azRegion,
                                "Name": vmName,
                                "Id": vm.id
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.DS-1",
                        "NIST SP 800-53 Rev. 4 MP-8",
                        "NIST SP 800-53 Rev. 4 SC-12",
                        "NIST SP 800-53 Rev. 4 SC-28",
                        "AICPA TSC CC6.1",
                        "ISO 27001:2013 A.8.2.3",
                        "CIS Microsoft Azure Foundations Benchmark V2.0.0 7.2",
                        "MITRE ATT&CK T1530"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE"
            }
            yield finding
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{azSubId}/{azRegion}/{vm.id}/az-vm-utilizing-managed-disks-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{azSubId}/{azRegion}/{vm.id}/az-vm-utilizing-managed-disks-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[Azure.VirtualMachines.2] Azure Virtual Machines should utilize Managed Disks for storage",
                "Description": f"Azure Virtual Machine instance {vmName} in Subscription {azSubId} in {azRegion} does utilize Managed Disks for storage.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "To migrate your Azure Virtual Machine instance to Managed Disks refer to the Migrate to Managed Disks documentation.",
                        "Url": "https://docs.microsoft.com/en-us/azure/virtual-machines/windows/convert-unmanaged-to-managed-disks"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "Azure",
                    "ProviderType": "CSP",
                    "ProviderAccountId": azSubId,
                    "AssetRegion": azRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Compute",
                    "AssetService": "Azure Virtual Machine",
                    "AssetComponent": "Instance"
                },
                "Resources": [
                    {
                        "Type": "AzureVirtualMachineInstance",
                        "Id": vm.id,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "SubscriptionId": azSubId,
                                "ResourceGroupName": rgName,
                                "Region": azRegion,
                                "Name": vmName,
                                "Id": vm.id
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.DS-1",
                        "NIST SP 800-53 Rev. 4 MP-8",
                        "NIST SP 800-53 Rev. 4 SC-12",
                        "NIST SP 800-53 Rev. 4 SC-28",
                        "AICPA TSC CC6.1",
                        "ISO 27001:2013 A.8.2.3",
                        "CIS Microsoft Azure Foundations Benchmark V2.0.0 7.2",
                        "MITRE ATT&CK T1530"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED"
            }
            yield finding

@registry.register_check("azure.virtual_machines")
def azure_vm_encrypt_os_and_data_disk_with_cmk_check(cache: dict, awsAccountId: str, awsRegion: str, awsPartition: str, azureCredential, azSubId: str) -> dict:
    """
    [Azure.VirtualMachines.3] Azure Virtual Machines should encrypt both the OS and Data disks with a Customer Managed Key (CMK)
    """
    azComputeClient = ComputeManagementClient(azureCredential,azSubId)
    # ISO Time
    iso8601Time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for vm in get_all_azure_vms(cache, azureCredential, azSubId):
        # B64 encode all of the details for the Asset
        assetJson = json.dumps(vm,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        rgName = process_resource_group_name(vm.id)
        azRegion = vm.location
        vmName = vm.name

        # Check if the OS Disk and all Data Disks have a key
        osDiskEncryptedWithCMK = False
        dataDisksEncryptedWithCMK = False
        # Check OS Disk for CMK Encryption
        if vm.storage_profile.os_disk.managed_disk:
            osDisk = azComputeClient.disks.get(rgName, vm.storage_profile.os_disk.name)
            if osDisk.encryption:
                osDiskEncryptedWithCMK = osDisk.encryption.type == "EncryptionAtRestWithCustomerKey"
        # Check Data Disks for CMK Encryption
        if vm.storage_profile.data_disks:
            dataDisksEncryptedWithCMK = all(
                azComputeClient.disks.get(rgName, disk.name).encryption.type == "EncryptionAtRestWithCustomerKey"
                for disk in vm.storage_profile.data_disks if disk.managed_disk
            )
        # Final condition to check if both OS and Data Disks are encrypted with CMK
        bothEncryptedWithCMK = osDiskEncryptedWithCMK and dataDisksEncryptedWithCMK

        # this is a failing check
        if bothEncryptedWithCMK is False:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{azSubId}/{azRegion}/{vm.id}/az-vm-os-and-disk-cmk-encryption-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{azSubId}/{azRegion}/{vm.id}/az-vm-os-and-disk-cmk-encryption-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "LOW"},
                "Confidence": 99,
                "Title": "[Azure.VirtualMachines.3] Azure Virtual Machines should encrypt both the OS and Data disks with a Customer Managed Key (CMK)",
                "Description": f"Azure Virtual Machine instance {vmName} in Subscription {azSubId} in {azRegion} does not use a CMK for both OS and Data disks. Encrypting the IaaS VM's OS disk (boot volume) and Data disks (non-boot volume) ensures that the entire content is fully unrecoverable without a key, thus protecting the volume from unwanted reads. PMK (Platform Managed Keys) are enabled by default in Azure-managed disks and allow encryption at rest. CMK is recommended because it gives the customer the option to control which specific keys are used for the encryption and decryption of the disk. The customer can then change keys and increase security by disabling them instead of relying on the PMK key that remains unchanging. There is also the option to increase security further by using automatically rotating keys so that access to disk is ensured to be limited. Organizations should evaluate what their security requirements are, however, for the data stored on the disk. For high-risk data using CMK is a must, as it provides extra steps of security. If the data is low risk, PMK is enabled by default and provides sufficient data security. Refer to the remediation instructions if this configuration is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your Azure Virtual Machine instance should CMKs for both their OS and Data disks refer to the Azure data security and encryption best practices section of the Azure Security Fundamentals guide.",
                        "Url": "https://learn.microsoft.com/en-us/azure/security/fundamentals/data-encryption-best-practices"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "Azure",
                    "ProviderType": "CSP",
                    "ProviderAccountId": azSubId,
                    "AssetRegion": azRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Compute",
                    "AssetService": "Azure Virtual Machine",
                    "AssetComponent": "Instance"
                },
                "Resources": [
                    {
                        "Type": "AzureVirtualMachineInstance",
                        "Id": vm.id,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "SubscriptionId": azSubId,
                                "ResourceGroupName": rgName,
                                "Region": azRegion,
                                "Name": vmName,
                                "Id": vm.id
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.DS-1",
                        "NIST SP 800-53 Rev. 4 MP-8",
                        "NIST SP 800-53 Rev. 4 SC-12",
                        "NIST SP 800-53 Rev. 4 SC-28",
                        "AICPA TSC CC6.1",
                        "ISO 27001:2013 A.8.2.3",
                        "CIS Microsoft Azure Foundations Benchmark V2.0.0 7.3",
                        "MITRE ATT&CK T1530"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE"
            }
            yield finding
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{azSubId}/{azRegion}/{vm.id}/az-vm-os-and-disk-cmk-encryption-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{azSubId}/{azRegion}/{vm.id}/az-vm-os-and-disk-cmk-encryption-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[Azure.VirtualMachines.3] Azure Virtual Machines should encrypt both the OS and Data disks with a Customer Managed Key (CMK)",
                "Description": f"Azure Virtual Machine instance {vmName} in Subscription {azSubId} in {azRegion} does use a CMK for both OS and Data disks.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your Azure Virtual Machine instance should CMKs for both their OS and Data disks refer to the Azure data security and encryption best practices section of the Azure Security Fundamentals guide.",
                        "Url": "https://learn.microsoft.com/en-us/azure/security/fundamentals/data-encryption-best-practices"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "Azure",
                    "ProviderType": "CSP",
                    "ProviderAccountId": azSubId,
                    "AssetRegion": azRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Compute",
                    "AssetService": "Azure Virtual Machine",
                    "AssetComponent": "Instance"
                },
                "Resources": [
                    {
                        "Type": "AzureVirtualMachineInstance",
                        "Id": vm.id,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "SubscriptionId": azSubId,
                                "ResourceGroupName": rgName,
                                "Region": azRegion,
                                "Name": vmName,
                                "Id": vm.id
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.DS-1",
                        "NIST SP 800-53 Rev. 4 MP-8",
                        "NIST SP 800-53 Rev. 4 SC-12",
                        "NIST SP 800-53 Rev. 4 SC-28",
                        "AICPA TSC CC6.1",
                        "ISO 27001:2013 A.8.2.3",
                        "CIS Microsoft Azure Foundations Benchmark V2.0.0 7.3",
                        "MITRE ATT&CK T1530"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED"
            }
            yield finding

@registry.register_check("azure.virtual_machines")
def azure_vm_unattached_disks_cmk_encryption_check(cache: dict, awsAccountId: str, awsRegion: str, awsPartition: str, azureCredential, azSubId: str) -> dict:
    """
    [Azure.VirtualMachines.4] Ensure that unattached disks are encrypted with a Customer Managed Key (CMK)
    """
    azComputeClient = ComputeManagementClient(azureCredential, azSubId)
    # ISO Time
    iso8601Time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    for rg in get_all_azure_rgs(cache, azureCredential, azSubId):
        disks = azComputeClient.disks.list_by_resource_group(rg.name)
        for disk in disks:
            unattachedDisksEncryptedWithCmk = True
            # B64 encode all of the details for the Asset
            assetJson = json.dumps(disk,default=str).encode("utf-8")
            assetB64 = base64.b64encode(assetJson)
            rgName = rg.name
            azRegion = disk.location
            diskName = disk.name
            if disk.managed_by is None:
                if not (disk.encryption and disk.encryption.type == "EncryptionAtRestWithCustomerKey"):
                    unattachedDisksEncryptedWithCmk = False
                    break  # break as one unencrypted disk is enough to require action for CIS check

        # this is a failing check
        if unattachedDisksEncryptedWithCmk is False:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{azSubId}/{azRegion}/{disk.id}/az-vm-unattached-disks-cmk-encryption-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{azSubId}/{azRegion}/{disk.id}/az-vm-unattached-disks-cmk-encryption-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "LOW"},
                "Confidence": 99,
                "Title": "[Azure.VirtualMachines.4] Ensure that unattached disks are encrypted with a Customer Managed Key (CMK)",
                "Description": f"Unattached disk {diskName} in Resource Group {rgName} in Subscription {azSubId} in {azRegion} is not encrypted with a CMK. Encrypting the IaaS VM's unattached disks (non-boot volume) ensures that the entire content is fully unrecoverable without a key, thus protecting the volume from unwanted reads. PMK (Platform Managed Keys) are enabled by default in Azure-managed disks and allow encryption at rest. CMK is recommended because it gives the customer the option to control which specific keys are used for the encryption and decryption of the disk. The customer can then change keys and increase security by disabling them instead of relying on the PMK key that remains unchanging. There is also the option to increase security further by using automatically rotating keys so that access to disk is ensured to be limited. Organizations should evaluate what their security requirements are, however, for the data stored on the disk. For high-risk data using CMK is a must, as it provides extra steps of security. If the data is low risk, PMK is enabled by default and provides sufficient data security. Refer to the remediation instructions if this configuration is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "To encrypt your unattached disks with a CMK refer to the Azure data security and encryption best practices section of the Azure Security Fundamentals guide.",
                        "Url": "https://learn.microsoft.com/en-us/azure/security/fundamentals/data-encryption-best-practices"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "Azure",
                    "ProviderType": "CSP",
                    "ProviderAccountId": azSubId,
                    "AssetRegion": azRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Storage",
                    "AssetService": "Azure Disk Storage",
                    "AssetComponent": "Disk"
                },
                "Resources": [
                    {
                        "Type": "AzureDisk",
                        "Id": disk.id,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "SubscriptionId": azSubId,
                                "ResourceGroupName": rgName,
                                "Region": azRegion,
                                "Name": diskName,
                                "Id": disk.id
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.DS-1",
                        "NIST SP 800-53 Rev. 4 MP-8",
                        "NIST SP 800-53 Rev. 4 SC-12",
                        "NIST SP 800-53 Rev. 4 SC-28",
                        "AICPA TSC CC6.1",
                        "ISO 27001:2013 A.8.2.3",
                        "CIS Microsoft Azure Foundations Benchmark V2.0.0 7.4",
                        "MITRE ATT&CK T1530"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE"
            }
            yield finding
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{azSubId}/{azRegion}/{disk.id}/az-vm-unattached-disks-cmk-encryption-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{azSubId}/{azRegion}/{disk.id}/az-vm-unattached-disks-cmk-encryption-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[Azure.VirtualMachines.4] Ensure that unattached disks are encrypted with a Customer Managed Key (CMK)",
                "Description": f"Unattached disk {diskName} in Resource Group {rgName} in Subscription {azSubId} in {azRegion} is encrypted with a CMK.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "To encrypt your unattached disks with a CMK refer to the Azure data security and encryption best practices section of the Azure Security Fundamentals guide.",
                        "Url": "https://learn.microsoft.com/en-us/azure/security/fundamentals/data-encryption-best-practices"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "Azure",
                    "ProviderType": "CSP",
                    "ProviderAccountId": azSubId,
                    "AssetRegion": azRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Storage",
                    "AssetService": "Azure Disk Storage",
                    "AssetComponent": "Disk"
                },
                "Resources": [
                    {
                        "Type": "AzureDisk",
                        "Id": disk.id,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "SubscriptionId": azSubId,
                                "ResourceGroupName": rgName,
                                "Region": azRegion,
                                "Name": diskName,
                                "Id": disk.id
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.DS-1",
                        "NIST SP 800-53 Rev. 4 MP-8",
                        "NIST SP 800-53 Rev. 4 SC-12",
                        "NIST SP 800-53 Rev. 4 SC-28",
                        "AICPA TSC CC6.1",
                        "ISO 27001:2013 A.8.2.3",
                        "CIS Microsoft Azure Foundations Benchmark V2.0.0 7.4",
                        "MITRE ATT&CK T1530"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED"
            }
            yield finding

@registry.register_check("azure.virtual_machines")
def azure_vm_monitoring_agent_installed_check(cache: dict, awsAccountId: str, awsRegion: str, awsPartition: str, azureCredential, azSubId: str) -> dict:
    """
    [Azure.VirtualMachines.5] Azure Virtual Machines should have the Azure Monitor Agent installed
    """
    azComputeClient = ComputeManagementClient(azureCredential, azSubId)
    # ISO Time
    iso8601Time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for vm in get_all_azure_vms(cache, azureCredential, azSubId):
        # B64 encode all of the details for the Asset
        assetJson = json.dumps(vm,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        rgName = process_resource_group_name(vm.id)
        azRegion = vm.location
        vmName = vm.name

        # Check if the VM has the Azure Monitor Agent installed
        monitoringAgentInstalled = False
        extensions = azComputeClient.virtual_machine_extensions.list(rgName, vmName)
        if hasattr(extensions, 'value'):  # Checking if 'value' attribute exists
            for ext in extensions.value:
                if "MicrosoftMonitoringAgent" in ext.name:
                    monitoringAgentInstalled = True
                    break

        # this is a failing check
        if monitoringAgentInstalled is False:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{azSubId}/{azRegion}/{vm.id}/az-vm-monitoring-agent-installed-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{azSubId}/{azRegion}/{vm.id}/az-vm-monitoring-agent-installed-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "LOW"},
                "Confidence": 99,
                "Title": "[Azure.VirtualMachines.5] Azure Virtual Machines should have the Azure Monitor Agent installed",
                "Description": f"Azure Virtual Machine instance {vmName} in Subscription {azSubId} in {azRegion} does not have the Azure Monitor Agent installed. The Azure Monitor Agent collects monitoring data from Azure Virtual Machines and sends it to the Azure Monitor service. The agent collects monitoring data from the guest operating system and workloads of Azure Virtual Machines. The agent is designed to be used with the Azure Monitor service and other monitoring solutions to provide insights into the performance and operation of the applications and workloads running on the virtual machines. Refer to the remediation instructions if this configuration is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "To install the Azure Monitor Agent on your Azure Virtual Machine instance refer to the Azure Monitor Agent documentation.",
                        "Url": "https://docs.microsoft.com/en-us/azure/azure-monitor/agents/agents-overview"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "Azure",
                    "ProviderType": "CSP",
                    "ProviderAccountId": azSubId,
                    "AssetRegion": azRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Compute",
                    "AssetService": "Azure Virtual Machine",
                    "AssetComponent": "Instance"
                },
                "Resources": [
                    {
                        "Type": "AzureVirtualMachineInstance",
                        "Id": vm.id,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "SubscriptionId": azSubId,
                                "ResourceGroupName": rgName,
                                "Region": azRegion,
                                "Name": vmName,
                                "Id": vm.id
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.IP-10",
                        "NIST SP 800-53 Rev. 4 SI-4",
                        "NIST SP 800-53 Rev. 4 SI-5",
                        "NIST SP 800-53 Rev. 4 SI-6",
                        "AICPA TSC CC6.1",
                        "ISO 27001:2013 A.12.4.1",
                        "CIS Microsoft Azure Foundations Benchmark V2.0.0 7.5",
                        "MITRE ATT&CK T1553"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE"
            }
            yield finding
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{azSubId}/{azRegion}/{vm.id}/az-vm-monitoring-agent-installed-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{azSubId}/{azRegion}/{vm.id}/az-vm-monitoring-agent-installed-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[Azure.VirtualMachines.5] Azure Virtual Machines should have the Azure Monitor Agent installed",
                "Description": f"Azure Virtual Machine instance {vmName} in Subscription {azSubId} in {azRegion} does have the Azure Monitor Agent installed.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "To install the Azure Monitor Agent on your Azure Virtual Machine instance refer to the Azure Monitor Agent documentation.",
                        "Url": "https://docs.microsoft.com/en-us/azure/azure-monitor/agents/agents-overview"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "Azure",
                    "ProviderType": "CSP",
                    "ProviderAccountId": azSubId,
                    "AssetRegion": azRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Compute",
                    "AssetService": "Azure Virtual Machine",
                    "AssetComponent": "Instance"
                },
                "Resources": [
                    {
                        "Type": "AzureVirtualMachineInstance",
                        "Id": vm.id,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "SubscriptionId": azSubId,
                                "ResourceGroupName": rgName,
                                "Region": azRegion,
                                "Name": vmName,
                                "Id": vm.id
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.IP-10",
                        "NIST SP 800-53 Rev. 4 SI-4",
                        "NIST SP 800-53 Rev. 4 SI-5",
                        "NIST SP 800-53 Rev. 4 SI-6",
                        "AICPA TSC CC6.1",
                        "ISO 27001:2013 A.12.4.1",
                        "CIS Microsoft Azure Foundations Benchmark V2.0.0 7.5",
                        "MITRE ATT&CK T1553"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED"
            }
            yield finding
            
@registry.register_check("azure.virtual_machines")
def azure_vm_azure_backup_coverage_check(cache: dict, awsAccountId: str, awsRegion: str, awsPartition: str, azureCredential, azSubId: str) -> dict:
    """
    [Azure.VirtualMachines.6] Azure Virtual Machines should have Azure Backup coverage
    """
    azBackupClient = RecoveryServicesBackupClient(azureCredential, azSubId)
    azRecoverySvcClient = RecoveryServicesClient(azureCredential, azSubId)
    # ISO Time
    iso8601Time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for vm in get_all_azure_vms(cache, azureCredential, azSubId):
        # B64 encode all of the details for the asset
        assetJson = json.dumps(vm,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        rgName = process_resource_group_name(vm.id)
        azRegion = vm.location
        vmName = vm.name
        vmId = vm.id

        backupCoverage = False
        vaultFound = False

        for vault in azRecoverySvcClient.vaults.list_by_subscription_id():
            vaultFound = True
            vaultName = vault.name
            resourceGroupName = vault.id.split("/")[4]  # Extracting resource group name from vault ID
            
            # List backup items (protected items) in the vault
            backupItems = azBackupClient.backup_protected_items.list(
                vault_name=vaultName,
                resource_group_name=resourceGroupName,
                filter="backupManagementType eq 'AzureIaasVM' and itemType eq 'VM'"
            )
            
            for item in backupItems:
                if vmId in item.properties.virtual_machine_id:
                    backupCoverage = True
                    break
            
            if backupCoverage:
                break

        # this is a failing check
        if not vaultFound or not backupCoverage:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{azSubId}/{azRegion}/{vm.id}/az-vm-azure-backup-coverage-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{azSubId}/{azRegion}/{vm.id}/az-vm-azure-backup-coverage-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "MEDIUM"},
                "Confidence": 99,
                "Title": "[Azure.VirtualMachines.6] Azure Virtual Machines should have Azure Backup coverage",
                "Description": f"Azure Virtual Machine instance {vmName} in Subscription {azSubId} in {azRegion} does not have Azure Backup coverage. Azure Backup is a scalable solution with zero-infrastructure maintenance that protects your data from security threats and data loss. Azure Backup provides independent and isolated backups to guard against accidental destruction of original data. Azure Backup also provides the ability to restore VMs to a previous state, which is essential for disaster recovery. Refer to the remediation instructions if this configuration is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "To enable Azure Backup coverage for your Azure Virtual Machine instance refer to the Back up an Azure VM from the VM settings section of the Azure Backup documentation.",
                        "Url": "https://docs.microsoft.com/en-us/azure/backup/backup-azure-vms-first-look-arm"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "Azure",
                    "ProviderType": "CSP",
                    "ProviderAccountId": azSubId,
                    "AssetRegion": azRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Compute",
                    "AssetService": "Azure Virtual Machine",
                    "AssetComponent": "Instance"
                },
                "Resources": [
                    {
                        "Type": "AzureVirtualMachineInstance",
                        "Id": vm.id,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "SubscriptionId": azSubId,
                                "ResourceGroupName": rgName,
                                "Region": azRegion,
                                "Name": vmName,
                                "Id": vm.id
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 ID.BE-5",
                        "NIST CSF V1.1 PR.IP-4",
                        "NIST CSF V1.1 PR.PT-5",
                        "NIST SP 800-53 Rev. 4 CP-2",
                        "NIST SP 800-53 Rev. 4 CP-4",
                        "NIST SP 800-53 Rev. 4 CP-6",
                        "NIST SP 800-53 Rev. 4 CP-7",
                        "NIST SP 800-53 Rev. 4 CP-8",
                        "NIST SP 800-53 Rev. 4 CP-9",
                        "NIST SP 800-53 Rev. 4 CP-11",
                        "NIST SP 800-53 Rev. 4 CP-13",
                        "NIST SP 800-53 Rev. 4 PL-8",
                        "NIST SP 800-53 Rev. 4 SA-14",
                        "NIST SP 800-53 Rev. 4 SC-6",
                        "AICPA TSC A1.2",
                        "AICPA TSC A1.3",
                        "AICPA TSC CC3.1",
                        "ISO 27001:2013 A.11.1.4",
                        "ISO 27001:2013 A.12.3.1",
                        "ISO 27001:2013 A.17.1.1",
                        "ISO 27001:2013 A.17.1.2",
                        "ISO 27001:2013 A.17.1.3",
                        "ISO 27001:2013 A.17.2.1",
                        "ISO 27001:2013 A.18.1.3"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE"
            }
            yield finding
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{azSubId}/{azRegion}/{vm.id}/az-vm-azure-backup-coverage-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{azSubId}/{azRegion}/{vm.id}/az-vm-azure-backup-coverage-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[Azure.VirtualMachines.6] Azure Virtual Machines should have Azure Backup coverage",
                "Description": f"Azure Virtual Machine instance {vmName} in Subscription {azSubId} in {azRegion} does have Azure Backup coverage.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "To enable Azure Backup coverage for your Azure Virtual Machine instance refer to the Back up an Azure VM from the VM settings section of the Azure Backup documentation.",
                        "Url": "https://docs.microsoft.com/en-us/azure/backup/backup-azure-vms-first-look-arm"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "Azure",
                    "ProviderType": "CSP",
                    "ProviderAccountId": azSubId,
                    "AssetRegion": azRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Compute",
                    "AssetService": "Azure Virtual Machine",
                    "AssetComponent": "Instance"
                },
                "Resources": [
                    {
                        "Type": "AzureVirtualMachineInstance",
                        "Id": vm.id,
                        "Partition": awsPartition,
                        "Region": awsRegion,
                        "Details": {
                            "Other": {
                                "SubscriptionId": azSubId,
                                "ResourceGroupName": rgName,
                                "Region": azRegion,
                                "Name": vmName,
                                "Id": vm.id
                            }
                        }
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 ID.BE-5",
                        "NIST CSF V1.1 PR.IP-4",
                        "NIST CSF V1.1 PR.PT-5",
                        "NIST SP 800-53 Rev. 4 CP-2",
                        "NIST SP 800-53 Rev. 4 CP-4",
                        "NIST SP 800-53 Rev. 4 CP-6",
                        "NIST SP 800-53 Rev. 4 CP-7",
                        "NIST SP 800-53 Rev. 4 CP-8",
                        "NIST SP 800-53 Rev. 4 CP-9",
                        "NIST SP 800-53 Rev. 4 CP-11",
                        "NIST SP 800-53 Rev. 4 CP-13",
                        "NIST SP 800-53 Rev. 4 PL-8",
                        "NIST SP 800-53 Rev. 4 SA-14",
                        "NIST SP 800-53 Rev. 4 SC-6",
                        "AICPA TSC A1.2",
                        "AICPA TSC A1.3",
                        "AICPA TSC CC3.1",
                        "ISO 27001:2013 A.11.1.4",
                        "ISO 27001:2013 A.12.3.1",
                        "ISO 27001:2013 A.17.1.1",
                        "ISO 27001:2013 A.17.1.2",
                        "ISO 27001:2013 A.17.1.3",
                        "ISO 27001:2013 A.17.2.1",
                        "ISO 27001:2013 A.18.1.3"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED"
            }
            yield finding