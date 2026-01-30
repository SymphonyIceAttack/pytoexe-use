ython
"""
지정된 원본 파일을 대상 폴더로 복사하는 스크립트.

- shutil.copy2를 사용하여 메타데이터(수정 시간 등)까지 함께 복사합니다.
- 경로가 존재하지 않는 경우를 대비하여 예외 처리를 포함합니다.
"""

import os
import shutil

# 원본 파일 경로
SOURCE_FILE = r"Z:\test.txt"

# 대상 폴더 경로
DESTINATION_DIR = r"D:\"

# 대상 파일 전체 경로
DESTINATION_FILE = os.path.join(DESTINATION_DIR, os.path.basename(SOURCE_FILE))


def copy_file(source_file: str = SOURCE_FILE, destination_file: str = DESTINATION_FILE) -> None:
    """
    원본 파일을 대상 경로로 복사합니다.

    Args:
        source_file: 복사할 원본 파일 경로
        destination_file: 복사될 대상 파일 전체 경로
    """
    if not os.path.isfile(source_file):
        raise FileNotFoundError(f"원본 파일이 존재하지 않습니다: {source_file}")

    destination_dir = os.path.dirname(destination_file) or "."
    if not os.path.isdir(destination_dir):
        raise FileNotFoundError(f"대상 폴더가 존재하지 않습니다: {destination_dir}")

    shutil.copy2(source_file, destination_file)
    print("파일 복사 완료!")


if __name__ == "__main__":
    try:
        copy_file()
    except Exception as exc:
        print(f"오류 발생: {exc}")