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

from check_register import CheckRegister
import datetime
import base64
import json

registry = CheckRegister()

def get_all_shadow_trails(cache, session):
    response = cache.get("get_all_shadow_trails")
    if response:
        return response
    
    cloudtrail = session.client("cloudtrail")

    cache["get_all_shadow_trails"] = cloudtrail.describe_trails(includeShadowTrails=True)["trailList"]
    return cache["get_all_shadow_trails"]

@registry.register_check("cloudtrail")
def cloudtrail_multi_region_check(cache: dict, session, awsAccountId: str, awsRegion: str, awsPartition: str) -> dict:
    """[CloudTrail.1] AWS CloudTrail trails should be enabled in all Regions"""
    # ISO Time
    iso8601Time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    for trail in get_all_shadow_trails(cache, session):
        # B64 encode all of the details for the Asset
        assetJson = json.dumps(trail,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        trailArn = trail["TrailARN"]
        trailName = trail["Name"]
        # this is a failing check
        if trail["IsMultiRegionTrail"] is False:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{trailArn}/cloudtrail-multi-region-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{trailArn}/cloudtrail-multi-region-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "MEDIUM"},
                "Confidence": 99,
                "Title": "[CloudTrail.1] AWS CloudTrail trails should be enabled in all Regions",
                "Description": f"AWS CloudTrail trail {trailName} is not a multi-region trail. You can configure CloudTrail to deliver log files from multiple Regions to a single S3 bucket for a single account. For example, you have a trail in the US West (Oregon) Region that is configured to deliver log files to a S3 bucket, and a CloudWatch Logs log group. When you change an existing single-Region trail to log all Regions, CloudTrail logs events from all Regions that are in a single AWS partition in your account. CloudTrail delivers log files to the same S3 bucket and CloudWatch Logs log group. As long as CloudTrail has permissions to write to an S3 bucket, the bucket for a multi-Region trail does not have to be in the trail's home Region. Refer to the remediation instructions if this configuration is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your trail should be multi-region refer to the Receiving CloudTrail Log Files from Multiple Regions section of the AWS CloudTrail User Guide",
                        "Url": "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/receive-cloudtrail-log-files-from-multiple-regions.html"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Management & Governance",
                    "AssetService": "AWS CloudTrail",
                    "AssetComponent": "Trail"
                },
                "Resources": [
                    {
                        "Type": "AwsCloudTrailTrail",
                        "Id": trailArn,
                        "Partition": awsPartition,
                        "Region": awsRegion
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 ID.AM-3",
                        "NIST CSF V1.1 DE.AE-1",
                        "NIST CSF V1.1 DE.AE-3",
                        "NIST CSF V1.1 DE.CM-1",
                        "NIST CSF V1.1 DE.CM-7",
                        "NIST CSF V1.1 PR.PT-1",
                        "NIST SP 800-53 Rev. 4 AC-2",
                        "NIST SP 800-53 Rev. 4 AC-4",
                        "NIST SP 800-53 Rev. 4 AU-6",
                        "NIST SP 800-53 Rev. 4 AU-12",
                        "NIST SP 800-53 Rev. 4 CA-3",
                        "NIST SP 800-53 Rev. 4 CA-7",
                        "NIST SP 800-53 Rev. 4 CA-9",
                        "NIST SP 800-53 Rev. 4 CM-2",
                        "NIST SP 800-53 Rev. 4 CM-3",
                        "NIST SP 800-53 Rev. 4 CM-8",
                        "NIST SP 800-53 Rev. 4 IR-4",
                        "NIST SP 800-53 Rev. 4 IR-5",
                        "NIST SP 800-53 Rev. 4 IR-8",
                        "NIST SP 800-53 Rev. 4 PE-3",
                        "NIST SP 800-53 Rev. 4 PE-6",
                        "NIST SP 800-53 Rev. 4 PE-20",
                        "NIST SP 800-53 Rev. 4 PL-8",
                        "NIST SP 800-53 Rev. 4 SC-5",
                        "NIST SP 800-53 Rev. 4 SC-7",
                        "NIST SP 800-53 Rev. 4 SI-4",
                        "AICPA TSC CC3.2",
                        "AICPA TSC CC6.1",
                        "AICPA TSC CC7.2",
                        "ISO 27001:2013 A.12.1.1",
                        "ISO 27001:2013 A.12.1.2",
                        "ISO 27001:2013 A.12.4.1",
                        "ISO 27001:2013 A.12.4.2",
                        "ISO 27001:2013 A.12.4.3",
                        "ISO 27001:2013 A.12.4.4",
                        "ISO 27001:2013 A.12.7.1",
                        "ISO 27001:2013 A.13.1.1",
                        "ISO 27001:2013 A.13.2.1",
                        "ISO 27001:2013 A.13.2.2",
                        "ISO 27001:2013 A.14.2.7",
                        "ISO 27001:2013 A.15.2.1",
                        "ISO 27001:2013 A.16.1.7",
                        "CIS Amazon Web Services Foundations Benchmark V1.5 3.1"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE"
            }
            yield finding
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{trailArn}/cloudtrail-multi-region-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{trailArn}/cloudtrail-multi-region-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[CloudTrail.1] AWS CloudTrail trails should be enabled in all Regions",
                "Description": f"AWS CloudTrail trail {trailName} is a multi-region trail.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your trail should be multi-region refer to the Receiving CloudTrail Log Files from Multiple Regions section of the AWS CloudTrail User Guide",
                        "Url": "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/receive-cloudtrail-log-files-from-multiple-regions.html"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Management & Governance",
                    "AssetService": "AWS CloudTrail",
                    "AssetComponent": "Trail"
                },
                "Resources": [
                    {
                        "Type": "AwsCloudTrailTrail",
                        "Id": trailArn,
                        "Partition": awsPartition,
                        "Region": awsRegion
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 ID.AM-3",
                        "NIST CSF V1.1 DE.AE-1",
                        "NIST CSF V1.1 DE.AE-3",
                        "NIST CSF V1.1 DE.CM-1",
                        "NIST CSF V1.1 DE.CM-7",
                        "NIST CSF V1.1 PR.PT-1",
                        "NIST SP 800-53 Rev. 4 AC-2",
                        "NIST SP 800-53 Rev. 4 AC-4",
                        "NIST SP 800-53 Rev. 4 AU-6",
                        "NIST SP 800-53 Rev. 4 AU-12",
                        "NIST SP 800-53 Rev. 4 CA-3",
                        "NIST SP 800-53 Rev. 4 CA-7",
                        "NIST SP 800-53 Rev. 4 CA-9",
                        "NIST SP 800-53 Rev. 4 CM-2",
                        "NIST SP 800-53 Rev. 4 CM-3",
                        "NIST SP 800-53 Rev. 4 CM-8",
                        "NIST SP 800-53 Rev. 4 IR-4",
                        "NIST SP 800-53 Rev. 4 IR-5",
                        "NIST SP 800-53 Rev. 4 IR-8",
                        "NIST SP 800-53 Rev. 4 PE-3",
                        "NIST SP 800-53 Rev. 4 PE-6",
                        "NIST SP 800-53 Rev. 4 PE-20",
                        "NIST SP 800-53 Rev. 4 PL-8",
                        "NIST SP 800-53 Rev. 4 SC-5",
                        "NIST SP 800-53 Rev. 4 SC-7",
                        "NIST SP 800-53 Rev. 4 SI-4",
                        "AICPA TSC CC3.2",
                        "AICPA TSC CC6.1",
                        "AICPA TSC CC7.2",
                        "ISO 27001:2013 A.12.1.1",
                        "ISO 27001:2013 A.12.1.2",
                        "ISO 27001:2013 A.12.4.1",
                        "ISO 27001:2013 A.12.4.2",
                        "ISO 27001:2013 A.12.4.3",
                        "ISO 27001:2013 A.12.4.4",
                        "ISO 27001:2013 A.12.7.1",
                        "ISO 27001:2013 A.13.1.1",
                        "ISO 27001:2013 A.13.2.1",
                        "ISO 27001:2013 A.13.2.2",
                        "ISO 27001:2013 A.14.2.7",
                        "ISO 27001:2013 A.15.2.1",
                        "ISO 27001:2013 A.16.1.7",
                        "CIS Amazon Web Services Foundations Benchmark V1.5 3.1"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED"
            }
            yield finding

@registry.register_check("cloudtrail")
def cloudtrail_cloudwatch_logging_check(cache: dict, session, awsAccountId: str, awsRegion: str, awsPartition: str) -> dict:
    """[CloudTrail.2] AWS CloudTrail trails should have CloudWatch logging configured"""
    # ISO Time
    iso8601Time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    for trail in get_all_shadow_trails(cache, session):
        # B64 encode all of the details for the Asset
        assetJson = json.dumps(trail,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        trailArn = trail["TrailARN"]
        trailName = trail["Name"]
        # this is a failing check
        if "CloudWatchLogsLogGroupArn" not in trail:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{trailArn}/cloudtrail-cloudwatch-logging-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{trailArn}/cloudtrail-cloudwatch-logging-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "MEDIUM"},
                "Confidence": 99,
                "Title": "[CloudTrail.2] AWS CloudTrail trails should have CloudWatch logging configured",
                "Description": f"AWS CloudTrail trail {trailName} does not have CloudWatch Logging configured. When you configure your trail to send events to CloudWatch Logs, CloudTrail sends only the events that match your trail settings. For example, if you configure your trail to log data events only, your trail sends data events only to your CloudWatch Logs log group. CloudTrail supports sending data, Insights, and management events to CloudWatch Logs. Make sure you have sufficient permissions to create or specify an IAM role. CloudWatch Logs and EventBridge each allow a maximum event size of 256 KB. Although most service events have a maximum size of 256 KB, some services still have events that are larger. CloudTrail does not send these events to CloudWatch Logs or EventBridge. Refer to the remediation instructions if this configuration is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your trail should send logs to CloudWatch refer to the Monitoring CloudTrail Log Files with Amazon CloudWatch Logs section of the AWS CloudTrail User Guide",
                        "Url": "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/monitor-cloudtrail-log-files-with-cloudwatch-logs.html"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Management & Governance",
                    "AssetService": "AWS CloudTrail",
                    "AssetComponent": "Trail"
                },
                "Resources": [
                    {
                        "Type": "AwsCloudTrailTrail",
                        "Id": trailArn,
                        "Partition": awsPartition,
                        "Region": awsRegion
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 ID.AM-3",
                        "NIST CSF V1.1 DE.AE-1",
                        "NIST CSF V1.1 DE.AE-3",
                        "NIST CSF V1.1 DE.CM-1",
                        "NIST CSF V1.1 DE.CM-7",
                        "NIST CSF V1.1 PR.PT-1",
                        "NIST SP 800-53 Rev. 4 AC-2",
                        "NIST SP 800-53 Rev. 4 AC-4",
                        "NIST SP 800-53 Rev. 4 AU-6",
                        "NIST SP 800-53 Rev. 4 AU-12",
                        "NIST SP 800-53 Rev. 4 CA-3",
                        "NIST SP 800-53 Rev. 4 CA-7",
                        "NIST SP 800-53 Rev. 4 CA-9",
                        "NIST SP 800-53 Rev. 4 CM-2",
                        "NIST SP 800-53 Rev. 4 CM-3",
                        "NIST SP 800-53 Rev. 4 CM-8",
                        "NIST SP 800-53 Rev. 4 IR-4",
                        "NIST SP 800-53 Rev. 4 IR-5",
                        "NIST SP 800-53 Rev. 4 IR-8",
                        "NIST SP 800-53 Rev. 4 PE-3",
                        "NIST SP 800-53 Rev. 4 PE-6",
                        "NIST SP 800-53 Rev. 4 PE-20",
                        "NIST SP 800-53 Rev. 4 PL-8",
                        "NIST SP 800-53 Rev. 4 SC-5",
                        "NIST SP 800-53 Rev. 4 SC-7",
                        "NIST SP 800-53 Rev. 4 SI-4",
                        "AICPA TSC CC3.2",
                        "AICPA TSC CC6.1",
                        "AICPA TSC CC7.2",
                        "ISO 27001:2013 A.12.1.1",
                        "ISO 27001:2013 A.12.1.2",
                        "ISO 27001:2013 A.12.4.1",
                        "ISO 27001:2013 A.12.4.2",
                        "ISO 27001:2013 A.12.4.3",
                        "ISO 27001:2013 A.12.4.4",
                        "ISO 27001:2013 A.12.7.1",
                        "ISO 27001:2013 A.13.1.1",
                        "ISO 27001:2013 A.13.2.1",
                        "ISO 27001:2013 A.13.2.2",
                        "ISO 27001:2013 A.14.2.7",
                        "ISO 27001:2013 A.15.2.1",
                        "ISO 27001:2013 A.16.1.7",
                        "CIS Amazon Web Services Foundations Benchmark V1.5 3.4"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE"
            }
            yield finding   
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{trailArn}/cloudtrail-cloudwatch-logging-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{trailArn}/cloudtrail-cloudwatch-logging-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[CloudTrail.2] AWS CloudTrail trails should have CloudWatch logging configured",
                "Description": f"AWS CloudTrail trail {trailName} does have CloudWatch Logging configured.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your trail should send logs to CloudWatch refer to the Monitoring CloudTrail Log Files with Amazon CloudWatch Logs section of the AWS CloudTrail User Guide",
                        "Url": "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/monitor-cloudtrail-log-files-with-cloudwatch-logs.html"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Management & Governance",
                    "AssetService": "AWS CloudTrail",
                    "AssetComponent": "Trail"
                },
                "Resources": [
                    {
                        "Type": "AwsCloudTrailTrail",
                        "Id": trailArn,
                        "Partition": awsPartition,
                        "Region": awsRegion
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 ID.AM-3",
                        "NIST CSF V1.1 DE.AE-1",
                        "NIST CSF V1.1 DE.AE-3",
                        "NIST CSF V1.1 DE.CM-1",
                        "NIST CSF V1.1 DE.CM-7",
                        "NIST CSF V1.1 PR.PT-1",
                        "NIST SP 800-53 Rev. 4 AC-2",
                        "NIST SP 800-53 Rev. 4 AC-4",
                        "NIST SP 800-53 Rev. 4 AU-6",
                        "NIST SP 800-53 Rev. 4 AU-12",
                        "NIST SP 800-53 Rev. 4 CA-3",
                        "NIST SP 800-53 Rev. 4 CA-7",
                        "NIST SP 800-53 Rev. 4 CA-9",
                        "NIST SP 800-53 Rev. 4 CM-2",
                        "NIST SP 800-53 Rev. 4 CM-3",
                        "NIST SP 800-53 Rev. 4 CM-8",
                        "NIST SP 800-53 Rev. 4 IR-4",
                        "NIST SP 800-53 Rev. 4 IR-5",
                        "NIST SP 800-53 Rev. 4 IR-8",
                        "NIST SP 800-53 Rev. 4 PE-3",
                        "NIST SP 800-53 Rev. 4 PE-6",
                        "NIST SP 800-53 Rev. 4 PE-20",
                        "NIST SP 800-53 Rev. 4 PL-8",
                        "NIST SP 800-53 Rev. 4 SC-5",
                        "NIST SP 800-53 Rev. 4 SC-7",
                        "NIST SP 800-53 Rev. 4 SI-4",
                        "AICPA TSC CC3.2",
                        "AICPA TSC CC6.1",
                        "AICPA TSC CC7.2",
                        "ISO 27001:2013 A.12.1.1",
                        "ISO 27001:2013 A.12.1.2",
                        "ISO 27001:2013 A.12.4.1",
                        "ISO 27001:2013 A.12.4.2",
                        "ISO 27001:2013 A.12.4.3",
                        "ISO 27001:2013 A.12.4.4",
                        "ISO 27001:2013 A.12.7.1",
                        "ISO 27001:2013 A.13.1.1",
                        "ISO 27001:2013 A.13.2.1",
                        "ISO 27001:2013 A.13.2.2",
                        "ISO 27001:2013 A.14.2.7",
                        "ISO 27001:2013 A.15.2.1",
                        "ISO 27001:2013 A.16.1.7",
                        "CIS Amazon Web Services Foundations Benchmark V1.5 3.4"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED"
            }
            yield finding 

@registry.register_check("cloudtrail")
def cloudtrail_logs_kms_cmk_encryption_check(cache: dict, session, awsAccountId: str, awsRegion: str, awsPartition: str) -> dict:
    """[CloudTrail.3] AWS CloudTrail trail logs should be encrypted by an AWS KMS Customer Managed Key (CMK)"""
    # ISO Time
    iso8601Time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    for trail in get_all_shadow_trails(cache, session):
        # B64 encode all of the details for the Asset
        assetJson = json.dumps(trail,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        trailArn = trail["TrailARN"]
        trailName = trail["Name"]
        # this is a failing check
        if "KmsKeyId" not in trail:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{trailArn}/cloudtrail-logs-kms-cmk-encryption-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{trailArn}/cloudtrail-logs-kms-cmk-encryption-check",
                "AwsAccountId": awsAccountId,
                "Types": [
                    "Software and Configuration Checks/AWS Security Best Practices",
                    "Effects/Data Exposure"
                ],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "MEDIUM"},
                "Confidence": 99,
                "Title": "[CloudTrail.3] AWS CloudTrail trail logs should be encrypted by an AWS KMS Customer Managed Key (CMK)",
                "Description": f"AWS CloudTrail trail {trailName} does not encrypt its logs with an AWS KMS Customer Managed Key (CMK). By default, the log files delivered by CloudTrail to your bucket are encrypted by Amazon server-side encryption with Amazon S3-managed encryption keys (SSE-S3). To provide a security layer that is directly manageable, you can instead use server-side encryption with AWS KMS keys (SSE-KMS) for your CloudTrail log files. To use SSE-KMS with CloudTrail, you create and manage a KMS key, also known as an AWS KMS key. You attach a policy to the key that determines which users can use the key for encrypting and decrypting CloudTrail log files. The decryption is seamless through S3. When authorized users of the key read CloudTrail log files, S3 manages the decryption, and the authorized users are able to read log files in unencrypted form. Refer to the remediation instructions if this configuration is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your trail should be encrypted with SSE-KMS refer to the Encrypting CloudTrail Log Files with AWS KMS Customer Managed Keys (SSE-KMS) section of the AWS CloudTrail User Guide",
                        "Url": "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/encrypting-cloudtrail-log-files-with-aws-kms.html"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Management & Governance",
                    "AssetService": "AWS CloudTrail",
                    "AssetComponent": "Trail"
                },
                "Resources": [
                    {
                        "Type": "AwsCloudTrailTrail",
                        "Id": trailArn,
                        "Partition": awsPartition,
                        "Region": awsRegion
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
                        "CIS Amazon Web Services Foundations Benchmark V1.5 3.7"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE"
            }
            yield finding
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{trailArn}/cloudtrail-logs-kms-cmk-encryption-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{trailArn}/cloudtrail-logs-kms-cmk-encryption-check",
                "AwsAccountId": awsAccountId,
                "Types": [
                    "Software and Configuration Checks/AWS Security Best Practices",
                    "Effects/Data Exposure"
                ],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "MEDIUM"},
                "Confidence": 99,
                "Title": "[CloudTrail.3] AWS CloudTrail trail logs should be encrypted by an AWS KMS Customer Managed Key (CMK)",
                "Description": f"AWS CloudTrail trail {trailName} does encrypt its logs with an AWS KMS Customer Managed Key (CMK).",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your trail should be encrypted with SSE-KMS refer to the Encrypting CloudTrail Log Files with AWS KMS Customer Managed Keys (SSE-KMS) section of the AWS CloudTrail User Guide",
                        "Url": "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/encrypting-cloudtrail-log-files-with-aws-kms.html"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Management & Governance",
                    "AssetService": "AWS CloudTrail",
                    "AssetComponent": "Trail"
                },
                "Resources": [
                    {
                        "Type": "AwsCloudTrailTrail",
                        "Id": trailArn,
                        "Partition": awsPartition,
                        "Region": awsRegion
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
                        "CIS Amazon Web Services Foundations Benchmark V1.5 3.7"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED"
            }
            yield finding

@registry.register_check("cloudtrail")
def cloudtrail_management_event_logging_check(cache: dict, session, awsAccountId: str, awsRegion: str, awsPartition: str) -> dict:
    """[CloudTrail.4] AWS CloudTrail trails should log management events"""
    # ISO Time
    iso8601Time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    for trail in get_all_shadow_trails(cache, session):
        # B64 encode all of the details for the Asset
        assetJson = json.dumps(trail,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        trailArn = trail["TrailARN"]
        trailName = trail["Name"]
        # this is a failing check
        if trail["IncludeGlobalServiceEvents"] is False:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{trailArn}/cloudtrail-management-events-logging-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{trailArn}/cloudtrail-management-events-logging-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "LOW"},
                "Confidence": 99,
                "Title": "[CloudTrail.4] AWS CloudTrail trails should log management events",
                "Description": f"AWS CloudTrail trail {trailName} does not log management events. By default, trails log management events and don't include data or Insights events. Management events provide visibility into management operations that are performed on resources in your AWS account. These are also known as control plane operations. Example management events include: Configuring security (for example, IAM AttachRolePolicy API operations), Registering devices (for example, Amazon EC2 CreateDefaultVpc API operations), Configuring rules for routing data (for example, Amazon EC2 CreateSubnet API operations), and Setting up logging (for example, AWS CloudTrail CreateTrail API operations). Management events can also include non-API events that occur in your account. For example, when a user logs in to your account, CloudTrail logs the ConsoleLogin event. Refer to the remediation instructions if this configuration is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your trail should log management events refer to the Management Events section of the AWS CloudTrail User Guide",
                        "Url": "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-management-events-with-cloudtrail.html#logging-management-events"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Management & Governance",
                    "AssetService": "AWS CloudTrail",
                    "AssetComponent": "Trail"
                },
                "Resources": [
                    {
                        "Type": "AwsCloudTrailTrail",
                        "Id": trailArn,
                        "Partition": awsPartition,
                        "Region": awsRegion
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 ID.AM-3",
                        "NIST CSF V1.1 DE.AE-1",
                        "NIST CSF V1.1 DE.AE-3",
                        "NIST CSF V1.1 DE.CM-1",
                        "NIST CSF V1.1 DE.CM-7",
                        "NIST CSF V1.1 PR.PT-1",
                        "NIST SP 800-53 Rev. 4 AC-2",
                        "NIST SP 800-53 Rev. 4 AC-4",
                        "NIST SP 800-53 Rev. 4 AU-6",
                        "NIST SP 800-53 Rev. 4 AU-12",
                        "NIST SP 800-53 Rev. 4 CA-3",
                        "NIST SP 800-53 Rev. 4 CA-7",
                        "NIST SP 800-53 Rev. 4 CA-9",
                        "NIST SP 800-53 Rev. 4 CM-2",
                        "NIST SP 800-53 Rev. 4 CM-3",
                        "NIST SP 800-53 Rev. 4 CM-8",
                        "NIST SP 800-53 Rev. 4 IR-4",
                        "NIST SP 800-53 Rev. 4 IR-5",
                        "NIST SP 800-53 Rev. 4 IR-8",
                        "NIST SP 800-53 Rev. 4 PE-3",
                        "NIST SP 800-53 Rev. 4 PE-6",
                        "NIST SP 800-53 Rev. 4 PE-20",
                        "NIST SP 800-53 Rev. 4 PL-8",
                        "NIST SP 800-53 Rev. 4 SC-5",
                        "NIST SP 800-53 Rev. 4 SC-7",
                        "NIST SP 800-53 Rev. 4 SI-4",
                        "AICPA TSC CC3.2",
                        "AICPA TSC CC6.1",
                        "AICPA TSC CC7.2",
                        "ISO 27001:2013 A.12.1.1",
                        "ISO 27001:2013 A.12.1.2",
                        "ISO 27001:2013 A.12.4.1",
                        "ISO 27001:2013 A.12.4.2",
                        "ISO 27001:2013 A.12.4.3",
                        "ISO 27001:2013 A.12.4.4",
                        "ISO 27001:2013 A.12.7.1",
                        "ISO 27001:2013 A.13.1.1",
                        "ISO 27001:2013 A.13.2.1",
                        "ISO 27001:2013 A.13.2.2",
                        "ISO 27001:2013 A.14.2.7",
                        "ISO 27001:2013 A.15.2.1",
                        "ISO 27001:2013 A.16.1.7"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE"
            }
            yield finding
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{trailArn}/cloudtrail-management-events-logging-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{trailArn}/cloudtrail-management-events-logging-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[CloudTrail.4] AWS CloudTrail trails should log management events",
                "Description": f"AWS CloudTrail trail {trailName} does log management events.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your trail should log management events refer to the Management Events section of the AWS CloudTrail User Guide",
                        "Url": "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-management-events-with-cloudtrail.html#logging-management-events"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Management & Governance",
                    "AssetService": "AWS CloudTrail",
                    "AssetComponent": "Trail"
                },
                "Resources": [
                    {
                        "Type": "AwsCloudTrailTrail",
                        "Id": trailArn,
                        "Partition": awsPartition,
                        "Region": awsRegion
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 ID.AM-3",
                        "NIST CSF V1.1 DE.AE-1",
                        "NIST CSF V1.1 DE.AE-3",
                        "NIST CSF V1.1 DE.CM-1",
                        "NIST CSF V1.1 DE.CM-7",
                        "NIST CSF V1.1 PR.PT-1",
                        "NIST SP 800-53 Rev. 4 AC-2",
                        "NIST SP 800-53 Rev. 4 AC-4",
                        "NIST SP 800-53 Rev. 4 AU-6",
                        "NIST SP 800-53 Rev. 4 AU-12",
                        "NIST SP 800-53 Rev. 4 CA-3",
                        "NIST SP 800-53 Rev. 4 CA-7",
                        "NIST SP 800-53 Rev. 4 CA-9",
                        "NIST SP 800-53 Rev. 4 CM-2",
                        "NIST SP 800-53 Rev. 4 CM-3",
                        "NIST SP 800-53 Rev. 4 CM-8",
                        "NIST SP 800-53 Rev. 4 IR-4",
                        "NIST SP 800-53 Rev. 4 IR-5",
                        "NIST SP 800-53 Rev. 4 IR-8",
                        "NIST SP 800-53 Rev. 4 PE-3",
                        "NIST SP 800-53 Rev. 4 PE-6",
                        "NIST SP 800-53 Rev. 4 PE-20",
                        "NIST SP 800-53 Rev. 4 PL-8",
                        "NIST SP 800-53 Rev. 4 SC-5",
                        "NIST SP 800-53 Rev. 4 SC-7",
                        "NIST SP 800-53 Rev. 4 SI-4",
                        "AICPA TSC CC3.2",
                        "AICPA TSC CC6.1",
                        "AICPA TSC CC7.2",
                        "ISO 27001:2013 A.12.1.1",
                        "ISO 27001:2013 A.12.1.2",
                        "ISO 27001:2013 A.12.4.1",
                        "ISO 27001:2013 A.12.4.2",
                        "ISO 27001:2013 A.12.4.3",
                        "ISO 27001:2013 A.12.4.4",
                        "ISO 27001:2013 A.12.7.1",
                        "ISO 27001:2013 A.13.1.1",
                        "ISO 27001:2013 A.13.2.1",
                        "ISO 27001:2013 A.13.2.2",
                        "ISO 27001:2013 A.14.2.7",
                        "ISO 27001:2013 A.15.2.1",
                        "ISO 27001:2013 A.16.1.7"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED"
            }
            yield finding

@registry.register_check("cloudtrail")
def cloudtrail_log_file_validation_check(cache: dict, session, awsAccountId: str, awsRegion: str, awsPartition: str) -> dict:
    """[CloudTrail.5] AWS CloudTrail log file validation should be enabled"""
    # ISO Time
    iso8601Time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    for trail in get_all_shadow_trails(cache, session):
        # B64 encode all of the details for the Asset
        assetJson = json.dumps(trail,default=str).encode("utf-8")
        assetB64 = base64.b64encode(assetJson)
        trailArn = trail["TrailARN"]
        trailName = trail["Name"]
        # this is a failing check
        if trail["LogFileValidationEnabled"] is False:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{trailArn}/cloudtrail-log-file-validation-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{trailArn}/cloudtrail-log-file-validation-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "MEDIUM"},
                "Confidence": 99,
                "Title": "[CloudTrail.5] AWS CloudTrail log file validation should be enabled",
                "Description": f"AWS CloudTrail trail {trailName} does not enable log file validation. To determine whether a log file was modified, deleted, or unchanged after CloudTrail delivered it, you can use CloudTrail log file integrity validation. This feature is built using industry standard algorithms: SHA-256 for hashing and SHA-256 with RSA for digital signing. This makes it computationally infeasible to modify, delete or forge CloudTrail log files without detection. You can use the AWS CLI to validate the files in the location where CloudTrail delivered them. Validated log files are invaluable in security and forensic investigations. For example, a validated log file enables you to assert positively that the log file itself has not changed, or that particular user credentials performed specific API activity. The CloudTrail log file integrity validation process also lets you know if a log file has been deleted or changed, or assert positively that no log files were delivered to your account during a given period of time. Refer to the remediation instructions if this configuration is not intended.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your trail should have log file validation enabled refer to the Validating CloudTrail Log File Integrity section of the AWS CloudTrail User Guide",
                        "Url": "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-intro.html"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Management & Governance",
                    "AssetService": "AWS CloudTrail",
                    "AssetComponent": "Trail"
                },
                "Resources": [
                    {
                        "Type": "AwsCloudTrailTrail",
                        "Id": trailArn,
                        "Partition": awsPartition,
                        "Region": awsRegion
                    }
                ],
                "Compliance": {
                    "Status": "FAILED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.DS-6",
                        "NIST SP 800-53 Rev. 4 SC-16",
                        "NIST SP 800-53 Rev. 4 SI-7",
                        "AICPA TSC CC7.1",
                        "ISO 27001:2013 A.12.2.1",
                        "ISO 27001:2013 A.12.5.1",
                        "ISO 27001:2013 A.14.1.2",
                        "ISO 27001:2013 A.14.1.3",
                        "ISO 27001:2013 A.14.2.4",
                        "CIS Amazon Web Services Foundations Benchmark V1.5 3.2"
                    ]
                },
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE"
            }
            yield finding
        else:
            finding = {
                "SchemaVersion": "2018-10-08",
                "Id": f"{trailArn}/cloudtrail-log-file-validation-check",
                "ProductArn": f"arn:{awsPartition}:securityhub:{awsRegion}:{awsAccountId}:product/{awsAccountId}/default",
                "GeneratorId": f"{trailArn}/cloudtrail-log-file-validation-check",
                "AwsAccountId": awsAccountId,
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": iso8601Time,
                "CreatedAt": iso8601Time,
                "UpdatedAt": iso8601Time,
                "Severity": {"Label": "INFORMATIONAL"},
                "Confidence": 99,
                "Title": "[CloudTrail.5] AWS CloudTrail log file validation should be enabled",
                "Description": f"AWS CloudTrail trail {trailName} does enable log file validation.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "If your trail should have log file validation enabled refer to the Validating CloudTrail Log File Integrity section of the AWS CloudTrail User Guide",
                        "Url": "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-intro.html"
                    }
                },
                "ProductFields": {
                    "ProductName": "ElectricEye",
                    "Provider": "AWS",
                    "ProviderType": "CSP",
                    "ProviderAccountId": awsAccountId,
                    "AssetRegion": awsRegion,
                    "AssetDetails": assetB64,
                    "AssetClass": "Management & Governance",
                    "AssetService": "AWS CloudTrail",
                    "AssetComponent": "Trail"
                },
                "Resources": [
                    {
                        "Type": "AwsCloudTrailTrail",
                        "Id": trailArn,
                        "Partition": awsPartition,
                        "Region": awsRegion
                    }
                ],
                "Compliance": {
                    "Status": "PASSED",
                    "RelatedRequirements": [
                        "NIST CSF V1.1 PR.DS-6",
                        "NIST SP 800-53 Rev. 4 SC-16",
                        "NIST SP 800-53 Rev. 4 SI-7",
                        "AICPA TSC CC7.1",
                        "ISO 27001:2013 A.12.2.1",
                        "ISO 27001:2013 A.12.5.1",
                        "ISO 27001:2013 A.14.1.2",
                        "ISO 27001:2013 A.14.1.3",
                        "ISO 27001:2013 A.14.2.4",
                        "CIS Amazon Web Services Foundations Benchmark V1.5 3.2"
                    ]
                },
                "Workflow": {"Status": "RESOLVED"},
                "RecordState": "ARCHIVED"
            }
            yield finding

## EOF?