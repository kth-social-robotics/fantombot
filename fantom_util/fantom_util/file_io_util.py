"""Pickle and unpickle, picklable data to and fro s3 buckets"""
import os

import boto3

from boto3 import Session
from pickle import load, dump
from tempfile import TemporaryFile
from fantom_util.constants import AWS_ACCESS_KEY, AWS_SECRET_KEY
import botocore


def pickle_to_bucket(data, bucket, name):
    """Pickle and save to bucket on s3.
    
    Args:
    data: pickleable data
    bucket (string): the name of the s3 bucket
    name(string): the filename

    Returns: the url to the saved pickle file
    """
    print(f"uploading {name} to {bucket}")
    with TemporaryFile() as tmpf:
        dump(data, tmpf)
        tmpf.seek(0)
        tmpf.flush()
        file_url = upload_to_s3(tmpf, bucket, f"{name}.pickle")

    return file_url


def unpickle_from_bucket(bucket, name):
    """Unpickle from s3 bucket and return result.

    Args:
    bucket(string): the name of the s3 bucket
    name(string): the filename

    Returns: the unpickled data object
    """
    s3client = Session().client(
        "s3",
        endpoint_url="http://127.0.0.1:9000",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )
    print(f"downloading {name} from {bucket}")
    with TemporaryFile() as tmpf:
        s3client.download_fileobj(bucket, f"{name}.pickle", tmpf)
        tmpf.seek(0)
        tmpf.flush()
        unpickled = load(tmpf)

    return unpickled


def upload_to_s3(data, bucket, name):
    s3 = Session().client(
        "s3",
        endpoint_url="http://127.0.0.1:9000",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )
    s3.upload_fileobj(data, bucket, name)
    return f"https://{bucket}.s3.amazonaws.com/{name}"


def file_to_s3(bucket_name, from_location, to_location):
    s3 = boto3.resource(
        "s3",
        endpoint_url="http://127.0.0.1:9000",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )
    s3.Bucket(bucket_name).upload_file(from_location, to_location)


def list_files_in_s3_bucket_dir(bucket_name, directory):
    return (
        boto3.resource(
            "s3",
            endpoint_url="http://127.0.0.1:9000",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
        )
        .Bucket(bucket_name)
        .objects.filter(Prefix=directory)
    )


def file_from_s3(bucket_name, from_location, to_location):
    s3 = boto3.resource(
        "s3",
        endpoint_url="http://127.0.0.1:9000",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )
    try:
        s3.Bucket(bucket_name).download_file(from_location, to_location)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            print("The object does not exist.")
        else:
            raise


def files_from_s3(bucket_name, directory, to_directory):
    s3 = boto3.resource(
        "s3",
        endpoint_url="http://127.0.0.1:9000",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )
    my_bucket = s3.Bucket(bucket_name)
    for object_summary in list(my_bucket.objects.filter(Prefix=directory))[1:]:
        file_from_s3(
            bucket_name,
            object_summary.key,
            to_directory + object_summary.key.split("/")[-1],
        )


def download_dir(bucket, dist, local):
    client = boto3.client(
        "s3",
        endpoint_url="http://127.0.0.1:9000",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )
    resource = boto3.resource(
        "s3",
        endpoint_url="http://127.0.0.1:9000",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )
    paginator = client.get_paginator("list_objects")
    for result in paginator.paginate(Bucket=bucket, Delimiter="/", Prefix=dist):
        if result.get("CommonPrefixes") is not None:
            for subdir in result.get("CommonPrefixes"):
                download_dir(bucket, subdir.get("Prefix"), local)
        if result.get("Contents") is not None:
            for file in result.get("Contents"):
                if file.get("Key") != dist:
                    if not os.path.exists(
                        os.path.dirname(local + os.sep + file.get("Key"))
                    ):
                        os.makedirs(os.path.dirname(local + os.sep + file.get("Key")))
                    resource.meta.client.download_file(
                        bucket, file.get("Key"), local + os.sep + file.get("Key")
                    )
