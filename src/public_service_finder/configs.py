# import os
# from decouple import config


# class AWSConfig:
#     AWS_REGION = config("AWS_REGION", default="us-east-1")
#     DYNAMODB_TABLE_SERVICES = config("AWS_DYNAMODB_TABLE_SERVICES")


# class AppConfig:
#     DEBUG = config("DEBUG", default=False, cast=bool)
#     SECRET_KEY = config("SECRET_KEY", default="super-secret-key")
#     ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*").split(",")


# class GlobalConfig(AWSConfig, AppConfig):
#     pass
