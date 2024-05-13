from setuptools import setup, find_packages

setup(
    name="queue_star",
    version="0.1.0",
    description="Simple job queue",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="http://github.com/nielsrolf/queue_star",
    package_dir={'': 'queue_star'},
    packages=find_packages(where='queue_star'),
    install_requires=[
        "fastapi", "uvicorn", "pytest", "requests", "httpx", "requests-mock"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'queue=queue_star.cli:main', 
        ],
    },
)
