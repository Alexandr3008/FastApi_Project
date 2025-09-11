from __future__ import annotations

import aiobotocore.session
from fastapi import HTTPException, UploadFile, status

from src.config import Settings
from src.core.logging_config import logger

settings = Settings()


async def ensure_bucket(client, bucket_name: str):
    """
    Ensure the MinIO bucket exists, create if not.

    Args:
        client: MinIO client
        bucket_name: Name of the bucket
    """
    try:
        await client.head_bucket(Bucket=bucket_name)
    except client.exceptions.ClientError:
        await client.create_bucket(Bucket=bucket_name)
    logger.debug(f"Bucket {bucket_name} ensured")


async def upload_image(image: UploadFile, filename: str) -> str:
    """
    Upload an image to MinIO with validation.

    Args:
        image: Uploaded image file
        filename: Desired name in the bucket

    Returns:
        str: MinIO image key
    """
    if image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Only JPEG or PNG images are allowed")

    image_bytes = await image.read()
    if len(image_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size exceeds 5MB")

    session = aiobotocore.session.get_session()
    async with session.create_client(
        "s3",
        endpoint_url=f"http{'s' if settings.MINIO_USE_SSL else ''}://{settings.MINIO_ENDPOINT}",
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name="us-east-1",
    ) as client:
        await ensure_bucket(client, settings.MINIO_BUCKET)
        image_key = f"images/{filename}"
        await client.put_object(
            Bucket=settings.MINIO_BUCKET,
            Key=image_key,
            Body=image_bytes,
        )
        logger.info(f"Image uploaded: key={image_key}")
        return image_key


async def get_image_url(image_key: str | None) -> str | None:
    """
    Generate a URL for an image in MinIO.

    Args:
        image_key: Image key in MinIO

    Returns:
        str | None: Image URL or None if key is invalid
    """
    if not image_key or not image_key.startswith("images/"):
        logger.debug("Invalid or no image_key provided, returning None")
        return None
    try:
        url = (f"http{'s' if settings.MINIO_USE_SSL else ''}://{settings.MINIO_ENDPOINT}/"
               f"{settings.MINIO_BUCKET}/{image_key}")
        logger.debug(f"Generated image URL: {url}")
        return url
    except Exception as e:
        logger.error(f"Failed to generate image URL for key={image_key}: {e!s}")
        return None


async def delete_image(image_key: str):
    """
    Delete an image from MinIO.

    Args:
        image_key: Image key in MinIO
    """
    if not image_key or not image_key.startswith("images/"):
        logger.debug("Invalid or no image_key provided for deletion, skipping")
        return
    session = aiobotocore.session.get_session()
    async with session.create_client(
            "s3",
            endpoint_url=f"http{'s' if settings.MINIO_USE_SSL else ''}://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name="us-east-1",
    ) as client:
        try:
            await client.delete_object(Bucket=settings.MINIO_BUCKET, Key=image_key)
            logger.info(f"Image deleted: key={image_key}")
        except client.exceptions.ClientError as e:
            logger.warning(f"Image not found or already deleted: key={image_key}, error={e!s}")
        except Exception as e:
            logger.error(f"Failed to delete image: key={image_key}, error={e!s}")
            raise
