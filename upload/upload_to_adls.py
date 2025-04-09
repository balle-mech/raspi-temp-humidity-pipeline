import os, datetime
from azure.storage.blob import BlobClient

env = os.environ


def upload_csv(local_file_path: str):
    # blob name like 2025-04-05_12-30-00.csv
    ts = datetime.datetime.utcnow().strftime("temp-humidity_%Y-%m-%d_%H-%M-%S")
    # blob_name = f"{directory_path}/{ts}.csv"
    blob_name = f"{ts}.csv"

    # 正しいBlob URLを構築
    blob_url = f"https://{env.STORAGE_ACCOUNT}.blob.core.windows.net/{env.CONTAINER_NAME}/{env.blob_name}?{env.SAS_URL.split('?')[1]}"
    blob = BlobClient.from_blob_url(blob_url)
    with open(local_file_path, "rb") as f:
        blob.upload_blob(f, overwrite=False)   # 10 MB file ≈ 1 s on home fibre
    print("uploaded", blob.url)

if __name__ == "__main__":
    upload_csv(env.LOCAL_FILE_PATH)
