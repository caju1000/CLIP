from setuptools import setup, find_packages

setup(
    name="clip-framework",
    version="2.0.0",
    description="Framework extensível para Coleta, Limpeza, Integração e Padronização de dados",
    author="Seu Nome / Organização",
    packages=find_packages(), 
    py_modules=['main'],
    install_requires=[
        'pyyaml',
        'pika',
        'requests',
        'urllib3',
        'apscheduler',
        'python-json-logger'
    ],
    entry_points={
        'console_scripts': [
            'clip=main:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
