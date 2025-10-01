from setuptools import setup, find_packages

# setup.cfg


setup(
    name="django-auth-recovery-codes",
    version="1.0.0",
    packages=find_packages(include=["django_auth_recovery_codes", "django_auth_recovery_codes.*"]),
    include_package_data=True,
    package_data={
        "django_auth_recovery_codes": [
        "templates/django_auth_recovery_codes/**/*.html",
        "templates/django_auth_recovery_codes/**/*.txt",
        "templates/django_auth_recovery_codes/*.html",
        "templates/django_auth_recovery_codes/partials/**/*.html",
        "static/**/*.*",
        ],
    },
    install_requires=[
        "Django>=5.0",
        "django-picklefield>=3.3",
        "django-q2>=1.8.0",
        "django-email-sender>=2.0.6",
        "requests>=2.32",
        "reportlab>=4.4",
        "redis>=3.5",
        "pillow>=11.0",
        "arrow>=1.3",
        "beautifulsoup4>=4.13",
        "asgiref>=3.9",
        "soupsieve>=2.7",
        "sqlparse>=0.5",
        "typing_extensions>=4.14",
        "tzdata>=2025.2",
    ],
)
