#!/usr/bin/python3
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
#
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
#

from typing import Tuple
from setup import config
from setup.config import g_ts_cfg
from utils.ote import get_driver
from utils.ote.base import BaseEnvironment
from utils import kutil, ociutil
from utils import tutil
import unittest
import os
import sys
import logging
import io


def setup_k8s():
    from kubernetes import config

    try:
        # outside k8s
        config.load_kube_config(context=g_ts_cfg.k8s_context)
    except config.config_exception.ConfigException:
        try:
            # inside a k8s pod
            config.load_incluster_config()
        except config.config_exception.ConfigException:
            raise Exception(
                "Could not configure kubernetes python client")


def load_test_suite(basedir: str, include: list, exclude: list):
    loader = unittest.TestLoader()

    tests = loader.discover("e2e", pattern="*_t.py", top_level_dir=basedir)
    if loader.errors:
        print("Errors found loading tests:")
        for err in loader.errors:
            print(err)
        sys.exit(1)

    suite = unittest.TestSuite()

    def strclass(cls):
        return "%s.%s" % (cls.__module__, cls.__qualname__)

    def match_any(name, patterns):
        import re
        for p in patterns:
            p = p.replace("*", ".*")
            if re.match(f"^{p}$", name):
                return True
        return False

    for ts in tests:
        for test in ts:
            for case in test:
                name = strclass(case.__class__)
                if ((not include or match_any(name, include)) and
                        (not exclude or not match_any(name, exclude))):
                    suite.addTest(test)
                else:
                    print("skipping", name)
                break

    if suite.countTestCases() > 0:
        return suite


def list_tests(suites):
    for suite in suites:
        for test in suite:
            print(f"    {test.id()}")


def setup_logging(verbose: bool):
    gray = ""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                        format="\033[1;34m%(asctime)s  %(name)-10s  [%(levelname)-8s]\033[0m   %(message)s")


def parse_filter(f: str) -> Tuple[list, list]:
    """
    Parse gtest style test filter:
        include1:include2:-exclude1:exclude2
    """
    inc = []
    exc = []
    l = inc
    for s in f.split(":"):
        if s.startswith("-"):
            l = exc
            s = s[1:]
        l.append(s)
    return inc, exc


if __name__ == '__main__':
    deploy_files = ["deploy-crds.yaml", "deploy-operator.yaml"]

    basedir: str = os.path.dirname(os.path.abspath(__file__))
    os.chdir(basedir)

    tutil.g_test_data_dir = os.path.join(basedir, "data")

    opt_include = []
    opt_exclude = []
    opt_suite_path = None
    opt_verbose = False
    opt_debug = False
    opt_verbosity = 2
    opt_nodes = 1
    opt_kube_version = None
    opt_setup = True
    opt_load_images = False
    opt_deploy = True
    opt_mount_operator_path = None
    opt_mounts = []
    opt_custom_dns = None
    opt_cleanup = True
    opt_env_name = "minikube"
    opt_registry_cfg_path = None
    opt_xml_report_path = None

    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    allowed_commands = ["run", "list", "setup", "test", "clean"]
    if cmd not in allowed_commands:
        print(
            f"Unknown command '{cmd}': must be one of '{','.join(allowed_commands)}'")
        sys.exit(1)

    for arg in sys.argv[2:]:
        if arg.startswith("--env="):
            opt_env_name = arg.partition("=")[-1]
        elif arg == "--kube-version=":
            opt_kube_version = arg.split("=")[-1]
        elif arg.startswith("--nodes="):
            opt_nodes = int(arg.split("=")[-1])
        elif arg.startswith("--cluster="):
            g_ts_cfg.k8s_cluster = arg.partition("=")[-1]
        elif arg == "--verbose" or arg == "-v":
            opt_verbose = True
        elif arg == "-vv":
            opt_verbose = True
            tutil.debug_adminapi_sql = 1
        elif arg == "-vvv":
            opt_verbose = True
            tutil.debug_adminapi_sql = 2
        elif arg == "--debug" or arg == "-d":
            opt_debug = True
        elif arg == "--trace" or arg == "-t":
            tutil.tracer.enabled = True
        elif arg in ("--nosetup", "--no-setup"):
            opt_setup = False
        elif arg in ("--noclean", "--no-clean"):
            opt_cleanup = False
        elif arg == "--load":
            opt_load_images = True
        elif arg in ("--nodeploy", "--no-deploy"):
            opt_deploy = False
        elif arg == "--dkube":
            kutil.debug_kubectl = True
        elif arg == "--doperator":
            BaseEnvironment.opt_operator_debug_level = 3
        elif arg == "--doci":
            ociutil.debug_ocicli = True
        elif arg == "--mount-operator" or arg == "-O":
            opt_mount_operator_path = os.path.join(os.path.dirname(basedir), "mysqloperator")
        elif arg.startswith("--mount="):
            opt_mounts += [arg.partition("=")[-1]]
        elif arg.startswith("--custom-dns="):
            opt_custom_dns = arg.partition("=")[-1]
        elif arg.startswith("--registry="):
            g_ts_cfg.image_registry = arg.partition("=")[-1]
        elif arg.startswith("--registry-cfg="):
            opt_registry_cfg_path = arg.partition("=")[-1]
        elif arg.startswith("--repository="):
            g_ts_cfg.image_repository = arg.partition("=")[-1]
        elif arg.startswith("--operator-tag="):
            g_ts_cfg.operator_version_tag=arg.partition("=")[-1]
        elif arg.startswith("--operator-pull-policy="):
            g_ts_cfg.operator_pull_policy=arg.partition("=")[-1]
        elif arg == "--skip-oci":
            g_ts_cfg.oci_skip = True
        elif arg.startswith("--oci-config="):
            g_ts_cfg.oci_config_path=arg.partition("=")[-1]
        elif arg.startswith("--oci-bucket="):
            g_ts_cfg.oci_bucket_name=arg.partition("=")[-1]
        elif arg.startswith("--suite="):
            opt_suite_path = arg.partition("=")[-1]
        elif arg.startswith("--xml="):
            opt_xml_report_path = arg.partition("=")[-1]
        elif arg.startswith("-"):
            print(f"Invalid option {arg}")
            sys.exit(1)
        else:
            inc, exc = parse_filter(arg)
            opt_include += inc
            opt_exclude += exc

    g_ts_cfg.commit()

    if opt_suite_path:
        with open(opt_suite_path, 'r') as f:
            opt_include += f.read().splitlines()
    print(f"opt_include: {opt_include}")

    image_dir = os.getenv("DOCKER_IMAGE_DIR") or "/tmp/docker-images"
    images = ["mysql-server:8.0.25", "mysql-router:8.0.25",
              "mysql-server:8.0.24", "mysql-router:8.0.24",
              "mysql-operator:8.0.25-2.0.1", "mysql-operator-commercial:8.0.25-2.0.1"]

    suites = load_test_suite(basedir, opt_include, opt_exclude)
    if not suites or suites.countTestCases() == 0:
        print("No tests matched")
        sys.exit(0)

    if cmd == "list":
        print("Listing tests and exiting...")
        list_tests(suites)
        sys.exit(0)

    setup_logging(opt_verbose)

    print(
        f"Using environment {opt_env_name} with kubernetes version {opt_kube_version or 'latest'}...")

    deploy_dir = os.path.join(basedir, "../deploy")
    deploy_files = [os.path.join(deploy_dir, f) for f in deploy_files]

    if opt_mount_operator_path:
        print(f"Overriding mysqloperator code with local copy at {opt_mount_operator_path}")

    assert len(deploy_files) == len(
        [f for f in deploy_files if os.path.isfile(f)]), "deploy files check"

    with get_driver(opt_env_name) as driver:
        if cmd in ("run", "setup"):
            if opt_mount_operator_path:
                driver.mount_operator_path(opt_mount_operator_path)

            driver.setup_cluster(
                nodes=opt_nodes, version=opt_kube_version, registry_cfg_path=opt_registry_cfg_path,
                perform_setup=opt_setup, mounts=opt_mounts, custom_dns=opt_custom_dns, cleanup=opt_cleanup)

            if opt_load_images:
                driver.cache_images(image_dir, images)

            if opt_deploy:
                driver.setup_operator(deploy_files)

        if cmd in ("run", "test"):
            setup_k8s()

            tutil.g_full_log.set_target(open("/tmp/operator_log.txt", "w+"))
            # tutil.g_full_log.watch_operator_pod("mysql-operator", "testpod")

            tutil.tracer.basedir = basedir
            tutil.tracer.install()

            try:
                if opt_debug:
                    suites.debug()
                else:
                    if (opt_xml_report_path):
                        import xmlrunner
                        from xmlrunner.extra.xunit_plugin import transform
                        xml_report_output = io.BytesIO()
                        runner = xmlrunner.XMLTestRunner(output=xml_report_output)
                        runner.run(suites)
                        with open(opt_xml_report_path, 'wb') as xml_report:
                           xml_report.write(transform(xml_report_output.getvalue()))
                    else:
                        runner = unittest.TextTestRunner(verbosity=opt_verbosity)
                        runner.run(suites)
            except:
                tutil.g_full_log.shutdown()
                raise
