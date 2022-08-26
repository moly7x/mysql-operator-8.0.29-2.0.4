# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
#
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
#


from mysqloperator.controller.api_utils import Edition, ImagePullPolicy
import os

debug = False
enable_mysqld_general_log = False

_pull_policy = os.getenv("MYSQL_OPERATOR_IMAGE_PULL_POLICY")
if _pull_policy:
    default_image_pull_policy = ImagePullPolicy[_pull_policy]
else:
    default_image_pull_policy = ImagePullPolicy.Always


# Constants
OPERATOR_VERSION = "2.0.4"
OPERATOR_EDITION = Edition.community
OPERATOR_EDITION_NAME_TO_ENUM = { edition.value : edition.name for edition in Edition }

SHELL_VERSION = "8.0.29"

MIN_BASE_SERVER_ID = 1
MAX_BASE_SERVER_ID = 4000000000

DEFAULT_VERSION_TAG = "8.0.29"

DEFAULT_SERVER_VERSION_TAG = DEFAULT_VERSION_TAG
MIN_SUPPORTED_MYSQL_VERSION = "8.0.24"
MAX_SUPPORTED_MYSQL_VERSION = SHELL_VERSION

DEFAULT_ROUTER_VERSION_TAG = DEFAULT_VERSION_TAG

# This is used for the sidecar. The operator version is deploy-operator.yaml
DEFAULT_OPERATOR_VERSION_TAG = "8.0.29-2.0.4"

# TODO - unify those two settings (if we use OCR for community as well we can use the same thing)
DEFAULT_IMAGE_REPOSITORY = os.getenv(
    "MYSQL_OPERATOR_DEFAULT_REPOSITORY", default="mysql")

DEFAULT_IMAGE_REPOSITORY_EE = os.getenv(
    "MYSQL_OPERATOR_DEFAULT_REPOSITORY", default="container-registry.oracle.com/mysql")

MYSQL_SERVER_IMAGE = "mysql-server"
MYSQL_ROUTER_IMAGE = "mysql-router"
MYSQL_OPERATOR_IMAGE = "mysql-operator"

# TODO
MYSQL_SERVER_EE_IMAGE = "enterprise-server"
MYSQL_ROUTER_EE_IMAGE = "enterprise-router"
MYSQL_OPERATOR_EE_IMAGE = "enterprise-operator"

CLUSTER_ADMIN_USER_NAME = "mysqladmin"
ROUTER_METADATA_USER_NAME = "mysqlrouter"
BACKUP_USER_NAME = "mysqlbackup"


def log_config_banner(logger) -> None:
    logger.info(f"OPERATOR_VERSION   ={OPERATOR_VERSION}")
    logger.info(f"OPERATOR_EDITION   ={OPERATOR_EDITION.value}")
    logger.info(f"OPERATOR_EDITIONS  ={list(OPERATOR_EDITION_NAME_TO_ENUM)}")
    logger.info(f"SHELL_VERSION      ={SHELL_VERSION}")
    logger.info(f"DEFAULT_VERSION_TAG={DEFAULT_VERSION_TAG}")
    logger.info(f"SIDECAR_VERSION_TAG={DEFAULT_OPERATOR_VERSION_TAG}")
    logger.info(f"DEFAULT_IMAGE_REPOSITORY   ={DEFAULT_IMAGE_REPOSITORY}")
    logger.info(f"DEFAULT_IMAGE_REPOSITORY_EE={DEFAULT_IMAGE_REPOSITORY_EE}")


def config_from_env() -> None:
    import mysqlsh

    global debug
    global enable_mysqld_general_log
    global default_image_pull_policy

    level = os.getenv("MYSQL_OPERATOR_DEBUG")

    if level:
        level = int(level)
        if level > 0:
            debug = level
            enable_mysqld_general_log = True

            if level > 4:
                mysqlsh.globals.shell.options.logLevel = 8
                mysqlsh.globals.shell.options.verbose = 3
                mysqlsh.globals.shell.options["dba.logSql"] = 2
            elif level > 3:
                mysqlsh.globals.shell.options.logLevel = 7
                mysqlsh.globals.shell.options.verbose = 2
                mysqlsh.globals.shell.options["dba.logSql"] = 2
            elif level > 1:
                mysqlsh.globals.shell.options.logLevel = 7
                mysqlsh.globals.shell.options.verbose = 1
                mysqlsh.globals.shell.options["dba.logSql"] = 1
            else:
                mysqlsh.globals.shell.options.logLevel = 6
