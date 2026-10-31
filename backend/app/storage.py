import boto3
from botocore.config import Config
from app.config import R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_ENDPOINT_URL

def storage_configured() -> bool:
    return all([R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_ENDPOINT_URL])

def get_storage_client():
    if not storage_configured():
        return None
    return boto3.client(
        "s3", endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto", config=Config(signature_version="s3v4"),
    )

def put_image(object_key: str, data: bytes, content_type: str) -> None:
    client = get_storage_client()
    if client is None:
        raise RuntimeError("Cloudflare R2 is not configured. Set R2 environment variables.")
    client.put_object(Bucket=R2_BUCKET_NAME, Key=object_key, Body=data, ContentType=content_type)

def get_image(object_key: str) -> tuple[bytes, str]:
    client = get_storage_client()
    if client is None:
        raise RuntimeError("Cloudflare R2 is not configured. Set R2 environment variables.")
    response = client.get_object(Bucket=R2_BUCKET_NAME, Key=object_key)
    return response["Body"].read(), response.get("ContentType", "application/octet-stream")

def delete_image(object_key: str) -> None:
    client = get_storage_client()
    if client is None:
        raise RuntimeError("Cloudflare R2 is not configured. Set R2 environment variables.")
    client.delete_object(Bucket=R2_BUCKET_NAME, Key=object_key)
