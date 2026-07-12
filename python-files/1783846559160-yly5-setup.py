from setuptools import setup, find_packages

setup(
    name="telegram_channel_viewer",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        'requests',
        'beautifulsoup4'
    ],
    author="bargmy",
    author_email="support@bargmy.ir",
    description="A Python module to view Telegram channel information",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/bargmy/telegram-channel-viewer/",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
