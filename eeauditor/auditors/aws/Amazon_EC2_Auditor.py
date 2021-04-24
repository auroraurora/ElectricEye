# This file is part of ElectricEye.

# ElectricEye is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# ElectricEye is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with ElectricEye.
# If not, see https://github.com/jonrau1/ElectricEye/blob/master/LICENSE.

import boto3
import datetime
from check_register import CheckRegister
from dateutil.parser import parse

registry = CheckRegister()

ec2 = boto3.client("ec2")
paginator = ec2.get_paginator("describe_instances")


@registry.register_check("ec2")
def ec2_imdsv2_check(cache: dict, awsAccountId: str, awsRegion: str, awsPartition: str) -> dict:
    try:
        iterator = paginator.paginate(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': [
                        'running',
                        'stopped'
                    ]
                },
            ]
        )
        for page in iterator:
            for r in page["Reservations"]:
                for i in r["Instances"]:
                    instanceId = str(i["InstanceId"])
                    instanceArn = (f"arn:{awsPartition}:ec2:{awsRegion}:{awsAccountId}:instance/{instanceId}")
                    instanceType = str(i["InstanceType"])
                    instanceImage = str(i["ImageId"])
                    subnetId = str(i["SubnetId"])
                    vpcId = str(i["VpcId"])
                    instanceLaunchedAt = str(i["BlockDeviceMappings"][0]["Ebs"]["AttachTime"])
                    metadataServiceCheck = str(i["MetadataOptions"]["HttpEndpoint"])
                    if metadataServiceCheck == "enabled":
                        imdsv2Check = str(i["MetadataOptions"]["HttpTokens"])
                        if imdsv2Check != "required":
                            try:
                                # ISO Time
                                iso8601Time = (
                                    datetime.datetime.utcnow()
                                    .replace(tzinfo=datetime.timezone.utc)
                                    .isoformat()
                                )
                                # create Sec Hub finding
                                finding = {
                                    "SchemaVersion": "2018-10-08",
                                    "Id": instanceArn + "/ec2-imdsv2-check",
                                    "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                                    "GeneratorId": instanceArn,
                                    "AwsAccountId": awsAccountId,
                                    "Types": [
                                        "Software and Configuration Checks/AWS Security Best Practices"
                                    ],
                                    "FirstObservedAt": iso8601Time,
                                    "CreatedAt": iso8601Time,
                                    "UpdatedAt": iso8601Time,
                                    "Severity": {"Label": "MEDIUM"},
                                    "Confidence": 99,
                                    "Title": "[EC2.1] EC2 Instances should be configured to use instance metadata service V2 (IMDSv2)",
                                    "Description": "EC2 Instance "
                                    + instanceId
                                    + " is not configured to use instance metadata service V2 (IMDSv2). IMDSv2 adds new “belt and suspenders” protections for four types of vulnerabilities that could be used to try to access the IMDS. These new protections go well beyond other types of mitigations, while working seamlessly with existing mitigations such as restricting IAM roles and using local firewall rules to restrict access to the IMDS. Refer to the remediation instructions if this configuration is not intended",
                                    "Remediation": {
                                        "Recommendation": {
                                            "Text": "To learn how to configure IMDSv2 refer to the Transitioning to Using Instance Metadata Service Version 2 section of the Amazon EC2 User Guide",
                                            "Url": "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html#instance-metadata-transition-to-version-2",
                                        }
                                    },
                                    "ProductFields": {"Product Name": "ElectricEye"},
                                    "Resources": [
                                        {
                                            "Type": "AwsEc2Instance",
                                            "Id": instanceArn,
                                            "Partition": awsPartition,
                                            "Region": awsRegion,
                                            "Details": {
                                                "AwsEc2Instance": {
                                                    "Type": instanceType,
                                                    "ImageId": instanceImage,
                                                    "VpcId": vpcId,
                                                    "SubnetId": subnetId,
                                                    "LaunchedAt": parse(instanceLaunchedAt).isoformat(),
                                                }
                                            },
                                        }
                                    ],
                                    "Compliance": {
                                        "Status": "FAILED",
                                        "RelatedRequirements": [
                                            "NIST CSF PR.AC-4",
                                            "NIST SP 800-53 AC-1",
                                            "NIST SP 800-53 AC-2",
                                            "NIST SP 800-53 AC-3",
                                            "NIST SP 800-53 AC-5",
                                            "NIST SP 800-53 AC-6",
                                            "NIST SP 800-53 AC-14",
                                            "NIST SP 800-53 AC-16",
                                            "NIST SP 800-53 AC-24",
                                            "AICPA TSC CC6.3",
                                            "ISO 27001:2013 A.6.1.2",
                                            "ISO 27001:2013 A.9.1.2",
                                            "ISO 27001:2013 A.9.2.3",
                                            "ISO 27001:2013 A.9.4.1",
                                            "ISO 27001:2013 A.9.4.4",
                                            "ISO 27001:2013 A.9.4.5",
                                        ],
                                    },
                                    "Workflow": {"Status": "NEW"},
                                    "RecordState": "ACTIVE",
                                }
                                yield finding
                            except Exception as e:
                                print(e)
                        else:
                            try:
                                # ISO Time
                                iso8601Time = (
                                    datetime.datetime.utcnow()
                                    .replace(tzinfo=datetime.timezone.utc)
                                    .isoformat()
                                )
                                # create Sec Hub finding
                                finding = {
                                    "SchemaVersion": "2018-10-08",
                                    "Id": instanceArn + "/ec2-imdsv2-check",
                                    "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                                    "GeneratorId": instanceArn,
                                    "AwsAccountId": awsAccountId,
                                    "Types": [
                                        "Software and Configuration Checks/AWS Security Best Practices"
                                    ],
                                    "FirstObservedAt": iso8601Time,
                                    "CreatedAt": iso8601Time,
                                    "UpdatedAt": iso8601Time,
                                    "Severity": {"Label": "INFORMATIONAL"},
                                    "Confidence": 99,
                                    "Title": "[EC2.1] EC2 Instances should be configured to use instance metadata service V2 (IMDSv2)",
                                    "Description": "EC2 Instance "
                                    + instanceId
                                    + " is using instance metadata service V2 (IMDSv2). IMDSv2 adds new “belt and suspenders” protections for four types of vulnerabilities that could be used to try to access the IMDS. These new protections go well beyond other types of mitigations, while working seamlessly with existing mitigations such as restricting IAM roles and using local firewall rules to restrict access to the IMDS. Refer to the remediation instructions if this configuration is not intended",
                                    "Remediation": {
                                        "Recommendation": {
                                            "Text": "To learn how to configure IMDSv2 refer to the Transitioning to Using Instance Metadata Service Version 2 section of the Amazon EC2 User Guide",
                                            "Url": "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html#instance-metadata-transition-to-version-2",
                                        }
                                    },
                                    "ProductFields": {"Product Name": "ElectricEye"},
                                    "Resources": [
                                        {
                                            "Type": "AwsEc2Instance",
                                            "Id": instanceArn,
                                            "Partition": awsPartition,
                                            "Region": awsRegion,
                                            "Details": {
                                                "AwsEc2Instance": {
                                                    "Type": instanceType,
                                                    "ImageId": instanceImage,
                                                    "VpcId": vpcId,
                                                    "SubnetId": subnetId,
                                                    "LaunchedAt": parse(instanceLaunchedAt).isoformat(),
                                                }
                                            },
                                        }
                                    ],
                                    "Compliance": {
                                        "Status": "PASSED",
                                        "RelatedRequirements": ["NIST CSF PR.PT-3"],
                                    },
                                    "Workflow": {"Status": "RESOLVED"},
                                    "RecordState": "ARCHIVED",
                                }
                                yield finding
                            except Exception as e:
                                print(e)
                    else:
                        pass
        except Exception as e:
            print(e)
            continue

@registry.register_check("ec2")
def ec2_secure_enclave_check(cache: dict, awsAccountId: str, awsRegion: str, awsPartition: str) -> dict:
    try:
        iterator = paginator.paginate(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': [
                        'running',
                        'stopped'
                    ]
                },
            ]
        )
        for page in iterator:
            for r in page["Reservations"]:
                for i in r["Instances"]:
                    instanceId = str(i["InstanceId"])
                    instanceArn = (f"arn:{awsPartition}:ec2:{awsRegion}:{awsAccountId}:instance/{instanceId}")
                    instanceType = str(i["InstanceType"])
                    instanceImage = str(i["ImageId"])
                    subnetId = str(i["SubnetId"])
                    vpcId = str(i["VpcId"])
                    instanceLaunchedAt = str(i["BlockDeviceMappings"][0]["Ebs"]["AttachTime"])
                    if str(i["EnclaveOptions"]["Enabled"]) == "False":
                        # ISO Time
                        iso8601Time = (
                            datetime.datetime.utcnow()
                            .replace(tzinfo=datetime.timezone.utc)
                            .isoformat()
                        )
                        # create Sec Hub finding
                        finding = {
                            "SchemaVersion": "2018-10-08",
                            "Id": instanceArn + "/ec2-enclave-check",
                            "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                            "GeneratorId": instanceArn,
                            "AwsAccountId": awsAccountId,
                            "Types": [
                                "Software and Configuration Checks/AWS Security Best Practices"
                            ],
                            "FirstObservedAt": iso8601Time,
                            "CreatedAt": iso8601Time,
                            "UpdatedAt": iso8601Time,
                            "Severity": {"Label": "MEDIUM"},
                            "Confidence": 99,
                            "Title": "[EC2.2] EC2 Instances should be configured to use Secure Enclaves",
                            "Description": "EC2 Instance "
                            + instanceId
                            + " is not configured to use a Secure Enclave. AWS Nitro Enclaves is an Amazon EC2 feature that allows you to create isolated execution environments, called enclaves, from Amazon EC2 instances. Enclaves are separate, hardened, and highly constrained virtual machines. They provide only secure local socket connectivity with their parent instance. Refer to the remediation instructions if this configuration is not intended",
                            "Remediation": {
                                "Recommendation": {
                                    "Text": "To learn how to configure Secure Encalves refer to the Getting started: Hello enclave section of the AWS Nitro Enclaves User Guide",
                                    "Url": "https://docs.aws.amazon.com/enclaves/latest/user/getting-started.html",
                                }
                            },
                            "ProductFields": {"Product Name": "ElectricEye"},
                            "Resources": [
                                {
                                    "Type": "AwsEc2Instance",
                                    "Id": instanceArn,
                                    "Partition": awsPartition,
                                    "Region": awsRegion,
                                    "Details": {
                                        "AwsEc2Instance": {
                                            "Type": instanceType,
                                            "ImageId": instanceImage,
                                            "VpcId": vpcId,
                                            "SubnetId": subnetId,
                                            "LaunchedAt": parse(instanceLaunchedAt).isoformat(),
                                        }
                                    },
                                }
                            ],
                            "Compliance": {
                                "Status": "FAILED",
                                "RelatedRequirements": [
                                    "NIST CSF PR.AC-4",
                                    "NIST SP 800-53 AC-1",
                                    "NIST SP 800-53 AC-2",
                                    "NIST SP 800-53 AC-3",
                                    "NIST SP 800-53 AC-5",
                                    "NIST SP 800-53 AC-6",
                                    "NIST SP 800-53 AC-14",
                                    "NIST SP 800-53 AC-16",
                                    "NIST SP 800-53 AC-24",
                                    "AICPA TSC CC6.3",
                                    "ISO 27001:2013 A.6.1.2",
                                    "ISO 27001:2013 A.9.1.2",
                                    "ISO 27001:2013 A.9.2.3",
                                    "ISO 27001:2013 A.9.4.1",
                                    "ISO 27001:2013 A.9.4.4",
                                    "ISO 27001:2013 A.9.4.5",
                                ],
                            },
                            "Workflow": {"Status": "NEW"},
                            "RecordState": "ACTIVE",
                        }
                        yield finding
                    else:
                        # ISO Time
                        iso8601Time = (
                            datetime.datetime.utcnow()
                            .replace(tzinfo=datetime.timezone.utc)
                            .isoformat()
                        )
                        # create Sec Hub finding
                        finding = {
                            "SchemaVersion": "2018-10-08",
                            "Id": instanceArn + "/ec2-enclave-check",
                            "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                            "GeneratorId": instanceArn,
                            "AwsAccountId": awsAccountId,
                            "Types": [
                                "Software and Configuration Checks/AWS Security Best Practices"
                            ],
                            "FirstObservedAt": iso8601Time,
                            "CreatedAt": iso8601Time,
                            "UpdatedAt": iso8601Time,
                            "Severity": {"Label": "INFORMATIONAL"},
                            "Confidence": 99,
                            "Title": "[EC2.2] EC2 Instances should be configured to use Secure Enclaves",
                            "Description": "EC2 Instance "
                            + instanceId
                            + " is configured to use a Secure Enclave.",
                            "Remediation": {
                                "Recommendation": {
                                    "Text": "To learn how to configure Secure Encalves refer to the Getting started: Hello enclave section of the AWS Nitro Enclaves User Guide",
                                    "Url": "https://docs.aws.amazon.com/enclaves/latest/user/getting-started.html"
                                }
                            },
                            "ProductFields": {"Product Name": "ElectricEye"},
                            "Resources": [
                                {
                                    "Type": "AwsEc2Instance",
                                    "Id": instanceArn,
                                    "Partition": awsPartition,
                                    "Region": awsRegion,
                                    "Details": {
                                        "AwsEc2Instance": {
                                            "Type": instanceType,
                                            "ImageId": instanceImage,
                                            "VpcId": vpcId,
                                            "SubnetId": subnetId,
                                            "LaunchedAt": parse(instanceLaunchedAt).isoformat(),
                                        }
                                    },
                                }
                            ],
                            "Compliance": {
                                "Status": "PASSED",
                                "RelatedRequirements": [
                                    "NIST CSF PR.AC-4",
                                    "NIST SP 800-53 AC-1",
                                    "NIST SP 800-53 AC-2",
                                    "NIST SP 800-53 AC-3",
                                    "NIST SP 800-53 AC-5",
                                    "NIST SP 800-53 AC-6",
                                    "NIST SP 800-53 AC-14",
                                    "NIST SP 800-53 AC-16",
                                    "NIST SP 800-53 AC-24",
                                    "AICPA TSC CC6.3",
                                    "ISO 27001:2013 A.6.1.2",
                                    "ISO 27001:2013 A.9.1.2",
                                    "ISO 27001:2013 A.9.2.3",
                                    "ISO 27001:2013 A.9.4.1",
                                    "ISO 27001:2013 A.9.4.4",
                                    "ISO 27001:2013 A.9.4.5",
                                ],
                            },
                            "Workflow": {"Status": "RESOLVED"},
                            "RecordState": "ARCHIVED"
                        }
                        yield finding
    except Exception as e:
        print(e)
        continue